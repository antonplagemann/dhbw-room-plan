import csv
import json
import os
import re
import shutil
import sys
from datetime import date, datetime

import icalevents.icalevents
import requests

# Create folder
folder_path = os.path.join(sys.path[0], "ical")
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
# Download all ical files
with open(os.path.join(sys.path[0], "links.txt")) as f:
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

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(folder_path, f"{course}.ical"), 'wb') as f:
                shutil.copyfileobj(res.raw, f)

            print(f'\tFile {filename} sucessfully downloaded; saved as {course}.ical')
        else:
            print(f'\tFile {filename} couldn\'t be retrieved')

# Constants
FOLDER = os.path.join(sys.path[0], "ical")
START = date.today()
END = date(2021, 12, 24)

# Data
dates = {}
rooms = set()

# Code
files = os.listdir(FOLDER)
for i, ical in enumerate(files):
    print(f"{i+1} of {len(files)}: Processing ical {ical}...")
    filepath = os.path.join(FOLDER, ical)
    try:
        events = icalevents.icalevents.events(
            file=filepath, start=START, end=END)
    except Exception as e:
        print(e)
        continue
    course = ical.split(".")[0]
    for event in events:
        if not event.location:
            continue
        # Get german date string
        date_string = event.start.date().strftime("%d.%m.%Y")
        # Get existing data
        date = dates.get(date_string, {})
        room = date.get(event.location, [])
        event_start = event.start.strftime("%H:%M")
        event_end = event.end.strftime("%H:%M")
        events_string = f"{event_start}-{event_end}: {event.summary} ({course})"
        room.append(events_string)
        # Save changes
        date[event.location] = room
        dates[date_string] = date
        rooms.add(event.location)

# Export as csv
data = []
rooms = sorted(rooms, reverse=True)
# Contruct titlerow
titlerow = ["Datum"] + rooms
data.append(titlerow)
# Sort dates ascending (needs to convert 'str -> datetime -> str' for sorting)
dates_obj = [datetime.strptime(date_str, "%d.%m.%Y") for date_str in dates.keys()]
dates_str = [date_obj.strftime("%d.%m.%Y") for date_obj in sorted(dates_obj)]
# Go though each date and build data row
for date in dates_str:
    row = [date]
    for room in rooms:
        events_strings = dates[date].get(room, [])
        events_string = " & ".join(events_strings)
        row.append(events_string)
    data.append(row)
# Write to file
filepath = os.path.join(sys.path[0], 'rooms.csv')
with open(filepath, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    writer.writerows(data)
# Export also as json file
filepath = os.path.join(sys.path[0], 'rooms.json')
with open(filepath, 'w', encoding="utf8") as jsonfile:
    export_data = {"rooms": list(rooms), "dates": dates}
    json.dump(export_data, jsonfile, indent=4)
# Finished
print("Finished")
