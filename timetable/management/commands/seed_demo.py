import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from rest_framework.exceptions import APIException

from timetable.services import validate_schedule


class Command(BaseCommand):
    help = "Load the demo dataset from timetable/sql/seed_demo.sql."

    @transaction.atomic
    def handle(self, *args, **options):
        script = Path(__file__).resolve().parents[2] / "sql" / "seed_demo.sql"
        statement = ""
        with connection.cursor() as cursor:
            for line in script.read_text(encoding="utf-8").splitlines(keepends=True):
                statement += line
                if sqlite3.complete_statement(statement):
                    cursor.execute(statement)
                    statement = ""
        if statement.strip():
            raise CommandError("The demo SQL script contains an incomplete statement.")
        try:
            validate_schedule()
        except APIException as exc:
            raise CommandError("Demo data conflicts with the current timetable.") from exc
        self.stdout.write(self.style.SUCCESS("Demo data loaded successfully."))
