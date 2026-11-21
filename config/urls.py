from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from timetable import web
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
    path("", web.plan, name="plan"),
    path("rooms/available/", web.rooms, name="available-rooms"),
    path("classes/new/", web.edit, name="class-create"),
    path("classes/<int:pk>/edit/", web.edit, name="class-edit"),
    path("classes/<int:pk>/delete/", web.delete, name="class-delete"),
    path("login/", LoginView.as_view(template_name="timetable/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("api/v1/auth/token/", obtain_auth_token, name="api-token"),
    path("api/v1/", include(router.urls)),
]
