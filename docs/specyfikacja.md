# Założenia projektu

System wspiera układanie i przeglądanie planu zajęć na uczelni. Student wyszukuje
zajęcia grupy lub prowadzącego i sprawdza dostępność sal. Administrator układa plan
przez API. Projekt bazuje na opisie Mateusza Nowaka i Łukasza Zawodzińskiego.

## Pierwsza wersja

Plan zawiera cotygodniowe terminy obowiązujące przez cały semestr. Każdy termin
ma jeden przedmiot, jednego prowadzącego, jedną grupę i jedną salę. Dni tygodnia
mają numery 1–7, od poniedziałku do niedzieli. Godziny oznaczają lokalny czas
uczelni w strefie Europe/Warsaw. Zajęcia zaczynają się i kończą tego samego dnia.

Odczyt jest publiczny. Konto Django z `is_staff=True` może zmieniać dane po
uwierzytelnieniu tokenem. Zwykłe konto ma uprawnienia odczytu. Konta tworzy się
poleceniami Django. Token przekazuje się w nagłówku `Authorization`.

## Dane

| Zasób | Pola użytkowe | Ograniczenia |
| --- | --- | --- |
| Semestr | nazwa, początek, koniec | unikalna nazwa, koniec od dnia początku |
| Przedmiot | nazwa | unikalna nazwa, do 150 znaków |
| Prowadzący | imię, nazwisko, e-mail | unikalny e-mail |
| Sala | nazwa | unikalna nazwa |
| Grupa | nazwa | unikalna nazwa |
| Termin zajęć | semestr, przedmiot, prowadzący, sala, grupa, dzień, godziny | początek przed końcem |

Pozostałe nazwy mają do 100 znaków. Wszystkie zasoby mają liczbowy identyfikator.
Pola są wymagane, puste napisy są odrzucane. Powiązania terminu wskazują istniejące
rekordy. Używane zasoby są chronione przed usunięciem.

## Kolizje

Dwie pozycje kolidują, jeśli mają wspólną salę, prowadzącego lub grupę,
wspólny dzień tygodnia i nakładające się godziny. Przedziały są prawostronnie
otwarte. Termin 10:00–11:30 może poprzedzać termin 11:30–13:00.

Przy porównaniu semestrów liczy się wspólny zakres dat wraz z oboma końcami.
Musi w nim wystąpić wskazany dzień tygodnia. Wspólna niedziela nie powoduje
kolizji poniedziałkowych zajęć. Wybrany dzień musi występować w semestrze.

API sprawdza kolizje przy tworzeniu i edycji zajęć, a także po zmianie dat
semestru. Błąd cofa całą zmianę. Wyszukiwanie wolnych sal korzysta z tej samej
funkcji porównującej przedziały. Dla MVP kontrola zmiany semestru przegląda cały
plan, co upraszcza obsługę niewielkiej bazy projektu.

Zapis odbywa się w transakcji SQLite `IMMEDIATE`. Blokada zapisu jest uzyskiwana
przed walidacją. Równoległe żądanie czeka do 20 sekund, po czym otrzymuje `503`,
jeśli blokada nadal trwa. Klient może wtedy ponowić żądanie. Wywołania ORM poza
API wymagają jawnego użycia transakcji i `validate_schedule`, tak jak `seed_demo`.
Baza dodatkowo kontroluje kolejność dat i godzin, zakres dni oraz klucze obce.

## Dalsze etapy

Kolejne wersje mogą objąć frontend Django, wyjątki kalendarzowe i tygodnie parzyste.
Automatyczne generowanie planu i integracje z systemami uczelni wymagają osobnego
rozszerzenia zakresu. Obecny projekt udostępnia API i bazę SQLite.

## Dane początkowe

Zestaw demonstracyjny jest zdefiniowany w `timetable/sql/seed_demo.sql`.
Polecenie `python manage.py seed_demo` wykonuje instrukcje SQL przez połączenie
Django w jednej transakcji, a następnie sprawdza kolizje w planie. Błąd cofa
cały import. Skrypt identyfikuje zasoby po nazwach lub adresie e-mail, a termin
po powiązaniach, dniu i godzinach. Ponowne uruchomienie pomija istniejące wpisy.
Wartości w istniejących zasobach zachowują aktualny stan.

Dane demonstracyjne ładuje się jawnie po migracjach. Komenda jest dostępna
zarówno lokalnie, jak i w obrazie kontenera. Edycja zestawu startowego odbywa się
w pliku SQL. Przy zmianie schematu trzeba utrzymać zgodność skryptu z migracjami.

Logi i komunikaty poleceń administracyjnych są w języku angielskim.
Dokumentacja oraz komunikaty walidacji zwracane przez API są w języku polskim.

## Interfejs przeglądarkowy

Szablony Django i Bootstrap udostępniają publiczny plan zajęć i wyszukiwarkę
wolnych sal. Administrator zalogowany przez sesję może zarządzać terminami.
Formularze korzystają ze wspólnej z API logiki kolizji i dostępności sal.
