# DHBW Mannheim Raumplan

⚠️Archived⚠️: This repository is inactive as of 04.01.2024. Please open an issue if you're still interested in using it.

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
- Zeigt die Auslastung der Mensaria Metropol des gewählten Tages nach Uhrzeit an.

**Hinweis**: Nicht alle Räume können über die Suchfunktion gefunden werden: Die Räume werden aus den Terminen der Kurskalender der nächsten 3 Monate ermittelt. Wenn ein Raum dort bei keinem Kurs eingetragen ist, fehlt er auch in der Raumliste.

## Mensa Auslastung

Die Diagramme für die Mensa-Auslastung werden mit den folgenden Annahmen berechnet:

- Bei jedem Kurs wird geprüft, ob es ein Vorlesungsende zwischen 11 und 14 Uhr gibt.
- Falls ja, wird diese Uhrzeit auf 15-Minuten Schritte reduziert und gespeichert.
- Unter der Annahme das ein Mensaaufenthalt bis zu 45 Minuten dauern kann, werden zwei weitere Belegungszeiten für diesen Kurs hinzugefügt (+15 bzw. +30 Minuten).
- Das Diagramm wird anschließend mit den Uhrzeiten (x-Achse) und der Anzahl der Kurse zu diesen Uhrzeiten (y-Achse) erstellt.
- Die maximale Auslastung pro Uhrzeit (2-Wochen-Maximum) ist zusätzlich als graue Linie gezeichnet.
- Die durchschnittliche Auslastung (2-Wochen-Durchschnitt) wird mit einer lila-farbigen Linie dargestellt.
- Diagramme werden täglich für die nächsten 2 Wochen berechnet (exkl. Wochenende).
