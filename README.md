# University Course Organizer

REST API do zarządzania tygodniowym planem zajęć uczelni. System obsługuje
semestry, przedmioty, prowadzących, sale i grupy oraz kontroluje kolizje terminów
przy tworzeniu i aktualizacji planu.

**Stos technologiczny** — Python 3.12, Django 5.2, Django REST Framework, SQLite,
Gunicorn. Zależności są zarządzane przez uv i zapisane w `uv.lock`.

## Zakres

- Zarządzanie zasobami planu i cotygodniowymi terminami zajęć.
- Filtrowanie planu według semestru, dnia, prowadzącego i grupy.
- Wyszukiwanie sal dostępnych w zadanym przedziale godzin.
- Kontrola kolizji sal, prowadzących i grup, również między semestrami.
- Publiczny odczyt i zapis dla administratorów uwierzytelnionych tokenem.

Pierwsza wersja udostępnia backend. Reguły planowania i zakres kolejnych etapów
opisuje [specyfikacja](docs/specyfikacja.md).

## Środowisko lokalne

Wymagane są Python 3.12 i uv. Polecenia wykonuje się z katalogu repozytorium.

```sh
uv sync --locked
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

API jest dostępne pod `http://127.0.0.1:8000/api/v1/`. Konto utworzone przez
`createsuperuser` ma uprawnienia do zapisu. Uwierzytelnianie, zasoby i formaty
żądań opisuje [kontrakt API](docs/api.md).

## Konfiguracja

Konfiguracja jest odczytywana ze zmiennych środowiskowych procesu.
`.env.example` zawiera wzór ustawień. Lokalne narzędzie uruchomieniowe musi
załadować plik `.env` do środowiska, a Docker przyjmuje go przez `--env-file`.

| Zmienna | Wartość domyślna | Znaczenie |
| --- | --- | --- |
| `DJANGO_DEBUG` | `0` | `1` włącza tryb debugowania |
| `DJANGO_SECRET_KEY` | klucz deweloperski | własny losowy sekret środowiska |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | dozwolone hosty, rozdzielone przecinkami |
| `DATABASE_PATH` | `db.sqlite3` | ścieżka bazy SQLite, w obrazie `/data/db.sqlite3` |

W środowisku wdrożeniowym wymagane są własny sekret, poprawna lista hostów,
terminacja HTTPS na reverse proxy oraz kopie zapasowe bazy.

## Dane początkowe

Skrypt [`timetable/sql/seed_demo.sql`](timetable/sql/seed_demo.sql) definiuje
zestaw demonstracyjny. Po wykonaniu migracji można go załadować poleceniem

```sh
uv run python manage.py seed_demo
```

Import działa w jednej transakcji i sprawdza kolizje przed zatwierdzeniem.
Ponowne uruchomienie pomija istniejące rekordy. Zestaw obejmuje semestr zimowy
2026/2027, przedmiot Bazy danych, grupę I2, prowadzącego Jana Kowalskiego i sale
204 oraz 205. Termin demonstracyjny przypada w poniedziałki 10:00–11:30 w sali 204.

## Uruchomienie w Dockerze

Obraz zawiera aplikację, zależności wykonawcze i Gunicorn. Podczas startu wykonuje
migracje, a następnie uruchamia serwer na porcie 8000. Baza jest zapisywana
w wolumenie `/data`. Ładowanie danych demonstracyjnych jest osobną operacją.

[Instrukcja obsługi kontenera](docs/kontener.md) obejmuje budowę i uruchomienie
obrazu, konfigurację, tworzenie kont, import danych, logi, restart oraz aktualizację
aplikacji z zachowaniem bazy.

## Kontrola jakości

```sh
uv run ruff check .
uv run ruff format --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest -q
```

Testy korzystają z osobnej bazy SQLite. Szczegóły zawierają
[instrukcja testów automatycznych](docs/testy-automatyczne.md)
i [scenariusze ręczne](docs/testy-reczne.md).

## CI/CD

GitHub Actions uruchamia lint, kontrolę formatowania, weryfikację migracji i testy
dla pull requestów do `main` oraz pushy na `main`. Po udanych kontrolach na `main`
buduje obraz, sprawdza uruchomienie aplikacji z pustą bazą i publikuje go w
`ghcr.io/matuszen/university-course-organizer` z tagami `latest` oraz SHA commita.
Uprawnienia do publikacji zapewnia `GITHUB_TOKEN` z `packages: write`.

## Struktura repozytorium

| Katalog | Przeznaczenie |
| --- | --- |
| `config/` | ustawienia i konfiguracja Django |
| `timetable/` | modele, REST API, reguły kolizji i skrypt danych początkowych |
| `tests/` | testy API, współbieżności i importu danych |
| `docs/` | specyfikacja, kontrakt API i instrukcje operacyjne |
| `.github/workflows/` | kontrola jakości i publikacja obrazu |

Dokumentacja i odpowiedzi API są w języku polskim. Logi, komunikaty poleceń
administracyjnych oraz nazwy jobów i kroków CI są w języku angielskim.
