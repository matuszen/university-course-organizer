# Uruchomienie i obsługa kontenera

Wymagany jest Docker z działającym silnikiem. W przypadku WSL dystrybucja musi
mieć włączoną integrację z Docker Desktop. Dostęp do silnika weryfikuje `docker info`.
Polecenia zakładają uruchomienie w katalogu repozytorium.

## Obraz i proces startowy

Dockerfile korzysta z obrazu `python:3.12-alpine3.23`, aktualizuje pakiety systemowe
poleceniem `apk upgrade --no-cache` i instaluje zależności
z `uv.lock`, z pominięciem grupy deweloperskiej. Kod aplikacji oraz skrypt danych
początkowych są kopiowane do `/app`. Proces działa jako użytkownik `app`,
z UID i GID równymi 10001.

`docker-entrypoint.sh` sprawdza obecność `DJANGO_SECRET_KEY`, wykonuje
`python manage.py migrate --noinput` i przekazuje sterowanie Gunicornowi przez
`exec`. Błąd migracji przerywa start. Gunicorn nasłuchuje na `0.0.0.0:8000`
i uruchamia dwa procesy robocze. Zatrzymanie kontenera przekazuje sygnał do serwera.

Plik SQLite znajduje się pod `/data/db.sqlite3`. Wolumen `course-data` przechowuje
go niezależnie od kontenera, więc dane przetrwają jego zatrzymanie i odtworzenie.
Nazwany wolumen otrzymuje uprawnienia katalogu `/data` z obrazu. Przy własnym
bind mouncie katalog hosta musi być zapisywalny dla UID 10001.

## Konfiguracja

```sh
cp .env.example .env
```

W `.env` ustaw własny losowy `DJANGO_SECRET_KEY`. Sekret można wygenerować
poleceniem `openssl rand -hex 32`. `DJANGO_ALLOWED_HOSTS` powinno zawierać nazwy
hostów, pod którymi API będzie obsługiwać żądania. Dla dostępu lokalnego wystarcza
`localhost,127.0.0.1`. Zachowaj `DJANGO_DEBUG=0`.

Podane niżej polecenie uruchomienia ustawia `DATABASE_PATH=/data/db.sqlite3`.
Wartość przekazana przez `--env` ma pierwszeństwo przed wartością z `--env-file`,
dzięki czemu lokalna ścieżka z `.env.example` zostanie zastąpiona ścieżką wolumenu.
Docker odczytuje plik środowiskowy przy tworzeniu kontenera. Zmiana `.env` wymaga
odtworzenia kontenera, aby proces otrzymał nowe wartości.

## Budowa i uruchomienie

```sh
docker build --pull --no-cache -t course-organizer:local .
docker run -d --name course-organizer \
  --restart unless-stopped \
  --env-file .env \
  --env DATABASE_PATH=/data/db.sqlite3 \
  --publish 127.0.0.1:8000:8000 \
  --volume course-data:/data \
  course-organizer:local
```

Kontener działa w tle pod nazwą `course-organizer`. Port 8000 kontenera jest
udostępniony na porcie 8000 lokalnego hosta. Przy wdrożeniu na serwerze reverse
proxy może przekazywać żądania do tego adresu i obsługiwać HTTPS.

```sh
docker ps --filter name=course-organizer
docker logs --tail 100 course-organizer
curl --fail http://127.0.0.1:8000/api/v1/semesters/
```

Po poprawnym starcie API zwraca `200`. Na nowej bazie lista semestrów jest pusta.
W logach powinny pojawić się komunikaty `Applying database migrations.`, wynik
migracji, `Starting application.` oraz informacje o procesach Gunicorna.

## Konto administratora i dane początkowe

Polecenia administracyjne wykonuje się wewnątrz działającego kontenera, z jego
konfiguracją i dostępem do tego samego wolumenu bazy.

```sh
docker exec -it course-organizer python manage.py createsuperuser
docker exec course-organizer python manage.py seed_demo
```

`createsuperuser` interaktywnie tworzy konto z uprawnieniami do zapisu przez API.
`seed_demo` wykonuje `timetable/sql/seed_demo.sql` w transakcji i weryfikuje plan
przed zatwierdzeniem. Import może być powtarzany. Konflikt z istniejącymi zajęciami
cofa całą operację i kończy polecenie błędem. Dane startowe można zmieniać w pliku
SQL, a następnie przebudować obraz.

```sh
curl --fail 'http://127.0.0.1:8000/api/v1/classes/?weekday=1'
```

