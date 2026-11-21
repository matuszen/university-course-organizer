-- Dane początkowe środowiska demonstracyjnego.
-- Transakcję i kontrolę kolizji zapewnia polecenie seed_demo.

INSERT INTO timetable_semester (name, start_date, end_date)
VALUES ('Zimowy 2026/2027', '2026-10-01', '2027-02-01')
ON CONFLICT (name) DO NOTHING;

INSERT INTO timetable_subject (name)
VALUES ('Bazy danych'), ('Programowanie w Pythonie'), ('Analiza danych'),
       ('Sieci komputerowe'), ('Matematyka dyskretna')
ON CONFLICT (name) DO NOTHING;

INSERT INTO timetable_lecturer (first_name, last_name, email)
VALUES ('Jan', 'Kowalski', 'jan.kowalski@example.org'),
       ('Anna', 'Nowak', 'anna.nowak@example.org'),
       ('Piotr', 'Wiśniewski', 'piotr.wisniewski@example.org'),
       ('Maria', 'Wójcik', 'maria.wojcik@example.org')
ON CONFLICT (email) DO NOTHING;

INSERT INTO timetable_room (name)
VALUES ('204'), ('205'), ('101'), ('102'), ('Laboratorium 1')
ON CONFLICT (name) DO NOTHING;

UPDATE timetable_studentgroup SET name = 'ABiBD1'
WHERE name = 'I2'
  AND NOT EXISTS (SELECT 1 FROM timetable_studentgroup WHERE name = 'ABiBD1');

INSERT INTO timetable_studentgroup (name)
VALUES ('ABiBD1'), ('ABiBD2'), ('ABiBD3')
ON CONFLICT (name) DO NOTHING;

INSERT INTO timetable_classsession (
    semester_id, subject_id, lecturer_id, room_id, group_id,
    weekday, start_time, end_time
)
SELECT semester.id, subject.id, lecturer.id, room.id, student_group.id,
       1, '10:00:00', '11:30:00'
FROM timetable_semester AS semester
CROSS JOIN timetable_subject AS subject
CROSS JOIN timetable_lecturer AS lecturer
CROSS JOIN timetable_room AS room
CROSS JOIN timetable_studentgroup AS student_group
WHERE semester.name = 'Zimowy 2026/2027'
  AND subject.name = 'Bazy danych'
  AND lecturer.email = 'jan.kowalski@example.org'
  AND room.name = '204'
  AND student_group.name = 'ABiBD1'
  AND NOT EXISTS (
      SELECT 1
      FROM timetable_classsession AS existing
      WHERE existing.semester_id = semester.id
        AND existing.subject_id = subject.id
        AND existing.lecturer_id = lecturer.id
        AND existing.room_id = room.id
        AND existing.group_id = student_group.id
        AND existing.weekday = 1
        AND existing.start_time = '10:00:00'
        AND existing.end_time = '11:30:00'
  );

WITH demo(subject, email, room, student_group, weekday, start_time, end_time) AS (
    VALUES
    ('Programowanie w Pythonie', 'anna.nowak@example.org', 'Laboratorium 1', 'ABiBD1', 2, '08:00:00', '09:30:00'),
    ('Analiza danych', 'piotr.wisniewski@example.org', '101', 'ABiBD1', 3, '12:00:00', '13:30:00'),
    ('Sieci komputerowe', 'maria.wojcik@example.org', '102', 'ABiBD1', 4, '14:00:00', '15:30:00'),
    ('Matematyka dyskretna', 'jan.kowalski@example.org', '205', 'ABiBD1', 5, '09:00:00', '10:30:00'),
    ('Bazy danych', 'jan.kowalski@example.org', '204', 'ABiBD2', 1, '11:30:00', '13:00:00'),
    ('Programowanie w Pythonie', 'anna.nowak@example.org', 'Laboratorium 1', 'ABiBD2', 2, '10:00:00', '11:30:00'),
    ('Analiza danych', 'piotr.wisniewski@example.org', '101', 'ABiBD2', 3, '14:00:00', '15:30:00'),
    ('Sieci komputerowe', 'maria.wojcik@example.org', '102', 'ABiBD2', 4, '16:00:00', '17:30:00'),
    ('Bazy danych', 'jan.kowalski@example.org', '204', 'ABiBD3', 1, '14:00:00', '15:30:00'),
    ('Programowanie w Pythonie', 'anna.nowak@example.org', 'Laboratorium 1', 'ABiBD3', 2, '12:00:00', '13:30:00'),
    ('Matematyka dyskretna', 'jan.kowalski@example.org', '205', 'ABiBD3', 5, '11:00:00', '12:30:00')
)
INSERT INTO timetable_classsession (
    semester_id, subject_id, lecturer_id, room_id, group_id, weekday, start_time, end_time
)
SELECT semester.id, subject.id, lecturer.id, room.id, student_group.id,
       demo.weekday, demo.start_time, demo.end_time
FROM demo
JOIN timetable_semester semester ON semester.name = 'Zimowy 2026/2027'
JOIN timetable_subject subject ON subject.name = demo.subject
JOIN timetable_lecturer lecturer ON lecturer.email = demo.email
JOIN timetable_room room ON room.name = demo.room
JOIN timetable_studentgroup student_group ON student_group.name = demo.student_group
WHERE NOT EXISTS (
    SELECT 1 FROM timetable_classsession existing
    WHERE existing.semester_id = semester.id AND existing.subject_id = subject.id
      AND existing.lecturer_id = lecturer.id AND existing.room_id = room.id
      AND existing.group_id = student_group.id AND existing.weekday = demo.weekday
      AND existing.start_time = demo.start_time AND existing.end_time = demo.end_time
);
