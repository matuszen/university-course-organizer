# Testy ręczne API

Scenariusze zakładają świeżą bazę i dane z `seed_demo`. Przy użyciu wcześniejszej
bazy pobierz aktualne identyfikatory z list zasobów i podstaw je w żądaniach.
Polecenia wykonuj w Bashu. Serwer powinien działać w osobnym terminalu.

```sh
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Odczyt planu

```sh
curl -i 'http://127.0.0.1:8000/api/v1/classes/?semester=1&weekday=1&group=1'
curl -i http://127.0.0.1:8000/api/v1/classes/1/
```

Oba żądania powinny zwrócić `200`. Lista powinna zawierać Bazy danych w poniedziałek
od 10:00 do 11:30. Odpowiedź wskazuje przedmiot przez jego ID.

## Token i uprawnienia

```sh
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"wlasne-haslo"}'
export API_TOKEN='wstaw-token-z-odpowiedzi'
curl -i -X POST http://127.0.0.1:8000/api/v1/rooms/ \
  -H 'Content-Type: application/json' -d '{"name":"301"}'
curl -i -X POST http://127.0.0.1:8000/api/v1/rooms/ \
  -H "Authorization: Token $API_TOKEN" \
  -H 'Content-Type: application/json' -d '{"name":"301"}'
```

Podstaw nazwę utworzonego administratora i jego hasło. Pierwsze żądanie zwraca
`200` i token. Utworzenie sali bez tokenu daje `401`, z tokenem administratora
`201`. Zwykły użytkownik po zalogowaniu otrzyma przy zapisie `403`.
Powtórne utworzenie sali o tej samej nazwie powinno dać `400`.

## Kolizje i granice godzin

```sh
curl -i -X POST http://127.0.0.1:8000/api/v1/classes/ \
  -H "Authorization: Token $API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"semester":1,"subject":1,"lecturer":1,"room":1,"group":1,"weekday":1,"start_time":"11:00","end_time":"12:00"}'
curl -i -X POST http://127.0.0.1:8000/api/v1/classes/ \
  -H "Authorization: Token $API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"semester":1,"subject":1,"lecturer":1,"room":1,"group":1,"weekday":1,"start_time":"11:30","end_time":"13:00"}'
```

Pierwsze żądanie powinno zwrócić `409` z kolizjami sali, prowadzącego i grupy.
Drugie powinno zwrócić `201`. Zapamiętaj ID dodanego terminu. Następnie spróbuj
przez `PATCH classes/ID/` zmienić początek na `11:00`. Oczekiwany kod to `409`,
a ponowny `GET` powinien nadal pokazać początek o 11:30.

## Dostępność i błędne dane

```sh
curl -i 'http://127.0.0.1:8000/api/v1/rooms/available/?semester=1&weekday=1&start_time=10:00&end_time=11:30'
curl -i 'http://127.0.0.1:8000/api/v1/rooms/available/?semester=1&weekday=1&start_time=12:00&end_time=10:00'
curl -i 'http://127.0.0.1:8000/api/v1/classes/?weekday=8'
```

Pierwsza lista powinna zawierać salę 205 i dodaną salę 301. Sala 204 jest zajęta.
Dwa kolejne żądania powinny zwrócić `400`.

## Usuwanie

Usunięcie `rooms/1/` z tokenem administratora powinno zwrócić `409`, ponieważ sala
jest przypisana do zajęć. Usuń dodatkowy termin przez `DELETE classes/ID/`.
Oczekiwany kod to `204`, a późniejszy odczyt tego terminu powinien zwrócić `404`.

Daty semestrów i równoczesne rezerwacje są sprawdzane w testach automatycznych.

## Interfejs przeglądarkowy

1. Wykonaj migracje i `seed_demo`, uruchom serwer i otwórz `/`.
2. Wybierz semestr zimowy 2026/2027 i grupę ABiBD1. Sprawdź zajęcia Bazy danych
   w poniedziałek 10:00–11:30, sala 204. Skopiuj adres i sprawdź zachowanie filtrów.
3. Przejdź do wolnych sal, podaj poniedziałek i godziny 10:00–11:30.
   Sala 205 powinna być dostępna, a sala 204 zajęta.
4. Zaloguj się kontem administratora i zmień salę tych zajęć na 205.
   Po ponownym wyszukaniu sala 204 powinna być wolna.
5. Spróbuj dodać kolidujące zajęcia. Sprawdź komunikat i zachowanie danych formularza.
6. Otwórz potwierdzenie usunięcia, anuluj, a następnie potwierdź usunięcie.
7. Sprawdź logowanie, wylogowanie i układ na telefonie oraz komputerze.
