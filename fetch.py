import requests
import re
import os, sys

LINKS_FILE = "newlinks.txt"

response = requests.get("https://vorlesungsplan.dhbw-mannheim.de/ical.php")

results = re.findall(r'<option label="(.+?)" value="(\d+)">.+?</option>', response.text)

with open(os.path.join(sys.path[0], LINKS_FILE), "w") as f:
    for course_name, course_id in results:
        f.write(f"{course_name}, http://vorlesungsplan.dhbw-mannheim.de/ical.php?uid=, {course_id}\n")
