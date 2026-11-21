from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from timetable.models import ClassSession, Lecturer, Room, Semester, StudentGroup, Subject

pytestmark = pytest.mark.django_db


def test_seed_demo_is_repeatable():
    call_command("seed_demo")
    call_command("seed_demo")
    assert ClassSession.objects.count() == 12
    assert Semester.objects.count() == 1
    assert Room.objects.count() == 5
    assert Lecturer.objects.count() == 4
    assert Subject.objects.count() == 5
    assert list(StudentGroup.objects.values_list("name", flat=True)) == [
        "ABiBD1",
        "ABiBD2",
        "ABiBD3",
    ]


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
    assert (
        ClassSession.objects.get(subject__name="Bazy danych", group__name="ABiBD1").lecturer_id
        == lecturer.pk
    )
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
    assert ClassSession.objects.filter(pk=existing.pk, group__name="ABiBD1").exists()


def test_demo_admin_is_created_and_preserved(django_user_model):
    call_command("seed_demo")
    user = django_user_model.objects.get(username="admin")
    assert user.is_staff and user.check_password("admin")
    user.set_password("changed-password")
    user.save()
    call_command("seed_demo")
    user.refresh_from_db()
    assert user.check_password("changed-password")
