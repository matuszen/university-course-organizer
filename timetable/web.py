from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import OperationalError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import APIException

from .models import ClassSession, Lecturer, Room, Semester, StudentGroup, Subject
from .serializers import ClassSessionSerializer, TimeWindowSerializer
from .services import available_rooms, save_resource

DAYS = [
    (1, "Poniedziałek"),
    (2, "Wtorek"),
    (3, "Środa"),
    (4, "Czwartek"),
    (5, "Piątek"),
    (6, "Sobota"),
    (7, "Niedziela"),
]


def label(instance):
    if isinstance(instance, Lecturer):
        return f"{instance.first_name} {instance.last_name}"
    return instance.name


class ResourceChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return label(obj)


class FilterForm(forms.Form):
    semester = ResourceChoice(Semester.objects.all(), label="Semestr", required=False)
    weekday = forms.TypedChoiceField(
        choices=[("", "Wszystkie dni"), *DAYS], coerce=int, required=False, label="Dzień"
    )
    group = ResourceChoice(StudentGroup.objects.all(), label="Grupa", required=False)
    lecturer = ResourceChoice(Lecturer.objects.all(), label="Prowadzący", required=False)


class WindowForm(forms.Form):
    semester = ResourceChoice(Semester.objects.all(), label="Semestr")
    weekday = forms.TypedChoiceField(choices=DAYS, coerce=int, label="Dzień")
    start_time = forms.TimeField(label="Od", widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(label="Do", widget=forms.TimeInput(attrs={"type": "time"}))


class SessionForm(forms.ModelForm):
    class Meta:
        model = ClassSession
        fields = [
            "semester",
            "subject",
            "lecturer",
            "room",
            "group",
            "weekday",
            "start_time",
            "end_time",
        ]
        widgets = {
            "weekday": forms.Select(choices=DAYS),
            "start_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "end_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
        }
        field_classes = {
            name: ResourceChoice for name in ("semester", "subject", "lecturer", "room", "group")
        }


def style(form):
    for field in form.fields.values():
        field.widget.attrs["class"] = (
            "form-select" if isinstance(field.widget, forms.Select) else "form-control"
        )
    return form


def errors(form, detail):
    if isinstance(detail, dict):
        for name, messages in detail.items():
            if name == "conflicts":
                resources = {"room": "Sala", "group": "Grupa", "lecturer": "Prowadzący"}
                for conflict in messages:
                    form.add_error(
                        None,
                        f"{resources[conflict['resource']]} — kolizja "
                        f"z zajęciami nr {conflict['class_id']}.",
                    )
            else:
                for message in messages if isinstance(messages, list) else [messages]:
                    form.add_error(name if name in form.fields else None, str(message))
    else:
        form.add_error(None, str(detail))


def plan(request):
    params = request.GET.copy()
    if "semester" not in params:
        today = timezone.localdate()
        semester = Semester.objects.filter(start_date__lte=today, end_date__gte=today).last()
        semester = semester or Semester.objects.last()
        if semester:
            params["semester"] = str(semester.pk)
    form = FilterForm(params)
    sessions = ClassSession.objects.none()
    if form.is_valid():
        filters = {key: value for key, value in form.cleaned_data.items() if value}
        sessions = (
            ClassSession.objects.filter(**filters)
            .select_related("subject", "room", "group", "lecturer", "semester")
            .order_by("weekday", "start_time", "id")
        )
    return render(
        request,
        "timetable/plan.html",
        {
            "form": style(form),
            "sessions": sessions,
            "days": DAYS,
            "has_semesters": Semester.objects.exists(),
            "query": params.urlencode(),
            "semester_id": params.get("semester", ""),
            "saved": request.GET.get("saved") == "1",
        },
    )


def rooms(request):
    form = WindowForm(request.GET or None)
    result = None
    if form.is_bound and form.is_valid():
        serializer = TimeWindowSerializer(data=request.GET)
        if serializer.is_valid():
            result = available_rooms(**serializer.validated_data)
        else:
            errors(form, serializer.errors)
    return render(request, "timetable/rooms.html", {"form": style(form), "rooms": result})


def staff_access(user):
    if user.is_authenticated and not user.is_staff:
        raise PermissionDenied("Zmiany wymagają konta administratora.")
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_access)
def edit(request, pk=None):
    instance = get_object_or_404(ClassSession, pk=pk) if pk else None
    form = SessionForm(
        request.POST if request.method == "POST" else None,
        instance=instance,
        initial={"semester": request.GET.get("semester")},
    )
    if request.method == "POST" and form.is_valid():
        serializer = ClassSessionSerializer(instance=instance, data=request.POST)
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                saved = save_resource(serializer)
            return HttpResponseRedirect(f"{reverse('plan')}?semester={saved.semester_id}&saved=1")
        except APIException as exc:
            errors(form, exc.detail)
        except OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            form.add_error(None, "Baza jest zajęta. Spróbuj ponownie za chwilę.")
    missing = [
        title
        for model, title in [
            (Semester, "semestr"),
            (Subject, "przedmiot"),
            (Lecturer, "prowadzący"),
            (Room, "sala"),
            (StudentGroup, "grupa"),
        ]
        if not model.objects.exists()
    ]
    return render(
        request,
        "timetable/edit.html",
        {
            "form": style(form),
            "editing": pk is not None,
            "missing": missing,
        },
    )


@user_passes_test(staff_access)
def delete(request, pk):
    session = get_object_or_404(ClassSession.objects.select_related("subject"), pk=pk)
    if request.method == "POST":
        semester_id = session.semester_id
        session.delete()
        return HttpResponseRedirect(f"{reverse('plan')}?semester={semester_id}&saved=1")
    return render(request, "timetable/delete.html", {"session": session})
