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
