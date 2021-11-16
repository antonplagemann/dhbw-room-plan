# DHBW Mannheim Raumplan

![Continuos update](https://github.com/antonplagemann/dhbw-room-plan/actions/workflows/update-room-plan.yml/badge.svg)
![Update frequency](https://img.shields.io/badge/Update%20frequency-daily-informational)
![Last updated](https://img.shields.io/badge/dynamic/json?color=blueviolet&label=Last%20update&query=%24.last_updated&url=https%3A%2F%2Fraw.githubusercontent.com%2Fantonplagemann%2Fdhbw-room-plan%2Fmain%2Fsrc%2Fassets%2Frooms.json)

Dieses Repository enthält den Quellcode und die Ressourcen für den Raumplan unter <https://rooms.plagemann.it>.

## Features

- Basiert kontinuierlich auf allen aktuell verfügbaren Kurskalendern der DHBW Mannheim.
- Beinhaltet alle Räume am Standort Coblitzallee (Eppelheim & Käfertal können auf Anfrage hinzugefügt werden).
- Wird täglich um 06:00 Uhr Morgens aktualisiert.
- Zeigt die Raumbelegung der nächsten 3 Monate.
- Zeigt an, wann ein Raum belegt ist (Kalenderansicht nach Raumwahl).
- Ansicht der heute nicht (mehr) belegten Räume (Startansicht).
- Ansicht von freien Räumen nach Uhrzeit und Datum.
- Anzeige der aktuellen oder zukünftigen Termine eines Raumes.
- Zeigt die Auslastung der Mensaria Metropol des aktuellen Tages nach Uhrzeit an.

## Mensa Auslastung

Das Diagramm für die Mensa-Auslastung wird mit den folgenden Annahmen berechnet:

- Bei jedem Kurs wird geprüft, ob es ein Vorlesungsende zwischen 11 und 14 Uhr gibt.
- Falls ja, wird diese Uhrzeit auf 15-Minuten Schritte reduziert und gespeichert.
- Unter der Annahme das ein Mensaaufenthalt bis zu 45 Minuten dauern kann, werden zwei weitere Belegungszeiten für diesen Kurs hinzugefügt (+15 bzw. +30 Minuten).
- Das Diagramm wird anschließend als die Summe der Kurse über die jeweilige Uhrzeit und die Anzahl der Kurse zu dieser Uhrzeit erstellt.
