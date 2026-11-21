# Uczelniany plan zajęć

Backend do układania tygodniowego planu zajęć z kontrolą zajętości sal,
prowadzących i grup. Python 3.12, Django, Django REST Framework i SQLite.

## Uruchomienie

Wymagane są Python 3.12 oraz uv.

```sh
uv sync --locked
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

API będzie dostępne pod `http://127.0.0.1:8000/api/v1/`.