Zasady uzyskania tokenu i zapisu danych opisuje [kontrakt API](api.md).

## Logi i cykl życia

```sh
docker logs --follow course-organizer
docker stop course-organizer
docker start course-organizer
docker restart course-organizer
```

`docker logs --follow` śledzi strumienie stdout i stderr. Zakończenie podglądu
przez Ctrl+C pozostawia aplikację uruchomioną. Logi startu, migracji, Gunicorna
i poleceń administracyjnych są po angielsku.

Każdy start ponownie sprawdza migracje. Polityka `unless-stopped` wznawia aplikację
po restarcie silnika Docker, z uwzględnieniem ręcznego zatrzymania kontenera.

## Aktualizacja aplikacji

Przed aktualizacją wykonaj kopię bazy. Poniższy wariant zatrzymuje zapis na czas
kopiowania. Katalog `backups` powstaje na hoście.

```sh
mkdir -p backups
docker stop course-organizer
docker cp course-organizer:/data/db.sqlite3 ./backups/db.sqlite3
```

Przy kolejnych kopiach stosuj osobne nazwy plików, aby zachować wcześniejsze wersje.
Następnie przebuduj obraz i odtwórz kontener z tym samym wolumenem oraz konfiguracją.

```sh
docker build --pull --no-cache -t course-organizer:local .
docker rm course-organizer
docker run -d --name course-organizer \
  --restart unless-stopped \
  --env-file .env \
  --env DATABASE_PATH=/data/db.sqlite3 \
  --publish 127.0.0.1:8000:8000 \
  --volume course-data:/data \
  course-organizer:local
```

Usunięcie kontenera przez `docker rm` zachowuje nazwany wolumen `course-data`.
Nowy kontener wykona migracje na istniejącej bazie. Po aktualizacji sprawdź logi
i odpowiedź API. Powrót do starszej wersji aplikacji wymaga uwzględnienia zgodności
jej schematu z wykonanymi migracjami.

## Obraz z GitHub Container Registry

CI publikuje obraz po udanych testach, skanie podatności i próbie uruchomienia
na gałęzi `main`.
Dla konkretnego wydania wybierz tag równy pełnemu SHA commita.

```sh
docker pull ghcr.io/matuszen/university-course-organizer:latest
```

Aby uruchomić opublikowany obraz, w poleceniu `docker run` zastąp końcowe
`course-organizer:local` przez `ghcr.io/matuszen/university-course-organizer:latest`
lub tag SHA. W przypadku prywatnego pakietu wymagane jest wcześniejsze zalogowanie
do GHCR kontem mającym prawo odczytu pakietu.

## Diagnostyka

| Objaw | Weryfikacja |
| --- | --- |
| Kontener kończy pracę przy starcie | `docker logs course-organizer`, poprawność sekretu i migracji |
| `DisallowedHost` lub odpowiedź `400` dla poprawnego URL | `DJANGO_ALLOWED_HOSTS` i odtworzenie kontenera po zmianie `.env` |
| `unable to open database file` lub `readonly database` | ścieżka `DATABASE_PATH`, montowanie `/data` i uprawnienia katalogu |
| Hostowy port 8000 jest zajęty | zmiana mapowania na `127.0.0.1:8001:8000` i adresu klienta |
| Docker jest niedostępny w WSL | działający Docker Desktop oraz integracja danej dystrybucji |

## Kontrola podatności obrazu

CI pobiera aktualną bazę obrazu i buduje aplikację z wyłączonym cache warstw,
aby wykonać aktualizację pakietów także wtedy, gdy tag bazowy pozostał bez zmian.
Przed publikacją Trivy skanuje gotowy obraz, obejmując pakiety systemowe
oraz zainstalowane zależności Pythona. Wykrycie podatności `HIGH` lub `CRITICAL`
przerywa job i blokuje publikację. Skan uwzględnia również podatności, dla których
poprawka jest jeszcze niedostępna. Wynik znajduje się w logach kroku
`Scan container for high and critical vulnerabilities`.

Lokalne sprawdzenie wymaga Trivy oraz działającego Dockera.

```sh
docker build --pull --no-cache -t course-organizer:local .
trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 1 course-organizer:local
```

Raport przypisany do bazowego obrazu opisuje jego oryginalne warstwy.
Wynik gotowej aplikacji uwzględnia aktualizacje wykonane w Dockerfile i zależności
z `uv.lock`. Aktualny wynik należy sprawdzać po przebudowaniu obrazu.
[Dokumentacja skanowania obrazów](https://trivy.dev/docs/latest/target/container_image/)
