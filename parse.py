import concurrent.futures
import csv
import json
import logging
import os
import re
import sys
import threading
from datetime import date, datetime, timezone

import requests
from dateutil.relativedelta import relativedelta
from icalevents import icalevents

# Get module specific logger
log = logging.getLogger('GMSync')
# Logging configuration
log.setLevel(logging.INFO)
loggingFormat = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_path = os.path.join(sys.path[0],"parser.log")
handler = logging.FileHandler(filename=file_path, mode='a', encoding="utf8")
handler.setLevel(logging.INFO)
handler.setFormatter(loggingFormat)
log.addHandler(handler)
log.info(f"Parser started")

class ICalParser():

    def __init__(self, logger: logging.Logger) -> None:
        # Constants
        self.log = logger
        self.thread_lock = threading.Lock()
        self.download_folder = "ical"  # Folder name where to download all ical files
        self.website_folder = "docs"  # Folder name where to save the json file
        self.ical_url = "http://vorlesungsplan.dhbw-mannheim.de/ical.php"
        self.last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.start_date = date.today()
        self.end_date = date.today() + relativedelta(months=+3)
        # Contains download links in the form of "<course>, <ical-link>"
        self.links_file = "links.txt"
        self.output_file = "rooms"    # The output file name (csv and json)

        # Data
        self.events_by_date = {}
        self.events_by_room = {}
        self.rooms = set()

    def download_ical_list(self) -> list:
        # Download ical list
        response = requests.get("https://vorlesungsplan.dhbw-mannheim.de/ical.php")
        # Parse HTML
        return re.findall(r'<option label="(.+?)" value="(\d+)">.+?</option>', response.text)

    def __process_ical(self, ical) -> None:
        '''Downloads and parses an ical file.'''
        course_name, course_id = ical
        # Process each ical of the list
        self.log.info(f"Processing '{course_name}' ({course_id}.ical)")
        # Download file
        try:
            events = icalevents.events(
                url=f"{self.ical_url}?uid={course_id}", 
                start=self.start_date, end=self.end_date)
            self.log.info(f'\tFile {course_id}.ical sucessfully downloaded')
        except Exception as e:
            # Skip invalid ical or empty files
            self.log.exception(e)
            self.log.info(f'\tFile {course_id}.ical couldn\'t be retrieved')
            return

        # Process each event
        for event in events:
            if not event.location:
                # Skip events without location
                continue
            # Create event string
            event_start = event.start.strftime("%H:%M")
            event_end = event.end.strftime("%H:%M")
            events_string = f"{event_start}-{event_end}: {event.summary} ({course_name})"
            # Get german date string (dd.mm.yyyy)
            date_string = event.start.date().strftime("%d.%m.%Y")
            with self.thread_lock:
                # Get existing csv_data (self.events_by_date)
                d_date = self.events_by_date.get(date_string, {})
                d_room = d_date.get(event.location, [])
                # Save changes (self.events_by_date)
                d_room.append(events_string)
                d_date[event.location] = d_room
                self.events_by_date[date_string] = d_date
                # Get existing csv_data (self.events_by_room)
                r_room = self.events_by_room.get(event.location, {})
                r_date = r_room.get(date_string, [])
                # Save changes (self.events_by_room)
                r_date.append(events_string)
                r_room[date_string] = r_date
                self.events_by_room[event.location] = r_room
        # Processing finished
        self.log.info(f'\tFile {course_id}.ical sucessfully processed')

    def parse(self, ical_list) -> None:
        # Process each ical of the list
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(executor.map(self.__process_ical, ical_list))

        # Calculate and sort all rooms
        self.rooms = sorted(set(self.events_by_room.keys()), reverse=True)

    def __export_csv(self) -> None:
        '''Exports all data as csv.'''
        # Export as csv
        csv_data = []
        # Contruct titlerow
        titlerow = ["Datum"] + self.rooms
        csv_data.append(titlerow)
        # Sort self.events_by_date ascending (needs to convert 'str -> datetime -> str' for sorting)
        self.events_by_date_obj = [datetime.strptime(
            date_str, "%d.%m.%Y") for date_str in self.events_by_date.keys()]
        self.events_by_date_str = [date_obj.strftime(
            "%d.%m.%Y") for date_obj in sorted(self.events_by_date_obj)]
        # Go though each date and build csv row
        for date in self.events_by_date_str:
            row = [date]
            for room in self.rooms:
                events_strings = self.events_by_date[date].get(room, [])
                events_string = " & ".join(events_strings)
                row.append(events_string)
            csv_data.append(row)
        # Write to file
        filepath = os.path.join(sys.path[0], self.output_file + '.csv')
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows(csv_data)

    def __export_json(self) -> None:
        '''Exports all data as json.'''
        # Export also as json file
        filepath = os.path.join(sys.path[0], self.website_folder, self.output_file + '.json')
        with open(filepath, 'w', encoding="utf8") as jsonfile:
            export_csv_data = {
                "last_updated": self.last_updated,
                "events_by_date": self.events_by_date,
                "events_by_room": self.events_by_room
            }
            json.dump(export_csv_data, jsonfile, indent=4, sort_keys=True)

    def export(self) -> None:
        "Call all export functions."
        self.__export_csv()
        self.__export_json()

parser = ICalParser(log)
icals = parser.download_ical_list()
parser.parse(icals)
parser.export()

# Finished
log.info("Finished")
