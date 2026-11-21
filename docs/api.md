# REST API

Adres bazowy to `/api/v1/`. Żądania zapisu przyjmują JSON. Odpowiedzi są w JSON.
Ścieżki kończą się ukośnikiem. Pola `id` są tylko do odczytu.

## Uwierzytelnianie

`POST /api/v1/auth/token/` przyjmuje `username` i `password`, zwraca `token`.
Token zachowuje ważność do usunięcia lub odtworzenia. Django udostępnia polecenie
`drf_create_token -r NAZWA_UZYTKOWNIKA` do jego odtworzenia.

```sh
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"wlasne-haslo"}'
```

W kolejnych żądaniach podaj `Authorization: Token WARTOSC_TOKENU`. Przy wdrożeniu
udostępniaj API przez HTTPS. Konto z `is_staff=True` może wykonywać zapis.

## Zasoby

| Ścieżka | Pola zapisu |
| --- | --- |
| `semesters/` | `name`, `start_date`, `end_date` |
| `subjects/` | `name` |
| `lecturers/` | `first_name`, `last_name`, `email` |
| `rooms/` | `name` |
| `groups/` | `name` |
| `classes/` | `semester`, `subject`, `lecturer`, `room`, `group`, `weekday`, `start_time`, `end_time` |

Każda ścieżka obsługuje `GET` listy i `POST`. Szczegóły pod `zasob/ID/` obsługują
`GET`, `PUT`, `PATCH` i `DELETE`. `PUT` wymaga wszystkich pól, `PATCH` zmienia
wskazane pola. Powiązania podaje się jako liczbowe identyfikatory. Daty mają
format `YYYY-MM-DD`, godziny `HH:MM` lub `HH:MM:SS`.

Przykładowe ciało żądania dodania zajęć, przy istniejących zasobach o ID 1.

```json
{
  "semester": 1,
  "subject": 1,
  "lecturer": 1,
  "room": 1,
  "group": 1,
  "weekday": 1,
  "start_time": "10:00",
  "end_time": "11:30"
}
```

Odpowiedź `201` zawiera te same pola, `id` nowego terminu oraz godziny zapisane
z sekundami. Usunięcie zwraca `204` z pustym ciałem.

## Listy i dostępność

Listy mają strukturę `count`, `next`, `previous`, `results`. Strona ma do 100
rekordów, numer kolejnej podaje się parametrem `page`. Zajęcia są sortowane według
początku semestru, ID semestru, dnia, godziny i ID terminu. Pozostałe listy mają
stały porządek według nazwy, nazwiska lub początku semestru oraz ID.

`GET classes/?semester=1&weekday=1&lecturer=1&group=1` łączy podane filtry.
Każdy z nich jest opcjonalny. Niepoprawna wartość lub nieistniejący identyfikator
filtra zwraca `400`. Nieznane parametry są pomijane.

`GET rooms/available/?semester=1&weekday=1&start_time=10:00&end_time=11:30`
zwraca paginowaną listę wolnych sal. Wszystkie cztery parametry są wymagane.
Uwzględniane są także kolidujące zajęcia z innych semestrów o wspólnych datach.

## Błędy

| Kod | Znaczenie |
| --- | --- |
| `400` | niepoprawne lub brakujące dane |
| `401` | brak prawidłowego tokenu przy zapisie |
| `403` | konto ma za małe uprawnienia |
| `404` | brak wskazanego zasobu |
| `409` | kolizja albo próba usunięcia używanego wpisu |
| `503` | przekroczony czas oczekiwania na blokadę bazy |

Błędy walidacji przypisane są do nazw pól lub `non_field_errors`. Błędy dostępu
zawierają `detail`. Przykład kolizji z terminem o ID 7.

```json
{
  "detail": "Kolizja terminów zajęć.",
  "conflicts": [{"resource": "room", "class_id": 7}]
}
```

`resource` przyjmuje `room`, `lecturer` lub `group`. Lista może wskazać kilka
zasobów. Przy usuwaniu używanego rekordu odpowiedź ma samo pole `detail`.
