import concurrent.futures
import csv
import json
import os
import re
import sys
import threading
from datetime import date, datetime, timezone

import requests
from dateutil.relativedelta import relativedelta
from icalevents import icalevents


class ICalParser():
    '''Main parser class.'''

    def __init__(self) -> None:
        # Constants
        self.thread_lock = threading.Lock()
        self.download_folder = "ical"  # Folder name where to download all ical files
        self.website_folder = "docs"  # Folder name where to save the json file
        self.ical_url = "http://vorlesungsplan.dhbw-mannheim.de/ical.php"
        self.last_updated = datetime.now(
            timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") # Now
        self.start_date = date.today()
        self.end_date = date.today() + relativedelta(months=+3)
        # Contains download links in the form of "<course>, <ical-link>"
        self.links_file = "links.txt"
        self.output_file = "rooms.json"    # The output file name

        # Data
        self.icals = []
        self.events_by_date = {
            (date.today() + relativedelta(days=+i)).strftime("%d.%m.%Y"): {}
            for i in range(100)
            if (date.today() + relativedelta(days=+i)) < self.end_date
        }
        self.events_by_room = {}
        self.rooms = set()

    def download_ical_list(self) -> None:
        # Download ical list
        response = requests.get(
            "https://vorlesungsplan.dhbw-mannheim.de/ical.php")
        # Parse HTML
        self.icals = re.findall(
            r'<option label="(.+?)" value="(\d+)">.+?</option>', response.text)

    def __process_ical(self, ical) -> None:
        '''Downloads and parses an ical file.'''
        course_name, course_id = ical
        # Process each ical of the list
        print(f"Processing '{course_name}' ({course_id}.ical)")
        # Download file
        try:
            events = icalevents.events(
                url=f"{self.ical_url}?uid={course_id}",
                start=self.start_date, end=self.end_date)
        except Exception as e:
            # Skip invalid ical or empty files
            print(e)
            print(f'\tFile {course_id}.ical couldn\'t be retrieved')
            return
        # Process each event
        for event in events:
            if not event.location:
                # Skip events without location
                continue
            # Create event object
            event_obj = {
                "title": event.summary,
                "course": course_name,
                "start": event.start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": event.end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            # Get german date string (dd.mm.yyyy)
            date_string = event.start.date().strftime("%d.%m.%Y")
            # Read and write data
            with self.thread_lock:
                # Get existing data (self.events_by_date)
                d_date = self.events_by_date.get(date_string, {})
                d_room = d_date.get(event.location, [])
                # Save changes (self.events_by_date)
                d_room.append(event_obj)
                d_date[event.location] = sorted(d_room, key=lambda e: e["start"])
                self.events_by_date[date_string] = d_date
                # Get existing data (self.events_by_room)
                r_room = self.events_by_room.get(event.location, {})
                r_date = r_room.get(date_string, [])
                # Save changes (self.events_by_room)
                r_date.append(event_obj)
                r_room[date_string] = sorted(r_date, key=lambda e: e["start"])
                self.events_by_room[event.location] = r_room
        # Processing finished
        print(f'\tFile {course_id}.ical sucessfully processed')

    def parse(self) -> None:
        # Use threading (5x faster)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start threads for each ical
            list(executor.map(self.__process_ical, self.icals))

        # Calculate and sort all rooms
        self.rooms = sorted(set(self.events_by_room.keys()), reverse=True)

    def export(self) -> None:
        '''Exports all data as json.'''
        # Export also as json file
        filepath = os.path.join(
            sys.path[0], self.website_folder, self.output_file)
        with open(filepath, 'w', encoding="utf8") as jsonfile:
            export_csv_data = {
                "last_updated": self.last_updated,
                "events_by_date": self.events_by_date,
                "events_by_room": self.events_by_room
            }
            json.dump(export_csv_data, jsonfile, indent=4, sort_keys=True)


# Start
print("Parser started")

parser = ICalParser()
parser.download_ical_list()
parser.parse()
parser.export()

# Finished
print("Finished")
