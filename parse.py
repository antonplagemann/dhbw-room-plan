import csv
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta

import icalevents.icalevents
import requests

# Constants
DOWNLOAD_FOLDER = "ical"  # Folder name where to download all ical files
WEBSITE_FOLDER = "docs"  # Folder name where to save the json file
LAST_UPDATED = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
START_DATE = date.today()
END_DATE = date.today() + relativedelta(months=+3)
# Contains download links in the form of "<course>, <ical-link>"
LINKS_FILE = "links.txt"
OUTPUT_FILE = "rooms"    # The output file name (csv and json)

# Create folder
donwload_path = os.path.join(sys.path[0], DOWNLOAD_FOLDER)
if not os.path.exists(donwload_path):
    os.makedirs(donwload_path)

# Download all ical files
with open(os.path.join(sys.path[0], LINKS_FILE)) as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        course, url = line.split(",")
        # Get filename from url
        filename = re.findall(r"\w*\.ical", url)[0]
        print(f"{i+1} of {len(lines)}: Downloading {filename}")
        # Download file
        res = requests.get(url.strip(), stream=True)
        # Check if the image was retrieved successfully
        if res.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            res.raw.decode_content = True
            # Open a local file with wb (write binary) permission.
            with open(os.path.join(donwload_path, f"{course}.ical"), 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            print(
                f'\tFile {filename} sucessfully downloaded; saved as {course}.ical')
        else:
            print(f'\tFile {filename} couldn\'t be retrieved')


# Initialize csv_data variables
events_by_date = {}
events_by_room = {}
rooms = set()

# Parse every ical file and event
files = os.listdir(DOWNLOAD_FOLDER)
for i, ical in enumerate(files):
    print(f"{i+1} of {len(files)}: Processing ical {ical}...")
    filepath = os.path.join(DOWNLOAD_FOLDER, ical)
    try:
        # Parse ical file and load events
        events = icalevents.icalevents.events(
            file=filepath, start=START_DATE, end=END_DATE)
    except Exception as e:
        # Skip invalid ical or empty files
        print(e)
        continue
    # Get course name from filename
    course = ical.split(".")[0]
    # Process each event
    for event in events:
        if not event.location:
            # Skip events without location
            continue
        # Create event string
        event_start = event.start.strftime("%H:%M")
        event_end = event.end.strftime("%H:%M")
        events_string = f"{event_start}-{event_end}: {event.summary} ({course})"
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

# Calculate all rooms
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
