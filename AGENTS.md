# Zasady pracy

Dokumentację, komentarze i komunikaty odpowiedzi API pisz po polsku. Logi, komunikaty
poleceń administracyjnych, identyfikatory w kodzie oraz tytuły commitów pisz po angielsku. Tytuł commita ma najwyżej 70 znaków, bez opisu.

Polecenia powłoki poprzedzaj `rtk`, w razie potrzeby używając `rtk proxy`.

Instalacja środowiska odbywa się przez `uv sync --locked`.
Przed commitem uruchom `uv run ruff check .`, `uv run ruff format --check .`,
`uv run python manage.py check`, `uv run python manage.py makemigrations --check --dry-run`
oraz `uv run pytest`. Aktualizuj dokumentację razem ze zmianami kontraktu API.

Reguły planowania znajdują się w aplikacji `timetable`. Zachowaj wspólną logikę
kolizji dla zapisu zajęć i wyszukiwania wolnych sal. Dołączaj migracje przy zmianach modeli.
Nie commituj bazy SQLite, tokenów, haseł ani lokalnego środowiska.

Dane demonstracyjne utrzymuj w `timetable/sql/seed_demo.sql`. Polecenie `seed_demo`
uruchamia skrypt w transakcji i sprawdza spójność planu. Zachowaj możliwość ponownego
wykonania skryptu oraz obsługę istniejących danych.
