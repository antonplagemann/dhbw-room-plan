"""Download, parse and export ical course calendar files."""

import csv
import json
import os
import re
import sys
import threading
from concurrent import futures as async_compute
from datetime import date, datetime, timezone

import requests
from dateutil.relativedelta import relativedelta
from icalevents import icalevents

from chart import ChartGenerator

TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DATE_FORMAT = '%d.%m.%Y'


class ICalParser(object):
    """Main parser class."""

    def __init__(self) -> None:
        """Initialize constants and working variables."""
        # Constants
        self.thread_lock = threading.Lock()
        # Folder name where to download all ical files
        self.download_folder = 'ical'
        # Folder name where to save all files
        self.website_folder = os.path.join('..', 'src', 'assets')
        self.ical_url = 'http://vorlesungsplan.dhbw-mannheim.de/ical.php'
        self.last_updated = datetime.now(
            timezone.utc).strftime(TIMESTAMP_FORMAT)  # Now
        self.start_date = date.today()  # Manual: date(2021, 10, 1)
        self.end_date = date.today() + relativedelta(months=+3)  # Manual: date(2021, 12, 31)
        # Contains download links in the form of '<course>, <ical-link>'
        self.links_file = 'links.txt'
        # The output file name
        self.output_file_json = 'rooms.json'
        self.output_file_csv = 'roomplan.csv'
        self.output_file_csv_raw = 'events_raw.csv'
        self.is_branch_office = re.compile('[KE][pP]?-Raum').search
        # Data
        self.icals = []
        self.events_by_date = {
            (date.today() + relativedelta(days=+i)).strftime(DATE_FORMAT): {}
            for i in range(100)
            if (date.today() + relativedelta(days=+i)) < self.end_date
        }
        self.events_by_room = {}
        self.rooms = set()

    def download_ical_list(self) -> None:
        # Download ical list
        response = requests.get(
            'https://vorlesungsplan.dhbw-mannheim.de/ical.php')
        # Parse HTML
        self.icals = re.findall(
            r'<option label="(.+?)" value="(\d+)">.+?</option>', response.text)

    def __process_ical(self, ical) -> None:
        """Downloads and parses an ical file."""
        course_name, course_id = ical
        # Process each ical of the list
        print(f"Processing '{course_name}' ({course_id}.ical)")
        # Download file
        try:
            events = icalevents.events(
                url=f'{self.ical_url}?uid={course_id}',
                start=self.start_date, end=self.end_date)
        except Exception as e:
            # Skip invalid ical or empty files
            print(e)
            print(f'\tFile {course_id}.ical couldn\'t be retrieved')
            return
        # Process each event
        for event in events:
            if not event.location or self.is_branch_office(event.location):
                # Skip events without location or not at Coblitzallee
                continue
            # Create event object
            event_obj = {
                'title': event.summary,
                'course': course_name,
                'start': event.start.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT),
                'end': event.end.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)
            }
            # Get german date string (dd.mm.yyyy)
            date_string = event.start.date().strftime(DATE_FORMAT)
            # Read and write data
            with self.thread_lock:
                # Get existing data (self.events_by_date)
                d_date = self.events_by_date.get(date_string, {})
                d_room = d_date.get(event.location, [])
                # Save changes (self.events_by_date)
                d_room.append(event_obj)
                d_date[event.location] = sorted(
                    d_room, key=lambda event: event['start'])
                self.events_by_date[date_string] = d_date
                # Get existing data (self.events_by_room)
                r_room = self.events_by_room.get(event.location, {})
                r_date = r_room.get(date_string, [])
                # Save changes (self.events_by_room)
                r_date.append(event_obj)
                r_room[date_string] = sorted(r_date, key=lambda e: e['start'])
                self.events_by_room[event.location] = r_room
        # Processing finished
        print(f'\tFile {course_id}.ical sucessfully processed')

    def parse(self) -> None:
        # Use threading (5x faster)
        with async_compute.ThreadPoolExecutor() as executor:
            # Start threads for each ical
            list(executor.map(self.__process_ical, self.icals))

        # Calculate and sort all rooms
        self.rooms = sorted(set(self.events_by_room.keys()), reverse=True)

    def export_json(self) -> None:
        """Exports all data as json."""
        # Export as json file
        filepath = os.path.join(
            sys.path[0], self.website_folder, self.output_file_json)
        with open(filepath, 'w', encoding='utf8') as jsonfile:
            export_csv_data = {
                'last_updated': self.last_updated,
                'events_by_date': self.events_by_date,
                'events_by_room': self.events_by_room
            }
            json.dump(export_csv_data, jsonfile, indent=4, sort_keys=True)

    def export_csv(self) -> None:
        """Exports all data as csv."""
        # Export room plan as csv
        csv_data = []
        # Contruct titlerow
        titlerow = ['Datum'] + self.rooms
        csv_data.append(titlerow)
        # Sort events_by_date ascending (needs to convert 'str -> datetime -> str' for sorting)
        self.events_by_date_obj = [datetime.strptime(
            date_str, DATE_FORMAT) for date_str in self.events_by_date.keys()]
        self.events_by_date_str = [date_obj.strftime(
            DATE_FORMAT) for date_obj in sorted(self.events_by_date_obj)]
        # Go though each date and build csv row
        for date in self.events_by_date_str:
            row = [date]
            for room in self.rooms:
                events = self.events_by_date[date].get(room, [])
                events_strings = [
                    datetime.strptime(event['start'], TIMESTAMP_FORMAT).strftime('%H:%M') +
                    '-' + datetime.strptime(event['end'], TIMESTAMP_FORMAT).strftime('%H:%M') +
                    ' ' + event['title'] + ' (' + event['course'] + ')'
                    for event in events
                ]
                events_string = ' & '.join(events_strings)
                row.append(events_string)
            csv_data.append(row)
        # Write to file
        filepath = os.path.join(sys.path[0], self.output_file_csv)
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows(csv_data)

    def export_raw_csv(self) -> None:
        # Export raw schedules as csv for data mining
        events = []
        csv_data = []
        # Contruct titlerow
        titlerow = ['Start', 'Ende', 'Raum', 'Kurs', 'Beschreibung']
        csv_data.append(titlerow)
        # Go though each event and build csv row
        for room_dict in self.events_by_date.values():
            for room, room_events in room_dict.items():
                for event in room_events:
                    start = event['start']
                    end = event['end']
                    description = event['title']
                    course = event['course']
                    events.append([start, end, room, course, description])
        # Sort rows by start date
        events = sorted(events, key=lambda event: event[0])
        # Change date format to german
        for start, end, room, course, description in events:
            csv_data.append(
                [
                    datetime.strptime(
                        start, TIMESTAMP_FORMAT).strftime('%d.%m.%Y %H:%M:%S'),
                    datetime.strptime(
                        end, TIMESTAMP_FORMAT).strftime('%d.%m.%Y %H:%M:%S'),
                    room,
                    course,
                    description
                ]
            )
        # Write to file
        filepath = os.path.join(sys.path[0], self.output_file_csv_raw)
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows(csv_data)

    def export_mensa_charts(self):
        target_path = os.path.join(self.website_folder, 'mensa_charts')
        chart = ChartGenerator(self.events_by_date, target_path)
        chart.generate()


# Start
print('Parser started')

parser = ICalParser()
parser.download_ical_list()
parser.parse()
parser.export_json()
parser.export_mensa_charts()

# Finished
print('Finished')
