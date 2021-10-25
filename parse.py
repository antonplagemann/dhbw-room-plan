import csv
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta

from icalevents import icalevents, icaldownload
import requests

# Constants
DOWNLOAD_FOLDER = "ical"  # Folder name where to download all ical files
WEBSITE_FOLDER = "docs"  # Folder name where to save the json file
ICAL_URL = "http://vorlesungsplan.dhbw-mannheim.de/ical.php"
LAST_UPDATED = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
START_DATE = date.today()
END_DATE = date.today() + relativedelta(months=+3)
# Contains download links in the form of "<course>, <ical-link>"
LINKS_FILE = "links.txt"
OUTPUT_FILE = "rooms"    # The output file name (csv and json)

# Download ical list
response = requests.get("https://vorlesungsplan.dhbw-mannheim.de/ical.php")
# Parse HTML
results = re.findall(r'<option label="(.+?)" value="(\d+)">.+?</option>', response.text)

# Initialize data variables
downloads = []
events_by_date = {}
events_by_room = {}
rooms = set()

# Process each ical of the list
for i, item in enumerate(results):
    course_name, course_id = item
    print(f"{i+1} of {len(results)}: Processing '{course_name}' ({course_id}.ical)")
    # Download file
    try:
        events = icalevents.events(
            url=f"{ICAL_URL}?uid={course_id}", 
            start=START_DATE, end=END_DATE)
        print(f'\tFile {course_id}.ical sucessfully downloaded')
    except Exception as e:
        # Skip invalid ical or empty files
        print(e)
        print(f'\tFile {course_id}.ical couldn\'t be retrieved')
        continue

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
        # Get existing csv_data (events_by_date)
        d_date = events_by_date.get(date_string, {})
        d_room = d_date.get(event.location, [])
        # Save changes (events_by_date)
        d_room.append(events_string)
        d_date[event.location] = d_room
        events_by_date[date_string] = d_date
        # Get existing csv_data (events_by_room)
        r_room = events_by_room.get(event.location, {})
        r_date = r_room.get(date_string, [])
        # Save changes (events_by_room)
        r_date.append(events_string)
        r_room[date_string] = r_date
        events_by_room[event.location] = r_room
    # Processing finished
    print(f'\tFile {course_id}.ical sucessfully processed')

# Calculate and sort all rooms
rooms = sorted(set(events_by_room.keys()), reverse=True)

# Export as csv
csv_data = []
# Contruct titlerow
titlerow = ["Datum"] + rooms
csv_data.append(titlerow)
# Sort events_by_date ascending (needs to convert 'str -> datetime -> str' for sorting)
events_by_date_obj = [datetime.strptime(
    date_str, "%d.%m.%Y") for date_str in events_by_date.keys()]
events_by_date_str = [date_obj.strftime(
    "%d.%m.%Y") for date_obj in sorted(events_by_date_obj)]
# Go though each date and build csv row
for date in events_by_date_str:
    row = [date]
    for room in rooms:
        events_strings = events_by_date[date].get(room, [])
        events_string = " & ".join(events_strings)
        row.append(events_string)
    csv_data.append(row)
# Write to file
filepath = os.path.join(sys.path[0], OUTPUT_FILE + '.csv')
with open(filepath, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    writer.writerows(csv_data)

# Export also as json file
filepath = os.path.join(sys.path[0], WEBSITE_FOLDER, OUTPUT_FILE + '.json')
with open(filepath, 'w', encoding="utf8") as jsonfile:
    export_csv_data = {
        "last_updated": LAST_UPDATED,
        "events_by_date": events_by_date,
        "events_by_room": events_by_room
    }
    json.dump(export_csv_data, jsonfile, indent=4, sort_keys=True)

# Finished
print("Finished")
