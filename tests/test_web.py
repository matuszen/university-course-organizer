import pytest
from django.test import Client

from timetable.models import ClassSession, Room
from timetable.serializers import ClassSessionSerializer

pytestmark = pytest.mark.django_db


def create_session(data):
    serializer = ClassSessionSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def test_public_plan_and_rooms(payload):
    session = create_session(payload)
    Room.objects.create(name="205")
    client = Client()
    response = client.get("/")
    assert response.status_code == 200
    assert "Bazy danych" in response.content.decode()
    response = client.get("/rooms/available/", payload)
    assert [room.name for room in response.context["rooms"]] == ["205"]
    assert not client.get("/", {"group": 999}).context["form"].is_valid()
    assert session.pk


def test_edit_collision_rolls_back(payload, staff):
    original = create_session(payload)
    second = create_session({**payload, "start_time": "12:00", "end_time": "13:00"})
    client = Client()
    client.force_login(staff)
    response = client.post(f"/classes/{second.pk}/edit/", payload)
    assert response.status_code == 200
    assert "kolizja" in response.content.decode().lower()
    second.refresh_from_db()
    assert second.start_time.hour == 12
    assert original.pk
    response = client.post(
        f"/classes/{second.pk}/edit/", {**payload, "start_time": "11:30", "end_time": "12:30"}
    )
    assert response.status_code == 302
    assert client.get(f"/classes/{second.pk}/delete/").status_code == 200
    assert ClassSession.objects.filter(pk=second.pk).exists()
    assert client.post(f"/classes/{second.pk}/delete/").status_code == 302
    assert not ClassSession.objects.filter(pk=second.pk).exists()


def test_permissions_and_csrf(payload, django_user_model, staff):
    client = Client(enforce_csrf_checks=True)
    assert client.get("/classes/new/").status_code == 302
    user = django_user_model.objects.create_user("reader", password="test-password")
    client.force_login(user)
    assert client.get("/classes/new/").status_code == 403
    client.force_login(staff)
    assert client.post("/classes/new/", payload).status_code == 403
    assert client.get("/logout/").status_code == 405


def test_empty_and_create(payload, staff):
    client = Client()
    assert "Brak zajęć" in client.get("/").content.decode()
    client.force_login(staff)
    assert client.post("/classes/new/", payload).status_code == 302
    assert ClassSession.objects.count() == 1


def test_empty_database():
    response = Client().get("/")
    assert response.status_code == 200
    assert "Brak semestrów" in response.content.decode()


def test_invalid_window_and_login(payload, staff):
    client = Client()
    response = client.get("/rooms/available/", {**payload, "end_time": "09:00"})
    assert response.context["form"].errors["end_time"]
    assert response.context["rooms"] is None
    assert (
        client.post(
            "/login/", {"username": staff.username, "password": "test-password"}
        ).status_code
        == 302
    )
    assert client.get("/classes/new/").status_code == 200
    assert client.post("/logout/").status_code == 302
    assert client.get("/classes/new/").status_code == 302
