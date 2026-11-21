# Testy automatyczne

Wymagane są Python 3.12 i zależności z grupy `dev`.

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest -q
```

pytest tworzy osobną, tymczasową bazę plikową SQLite i usuwa ją po zakończeniu.
Baza aplikacji pozostaje niezależna. Wersja plikowa pozwala sprawdzić rzeczywiste
oczekiwanie na blokadę przy równoległych zapisach.

## Wybrane przypadki

```sh
uv run pytest tests/test_api.py -k conflict -v
uv run pytest tests/test_api.py -k concurrent -v
uv run pytest tests/test_demo.py -v
```

Testy API sprawdzają publiczny odczyt, pobieranie tokenu, odmowę zapisu dla konta
zwykłego użytkownika oraz CRUD administratora. Osobne przypadki obejmują kolizje
sali, prowadzącego i grupy, przylegające godziny, cofnięcie nieudanej edycji,
filtry, dostępność sal i ochronę używanych rekordów.

Test granic semestrów sprawdza wspólne daty i rzeczywiste wystąpienie dnia tygodnia.
Zmiana dat powodująca kolizję ma pozostawić poprzednie dane. Test współbieżności
wysyła dwie rezerwacje z osobnych połączeń. Oczekiwany wynik to jedno `201`, jedno
`409` i dokładnie jeden zapisany termin.

Testy danych przykładowych sprawdzają ponowne uruchomienie komendy oraz cofnięcie
całego zestawu, gdy dane kolidują z istniejącym planem. Dodatkowe przypadki
obejmują zachowanie zmienionych danych istniejącego prowadzącego, angielski
komunikat zakończenia oraz zgodność z danymi zapisanymi wcześniej przez ORM.

## Kontrola migracji i kontenera

```sh
DATABASE_PATH=/tmp/plan-check.sqlite3 uv run python manage.py migrate --noinput
docker build --pull --no-cache -t course-organizer .
docker run --rm -p 8000:8000 -v course-test:/data \
  -e DJANGO_SECRET_KEY=lokalny-sekret-do-testu course-organizer
```

Ścieżka `/tmp/plan-check.sqlite3` powinna być nową bazą przeznaczoną do testu.
W osobnym terminalu pobierz `http://127.0.0.1:8000/api/v1/semesters/`.
Oczekiwane są kod `200` i pusta lista w `results`. Po ponownym uruchomieniu
kontenera z tym samym wolumenem zapisane dane powinny nadal istnieć.

GitHub Actions wykonuje kontrolę jakości i migracji dla zmian do `main`.
Po pushu na `main` dodatkowo skanuje gotowy obraz pod kątem podatności `HIGH`
i `CRITICAL`, sprawdza start kontenera i publikuje obraz w GHCR. Wykrycie podatności
z tych kategorii blokuje publikację. Polecenie do lokalnego skanu znajduje się
w [instrukcji kontenera](kontener.md#kontrola-podatności-obrazu).

## Widoki HTML

`tests/test_web.py` sprawdza publiczny plan i dostępność sal, filtrowanie,
tworzenie i usuwanie terminów oraz wycofanie kolidującej edycji.
Obejmuje też uprawnienia administratora, ochronę CSRF i metodę wylogowania.
