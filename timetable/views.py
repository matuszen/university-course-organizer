from django.db import OperationalError, transaction
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action

from .models import ClassSession, Lecturer, Room, Semester, StudentGroup, Subject
from .serializers import (
    ClassFilterSerializer,
    ClassSessionSerializer,
    GroupSerializer,
    LecturerSerializer,
    RoomSerializer,
    SemesterSerializer,
    SubjectSerializer,
    TimeWindowSerializer,
)
from .services import ScheduleConflict, overlapping_sessions, validate_schedule


class ResourceViewSet(viewsets.ModelViewSet):
    def dispatch(self, request, *args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            try:
                with transaction.atomic():
                    response = super().dispatch(request, *args, **kwargs)
                    if response.status_code >= 400:
                        transaction.set_rollback(True)
                    return response
            except OperationalError as exc:
                if "locked" not in str(exc).lower():
                    raise
                return JsonResponse(
                    {"detail": "Baza jest zajęta. Spróbuj ponownie za chwilę."}, status=503
                )
        return super().dispatch(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()
        if isinstance(serializer.instance, ClassSession):
            validate_schedule(serializer.instance)
        elif isinstance(serializer.instance, Semester):
            validate_schedule()

    def perform_update(self, serializer):
        self.perform_create(serializer)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ScheduleConflict("Ten wpis jest używany przez zajęcia w planie.") from exc


class SemesterViewSet(ResourceViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer


class SubjectViewSet(ResourceViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class LecturerViewSet(ResourceViewSet):
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer


class GroupViewSet(ResourceViewSet):
    queryset = StudentGroup.objects.all()
    serializer_class = GroupSerializer


class RoomViewSet(ResourceViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    @action(detail=False, methods=["get"])
    def available(self, request):
        params = TimeWindowSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        busy_rooms = [session.room_id for session in overlapping_sessions(**params.validated_data)]
        rooms = self.get_queryset().exclude(pk__in=busy_rooms)
        page = self.paginate_queryset(rooms)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)


class ClassSessionViewSet(ResourceViewSet):
    queryset = ClassSession.objects.select_related("semester").all()
    serializer_class = ClassSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            params = ClassFilterSerializer(data=self.request.query_params)
            params.is_valid(raise_exception=True)
            queryset = queryset.filter(**params.validated_data)
        return queryset
