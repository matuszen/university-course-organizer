from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from timetable.views import (
    ClassSessionViewSet,
    GroupViewSet,
    LecturerViewSet,
    RoomViewSet,
    SemesterViewSet,
    SubjectViewSet,
)

router = DefaultRouter()
router.register("semesters", SemesterViewSet)
router.register("subjects", SubjectViewSet)
router.register("lecturers", LecturerViewSet)
router.register("rooms", RoomViewSet)
router.register("groups", GroupViewSet)
router.register("classes", ClassSessionViewSet)

urlpatterns = [
    path("api/v1/auth/token/", obtain_auth_token, name="api-token"),
    path("api/v1/", include(router.urls)),
]
