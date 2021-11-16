import concurrent.futures
import csv
import json
import os
import re
import sys
import threading
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas
import requests
from dateutil.relativedelta import relativedelta
from icalevents import icalevents


class ICalParser():
    '''Main parser class.'''

    def __init__(self) -> None:
        # Constants
        self.thread_lock = threading.Lock()
        self.download_folder = "ical"  # Folder name where to download all ical files
        self.website_folder = "../src/assets"  # Folder name where to save all files
        self.ical_url = "http://vorlesungsplan.dhbw-mannheim.de/ical.php"
        self.last_updated = datetime.now(
            timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # Now
        self.start_date = date.today()  # Manual: date(2021, 10, 1)
        self.end_date = date.today() + relativedelta(months=+3)  # Manual: date(2021, 12, 31)
        # Contains download links in the form of "<course>, <ical-link>"
        self.links_file = "links.txt"
        # The output file name
        self.output_file_json = "rooms.json"
        self.output_file_csv = "roomplan.csv"
        self.output_file_csv_raw = "events_raw.csv"
        self.is_branch_office = re.compile("[KE][pP]?-Raum").search
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
            if not event.location or self.is_branch_office(event.location):
                # Skip events without location or not at Coblitzallee
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
                d_date[event.location] = sorted(
                    d_room, key=lambda event: event["start"])
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

    def export_json(self) -> None:
        '''Exports all data as json.'''
        # Export as json file
        filepath = os.path.join(
            sys.path[0], self.website_folder, self.output_file_json)
        with open(filepath, 'w', encoding="utf8") as jsonfile:
            export_csv_data = {
                "last_updated": self.last_updated,
                "events_by_date": self.events_by_date,
                "events_by_room": self.events_by_room
            }
            json.dump(export_csv_data, jsonfile, indent=4, sort_keys=True)

    def export_csv(self) -> None:
        '''Exports all data as csv.'''
        # Export room plan as csv
        csv_data = []
        # Contruct titlerow
        titlerow = ["Datum"] + self.rooms
        csv_data.append(titlerow)
        # Sort events_by_date ascending (needs to convert 'str -> datetime -> str' for sorting)
        self.events_by_date_obj = [datetime.strptime(
            date_str, "%d.%m.%Y") for date_str in self.events_by_date.keys()]
        self.events_by_date_str = [date_obj.strftime(
            "%d.%m.%Y") for date_obj in sorted(self.events_by_date_obj)]
        # Go though each date and build csv row
        for date in self.events_by_date_str:
            row = [date]
            for room in self.rooms:
                events = self.events_by_date[date].get(room, [])
                events_strings = [
                    datetime.strptime(event["start"], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M") +
                    "-" + datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M") +
                    " " + event["title"] + " (" + event["course"] + ")"
                    for event in events
                ]
                events_string = " & ".join(events_strings)
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
        titlerow = ["Start", "Ende", "Raum", "Kurs", "Beschreibung"]
        csv_data.append(titlerow)
        # Go though each event and build csv row
        for room_dict in self.events_by_date.values():
            for room, room_events in room_dict.items():
                for event in room_events:
                    start = event["start"]
                    end = event["end"]
                    description = event["title"]
                    course = event["course"]
                    events.append([start, end, room, course, description])
        # Sort rows by start date
        events = sorted(events, key=lambda event: event[0])
        # Change date format to german
        for start, end, room, course, description in events:
            csv_data.append(
                [
                    datetime.strptime(
                        start, "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y %H:%M:%S"),
                    datetime.strptime(
                        end, "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y %H:%M:%S"),
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

    def __roundTime(self, dt: datetime = None, dateDelta: timedelta = timedelta(minutes=15)) -> datetime:
        """Round a datetime object to a multiple of a timedelta
        dt : datetime.datetime object, default now.
        dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
        Author: Thierry Husson 2012 - Use it as you want but don't blame me.
                Stijn Nevens 2014 - Changed to use only datetime objects as variables
        """
        roundTo = dateDelta.total_seconds()

        if dt == None:
            dt = datetime.datetime.now()
        seconds = (dt - dt.min).seconds
        # // is a floor division, not a comment on following line:
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        return dt + timedelta(0, rounding-seconds, -dt.microsecond)

    def __zerofill(self, dates: Dict[datetime, int], delta: timedelta = timedelta(minutes=15)):
        '''Fills a sorted date: value dict with zeros if there are gaps in the specified delta.'''
        min_date, max_date = min(dates.keys()), max(dates.keys())
        curr_date = min_date
        while curr_date < max_date:
            if not dates.get(curr_date, None):
                dates[curr_date] = 0
            curr_date += delta
        return dates

    def export_mensa_chart(self):
        # Export lunch time schedule
        today = datetime.today().strftime("%d.%m.%Y")
        events = {}
        # Go though each event and count courses
        for room_events in self.events_by_date[today].values():
            for event in room_events:
                end = self.__roundTime(datetime.strptime(
                    event["end"], "%Y-%m-%dT%H:%M:%SZ"))
                if end.time() >= time(11) and end.time() < time(14):
                    for date in [end, end + timedelta(minutes=15), end + timedelta(minutes=30)]:
                        if end.hour >= 14:
                            continue
                        if events.get(date, None):
                            events[date] += 1
                        else:
                            events[date] = 1
        # Zerofill events dict
        events = self.__zerofill(events)
        # Build sorted events list
        events_list = sorted(list(events.items()), key=lambda e: e[0])
        # Export light chart
        # options = {
        #     "theme": "seaborn",
        #     "figure_bg": "white",
        #     "grid_bg": "#EAEAF2",
        #     "grid_linewidth": 2,
        #     "bar_color": "#4C72B0",
        #     "text_color": "tab:blue",
        #     "filename": "mensa_light.png",
        # }
        # self.__exportFigure(events_list, **options)
        # Export dark chart
        options = {
            "theme": "dark_background",
            "figure_bg": "#282828",
            "grid_bg": "#282828",
            "grid_linewidth": 0.5,
            "bar_color": "#7957d5",
            "text_color": "#E39031",
            "filename": "mensa_dark.png",
        }
        self.__exportFigure(events_list, **options)

    def __exportFigure(self, events: List, **kwargs):
        y_series = [v for _, v in events]
        x_series = [k for k, _ in events]
        # Create plot
        frame = pandas.DataFrame(events, columns=[
                                 "Uhrzeit", "Anzahl Kurse in Mittagspause"]).set_index("Uhrzeit")
        # Style plot
        plt.style.use(kwargs["theme"])
        ax = frame.plot(kind="bar", rot=0, color=kwargs["bar_color"])
        figure = ax.get_figure()
        figure.set_facecolor(kwargs["figure_bg"])
        ax.set_facecolor(kwargs["grid_bg"])
        ax.set_ylabel("Anzahl Kurse", fontsize=16, fontweight='bold')
        ax.set_xlabel("Uhrzeit", fontsize=16, fontweight='bold')
        ax.yaxis.grid(True, which='major', linestyle='-',
                      linewidth=kwargs["grid_linewidth"])
        ax.xaxis.grid(False)
        legend = ax.legend(fontsize="large", frameon=True,
                           facecolor=kwargs["grid_bg"], framealpha=1)
        legend.get_frame().set_linewidth(0.0)
        ax.set_ylim(top=max(y_series) + 4)
        # Set x tick labels
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.set_xticklabels([date.strftime("%H:%M") for date in x_series])
        # Add bar values
        props = dict(facecolor=kwargs["grid_bg"], alpha=1, edgecolor='none')
        for i, v in enumerate(y_series):
            ax.text(i, v + 1, str(v), color=kwargs["text_color"],
                    fontweight='bold', ha='center', fontsize=12, alpha=1, bbox=props)
        # Export plot
        filepath = os.path.join(
            sys.path[0], self.website_folder, kwargs["filename"])
        figure.savefig(filepath, bbox_inches='tight', dpi=200,
                       facecolor=figure.get_facecolor(), edgecolor='none')


# Start
print("Parser started")

parser = ICalParser()
parser.download_ical_list()
parser.parse()
parser.export_json()
parser.export_mensa_chart()

# Finished
print("Finished")
