from rest_framework import serializers

from .models import ClassSession, Lecturer, Room, Semester, StudentGroup, Subject
from .services import occurs_between


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ["id", "name", "start_date", "end_date"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and start > end:
            raise serializers.ValidationError({"end_date": "Koniec musi przypadać po początku."})
        return attrs


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]


class LecturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecturer
        fields = ["id", "first_name", "last_name", "email"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroup
        fields = ["id", "name"]


class TimeWindowSerializer(serializers.Serializer):
    semester = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all())
    weekday = serializers.IntegerField(min_value=1, max_value=7)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError(
                {"end_time": "Godzina zakończenia musi być późniejsza niż rozpoczęcia."}
            )
        semester = attrs["semester"]
        if not occurs_between(semester.start_date, semester.end_date, attrs["weekday"]):
            raise serializers.ValidationError({"weekday": "Ten dzień nie występuje w semestrze."})
        return attrs


class ClassSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSession
        fields = [
            "id",
            "semester",
            "subject",
            "lecturer",
            "room",
            "group",
            "weekday",
            "start_time",
            "end_time",
        ]

    def validate(self, attrs):
        values = {
            name: attrs.get(name, getattr(self.instance, name, None))
            for name in ("semester", "weekday", "start_time", "end_time")
        }
        TimeWindowSerializer().validate(values)
        return attrs


class ClassFilterSerializer(serializers.Serializer):
    semester = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all(), required=False)
    weekday = serializers.IntegerField(min_value=1, max_value=7, required=False)
    lecturer = serializers.PrimaryKeyRelatedField(queryset=Lecturer.objects.all(), required=False)
    group = serializers.PrimaryKeyRelatedField(queryset=StudentGroup.objects.all(), required=False)
