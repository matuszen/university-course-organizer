from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework.exceptions import APIException

from timetable.models import ClassSession, Lecturer, Room, Semester, StudentGroup, Subject
from timetable.services import validate_schedule


class Command(BaseCommand):
    help = "Dodaje przykładowy semestr i plan zajęć."

    @transaction.atomic
    def handle(self, *args, **options):
        semester, _ = Semester.objects.get_or_create(
            name="Zimowy 2026/2027",
            defaults={"start_date": "2026-10-01", "end_date": "2027-02-01"},
        )
        subject, _ = Subject.objects.get_or_create(name="Bazy danych")
        lecturer, _ = Lecturer.objects.get_or_create(
            email="jan.kowalski@example.org",
            defaults={"first_name": "Jan", "last_name": "Kowalski"},
        )
        room, _ = Room.objects.get_or_create(name="204")
        Room.objects.get_or_create(name="205")
        group, _ = StudentGroup.objects.get_or_create(name="I2")
        ClassSession.objects.get_or_create(
            semester=semester,
            subject=subject,
            lecturer=lecturer,
            room=room,
            group=group,
            weekday=1,
            start_time="10:00",
            end_time="11:30",
        )
        try:
            validate_schedule()
        except APIException as exc:
            raise CommandError("Dane przykładowe kolidują z aktualnym planem.") from exc
        self.stdout.write(self.style.SUCCESS("Dane przykładowe są gotowe."))
