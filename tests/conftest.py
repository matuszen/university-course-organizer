import pytest
from rest_framework.test import APIClient

from timetable.models import Lecturer, Room, Semester, StudentGroup, Subject


@pytest.fixture(scope="session")
def django_db_modify_db_settings(django_db_modify_db_settings_parallel_suffix, tmp_path_factory):
    from django.conf import settings

    settings.DATABASES["default"]["TEST"]["NAME"] = str(
        tmp_path_factory.mktemp("database") / "test.sqlite3"
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def staff(django_user_model):
    return django_user_model.objects.create_user("admin", password="test-password", is_staff=True)


@pytest.fixture
def admin(staff):
    authenticated = APIClient()
    authenticated.force_authenticate(staff)
    return authenticated


@pytest.fixture
def payload(db):
    semester = Semester.objects.create(
        name="Zimowy 2026", start_date="2026-10-01", end_date="2027-02-01"
    )
    subject = Subject.objects.create(name="Bazy danych")
    lecturer = Lecturer.objects.create(
        first_name="Jan", last_name="Kowalski", email="jan@example.org"
    )
    room = Room.objects.create(name="204")
    group = StudentGroup.objects.create(name="I2")
    return {
        "semester": semester.pk,
        "subject": subject.pk,
        "lecturer": lecturer.pk,
        "room": room.pk,
        "group": group.pk,
        "weekday": 1,
        "start_time": "10:00",
        "end_time": "11:30",
    }
