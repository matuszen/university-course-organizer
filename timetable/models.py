from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Semester(models.Model):
    name = models.CharField("nazwa", max_length=100, unique=True)
    start_date = models.DateField("początek")
    end_date = models.DateField("koniec")

    class Meta:
        ordering = ["start_date", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="semester_dates_ordered",
            )
        ]


class Subject(models.Model):
    name = models.CharField("nazwa", max_length=150, unique=True)

    class Meta:
        ordering = ["name", "id"]


class Lecturer(models.Model):
    first_name = models.CharField("imię", max_length=100)
    last_name = models.CharField("nazwisko", max_length=100)
    email = models.EmailField("e-mail", unique=True)

    class Meta:
        ordering = ["last_name", "first_name", "id"]


class Room(models.Model):
    name = models.CharField("nazwa", max_length=100, unique=True)

    class Meta:
        ordering = ["name", "id"]


class StudentGroup(models.Model):
    name = models.CharField("nazwa", max_length=100, unique=True)

    class Meta:
        ordering = ["name", "id"]


class ClassSession(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, verbose_name="semestr")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, verbose_name="przedmiot")
    lecturer = models.ForeignKey(Lecturer, on_delete=models.PROTECT, verbose_name="prowadzący")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, verbose_name="sala")
    group = models.ForeignKey(StudentGroup, on_delete=models.PROTECT, verbose_name="grupa")
    weekday = models.PositiveSmallIntegerField(
        "dzień tygodnia", validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    start_time = models.TimeField("godzina rozpoczęcia")
    end_time = models.TimeField("godzina zakończenia")

    class Meta:
        ordering = ["semester__start_date", "semester_id", "weekday", "start_time", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="class_times_ordered",
            ),
            models.CheckConstraint(
                condition=models.Q(weekday__gte=1, weekday__lte=7), name="class_weekday_valid"
            ),
        ]
        indexes = [models.Index(fields=["weekday", "start_time", "end_time"])]
