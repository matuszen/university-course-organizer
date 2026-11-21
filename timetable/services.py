from datetime import timedelta

from rest_framework.exceptions import APIException, ValidationError

from .models import ClassSession


class ScheduleConflict(APIException):
    status_code = 409
    default_detail = "Termin koliduje z istniejącym planem."
    default_code = "schedule_conflict"

    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)
        if isinstance(detail, dict):
            self.detail = detail


def occurs_between(start_date, end_date, weekday):
    first_date = start_date + timedelta(days=(weekday - start_date.isoweekday()) % 7)
    return first_date <= end_date


def overlapping_sessions(semester, weekday, start_time, end_time):
    candidates = ClassSession.objects.select_related("semester").filter(
        weekday=weekday,
        start_time__lt=end_time,
        end_time__gt=start_time,
        semester__start_date__lte=semester.end_date,
        semester__end_date__gte=semester.start_date,
    )
    return [
        session
        for session in candidates
        if occurs_between(
            max(semester.start_date, session.semester.start_date),
            min(semester.end_date, session.semester.end_date),
            weekday,
        )
    ]


def validate_schedule(changed_session=None):
    sessions = (
        [changed_session] if changed_session else ClassSession.objects.select_related("semester")
    )
    for session in sessions:
        if not occurs_between(
            session.semester.start_date, session.semester.end_date, session.weekday
        ):
            raise ValidationError({"weekday": "Ten dzień nie występuje w zakresie dat semestru."})
        conflicts = []
        for other in overlapping_sessions(
            session.semester, session.weekday, session.start_time, session.end_time
        ):
            if other.pk == session.pk:
                continue
            for resource in ("room", "lecturer", "group"):
                if getattr(session, f"{resource}_id") == getattr(other, f"{resource}_id"):
                    conflicts.append({"resource": resource, "class_id": other.pk})
        if conflicts:
            raise ScheduleConflict({"detail": "Kolizja terminów zajęć.", "conflicts": conflicts})
