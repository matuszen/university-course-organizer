from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections
from rest_framework.test import APIClient

from timetable.models import ClassSession, Lecturer, Room, Semester, StudentGroup

pytestmark = pytest.mark.django_db
URL = "/api/v1/classes/"


def test_public_read_and_staff_write(client, admin, payload):
    response = admin.post(URL, payload)
    assert response.status_code == 201
    assert client.get(URL).data["count"] == 1
    assert client.get(f"{URL}{response.data['id']}/").status_code == 200
    assert client.post(URL, payload).status_code == 401


def test_token_and_regular_user_permissions(client, django_user_model, payload):
    django_user_model.objects.create_user("student", password="test-password")
    response = client.post(
        "/api/v1/auth/token/", {"username": "student", "password": "test-password"}
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
    assert client.get(URL).status_code == 200
    assert client.post(URL, payload).status_code == 403


@pytest.mark.parametrize("resource", ["room", "lecturer", "group"])
def test_conflict_rolls_back(admin, payload, resource):
    first = admin.post(URL, payload).data
    other = dict(payload)
    other["room"] = Room.objects.create(name="205").pk
    other["lecturer"] = Lecturer.objects.create(
        first_name="Anna", last_name="Nowak", email="anna@example.org"
    ).pk
    other["group"] = StudentGroup.objects.create(name="I3").pk
    other[resource] = payload[resource]
    response = admin.post(URL, other)
    assert response.status_code == 409
    assert response.data["conflicts"][0]["resource"] == resource
    assert int(response.data["conflicts"][0]["class_id"]) == first["id"]
    assert ClassSession.objects.count() == 1


def test_adjacent_times_update_and_delete(admin, payload):
    first = admin.post(URL, payload).data
    assert admin.patch(f"{URL}{first['id']}/", {"start_time": "10:15"}).status_code == 200
    second = admin.post(URL, {**payload, "start_time": "11:30", "end_time": "13:00"})
    assert second.status_code == 201
    response = admin.patch(f"{URL}{second.data['id']}/", {"start_time": "11:00"})
    assert response.status_code == 409
    assert admin.get(f"{URL}{second.data['id']}/").data["start_time"] == "11:30:00"
    assert admin.delete(f"{URL}{first['id']}/").status_code == 204


@pytest.mark.parametrize(
    "changes",
    [
        {"weekday": 0},
        {"weekday": 8},
        {"start_time": "12:00"},
        {"end_time": "10:00"},
        {"room": 99999},
        {"start_time": "bad"},
    ],
)
def test_invalid_class(admin, payload, changes):
    assert admin.post(URL, {**payload, **changes}).status_code == 400
    assert ClassSession.objects.count() == 0


@pytest.mark.parametrize(
    "resource,field",
    [
        ("semesters", "semester"),
        ("subjects", "subject"),
        ("lecturers", "lecturer"),
        ("rooms", "room"),
        ("groups", "group"),
    ],
)
def test_protected_resource(admin, payload, resource, field):
    admin.post(URL, payload)
    assert admin.delete(f"/api/v1/{resource}/{payload[field]}/").status_code == 409


@pytest.mark.parametrize(
    "resource,body",
    [
        ("semesters", {"name": "Letni", "start_date": "2027-03-01", "end_date": "2027-06-30"}),
        ("subjects", {"name": "Matematyka"}),
        ("rooms", {"name": "100"}),
        ("groups", {"name": "I1"}),
        ("lecturers", {"first_name": "Jan", "last_name": "Nowak", "email": "j@example.org"}),
    ],
)
def test_resource_crud(admin, client, resource, body):
    url = f"/api/v1/{resource}/"
    created = admin.post(url, body)
    assert created.status_code == 201
    detail = f"{url}{created.data['id']}/"
    assert admin.put(detail, body).status_code == 200
    assert admin.patch(detail, {}).status_code == 200
    assert client.get(url).data["count"] == 1
    assert client.get(detail).status_code == 200
    assert client.delete(detail).status_code == 401


def test_filters_and_availability(admin, payload):
    admin.post(URL, payload)
    free = Room.objects.create(name="300")
    filters = {key: payload[key] for key in ("semester", "weekday", "lecturer", "group")}
    assert admin.get(URL, filters).data["count"] == 1
    assert admin.get(URL, {**filters, "weekday": 2}).data["count"] == 0
    assert admin.get(URL, {"weekday": "bad"}).status_code == 400
    window = {key: payload[key] for key in ("semester", "weekday", "start_time", "end_time")}
    response = admin.get("/api/v1/rooms/available/", window)
    assert [room["id"] for room in response.data["results"]] == [free.pk]
    assert admin.get("/api/v1/rooms/available/").status_code == 400
    assert admin.get("/api/v1/rooms/available/", {**window, "end_time": "09:00"}).status_code == 400


def test_semester_boundaries_and_rollback(admin, payload):
    admin.post(URL, payload)
    # Wspólna niedziela nie tworzy kolizji poniedziałkowych zajęć.
    semester = Semester.objects.create(
        name="Krótki", start_date="2027-01-31", end_date="2027-01-31"
    )
    assert admin.post(URL, {**payload, "semester": semester.pk}).status_code == 400
    semester.end_date = "2027-02-07"
    semester.start_date = "2027-02-01"
    semester.save()
    assert admin.post(URL, {**payload, "semester": semester.pk}).status_code == 409
    semester.start_date = "2027-02-02"
    semester.end_date = "2027-02-08"
    semester.save()
    assert admin.post(URL, {**payload, "semester": semester.pk}).status_code == 201
    response = admin.patch(f"/api/v1/semesters/{semester.pk}/", {"start_date": "2027-02-01"})
    assert response.status_code == 409
    semester.refresh_from_db()
    assert semester.start_date.isoformat() == "2027-02-02"
    assert (
        admin.patch(f"/api/v1/semesters/{semester.pk}/", {"end_date": "2027-01-01"}).status_code
        == 400
    )


def test_overlapping_dates_without_shared_weekday(admin, payload):
    first = Semester.objects.get(pk=payload["semester"])
    first.end_date = "2027-01-31"
    first.save()
    assert admin.post(URL, payload).status_code == 201
    second = Semester.objects.create(name="Drugi", start_date="2027-01-31", end_date="2027-02-08")
    assert admin.post(URL, {**payload, "semester": second.pk}).status_code == 201


@pytest.mark.django_db(transaction=True)
def test_concurrent_booking(staff, payload):
    barrier = Barrier(2)

    def book():
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(staff)
            barrier.wait(timeout=10)
            return client.post(URL, payload).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: book(), range(2)))
    assert sorted(results) == [201, 409]
    assert ClassSession.objects.count() == 1
