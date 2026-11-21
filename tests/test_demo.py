from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from timetable.models import ClassSession, Lecturer, Room, Semester, StudentGroup, Subject

pytestmark = pytest.mark.django_db


def test_seed_demo_is_repeatable():
    call_command("seed_demo")
    call_command("seed_demo")
    assert ClassSession.objects.count() == 1
    assert Semester.objects.count() == 1
    assert Room.objects.count() == 2
    assert Lecturer.objects.count() == Subject.objects.count() == StudentGroup.objects.count() == 1


def test_seed_conflict_rolls_back(admin, payload):
    assert admin.post("/api/v1/classes/", payload).status_code == 201
    with pytest.raises(CommandError):
        call_command("seed_demo")
    assert ClassSession.objects.count() == 1
    assert Semester.objects.count() == Room.objects.count() == Lecturer.objects.count() == 1


def test_seed_uses_existing_records_without_overwriting_them():
    lecturer = Lecturer.objects.create(
        first_name="Jan", last_name="Nowak", email="jan.kowalski@example.org"
    )
    output = StringIO()
    call_command("seed_demo", stdout=output)
    lecturer.refresh_from_db()
    assert lecturer.last_name == "Nowak"
    assert ClassSession.objects.get().lecturer_id == lecturer.pk
    assert output.getvalue().strip() == "Demo data loaded successfully."


def test_seed_handles_data_created_before_sql_script():
    semester = Semester.objects.create(
        name="Zimowy 2026/2027", start_date="2026-10-01", end_date="2027-02-01"
    )
    subject = Subject.objects.create(name="Bazy danych")
    lecturer = Lecturer.objects.create(
        first_name="Jan", last_name="Kowalski", email="jan.kowalski@example.org"
    )
    room = Room.objects.create(name="204")
    group = StudentGroup.objects.create(name="I2")
    existing = ClassSession.objects.create(
        semester=semester,
        subject=subject,
        lecturer=lecturer,
        room=room,
        group=group,
        weekday=1,
        start_time="10:00",
        end_time="11:30",
    )
    call_command("seed_demo")
    assert ClassSession.objects.get().pk == existing.pk
