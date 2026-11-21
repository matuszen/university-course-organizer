# Uczelniany plan zajęć

Backend do układania tygodniowego planu zajęć z kontrolą zajętości sal,
prowadzących i grup. Python 3.12, Django, Django REST Framework i SQLite.

## Uruchomienie

Wymagane są Python 3.12 oraz uv. Z katalogu repozytorium wykonaj poniższe polecenia.

```sh
uv sync --locked
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

API będzie dostępne pod `http://127.0.0.1:8000/api/v1/`.

```sh
curl 'http://127.0.0.1:8000/api/v1/classes/?weekday=1'
curl 'http://127.0.0.1:8000/api/v1/rooms/available/?semester=1&weekday=1&start_time=10:00&end_time=11:30'
```

Dane przykładowe to semestr zimowy 2026/2027, przedmiot Bazy danych, grupa I2,
prowadzący Jan Kowalski i sale 204 oraz 205. Zajęcia odbywają się w poniedziałek
10:00–11:30 w sali 204. Ponowne wykonanie `seed_demo` zachowuje jeden zestaw.
Identyfikatory w przykładzie odpowiadają świeżej bazie.

## Zmiana planu

Odczyt jest publiczny. Administrator loguje się przez API i przekazuje uzyskany
token w nagłówku kolejnych żądań.

```sh
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"wlasne-haslo"}'
curl -X POST http://127.0.0.1:8000/api/v1/rooms/ \
  -H 'Authorization: Token WARTOSC_TOKENU' \
  -H 'Content-Type: application/json' -d '{"name":"301"}'
```

Podstaw nazwę i hasło utworzonego konta. Wymagane jest `is_staff=True`, które
`createsuperuser` ustawia automatycznie. Zwykłe konta mogą czytać dane.

## Konfiguracja

Zmienne środowiskowe opisuje `.env.example`. Ustaw je w powłoce lub konfiguracji
kontenera. Aplikacja odczytuje środowisko procesu. Plik `.env` wymaga załadowania
przez używane narzędzie.

| Zmienna | Domyślna wartość lokalna |
| --- | --- |
| `DJANGO_DEBUG` | `0`, ustaw `1` do debugowania |
| `DJANGO_SECRET_KEY` | stały klucz deweloperski |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` |
| `DATABASE_PATH` | `db.sqlite3` w repozytorium |

Przy wdrożeniu ustaw własny losowy sekret, dozwoloną domenę i HTTPS na serwerze
proxy. Wykonuj kopie bazy SQLite, np. narzędziem backup SQLite. Plik bazy jest
pomijany przez Git. Kontener domyślnie zapisuje go w trwałym wolumenie `/data`.

## Dokumentacja i testy

- [Specyfikacja projektu](docs/specyfikacja.md)
- [Kontrakt REST API](docs/api.md)
- [Testy automatyczne](docs/testy-automatyczne.md)
- [Scenariusze ręczne](docs/testy-reczne.md)

```sh
uv run ruff check .
uv run ruff format --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest -q
```

## Kontener

```sh
docker build -t course-organizer .
docker run --rm -p 8000:8000 -v course-data:/data \
  -e DJANGO_SECRET_KEY=wlasny-losowy-sekret course-organizer
```

Start kontenera wykonuje migracje i uruchamia Gunicorn. Przy pierwszym starcie
utwórz konto, korzystając z identyfikatora działającego kontenera.

```sh
docker exec -it ID_KONTENERA /app/.venv/bin/python manage.py createsuperuser
docker exec ID_KONTENERA /app/.venv/bin/python manage.py seed_demo
```

GitHub Actions sprawdza kod i testy dla pull requestów do `main` oraz pushy na
`main`. Po udanych kontrolach push na `main` uruchamia budowę, próbę startu i
publikację obrazu `ghcr.io/matuszen/university-course-organizer` z tagami `latest`
i SHA commita. Workflow korzysta z `GITHUB_TOKEN` i uprawnienia `packages: write`.
Dostępność obrazu dla innych kont zależy od widoczności pakietu w GHCR.

## Układ projektu

`config` zawiera konfigurację Django, `timetable` modele i API, `tests` testy,
a `docs` specyfikację i scenariusze. Migracje należą do repozytorium. Zależności
są zapisane w `pyproject.toml` i zablokowane w `uv.lock`.
