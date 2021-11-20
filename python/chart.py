
import os
import sys
import json
import pandas
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt
import matplotlib
from typing import Dict
from statistics import mean
import numpy as np

# Use non-interactive backend (Qt5Agg else)
matplotlib.use('Agg')

class ChartGenerator:
    def __init__(self, events_by_date, target_path) -> None:
        self.events_by_date = events_by_date
        self.target_path = os.path.join(sys.path[0], target_path)
        self.mensa_occ = {}
        self.line_values = []
        self.options = {
            "theme": "dark_background",
            "figure_bg": "#282828",
            "grid_bg": "#282828",
            "grid_linewidth": 0.5,
            "bar_color": "#7957d5",
            "text_color": "#E39031",
            "3-Monate-Durchschnitt": "#7957d5",
            "3-Monate-Maximum": "#787878",
            "filename": "mensa_dark.png",
        }
    
    def __round_time(self, dt: datetime = None, dateDelta: timedelta = timedelta(minutes=15)) -> datetime:
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

    
    def __zerofill(self, course_values: Dict[datetime, int], delta: timedelta = timedelta(minutes=15), fill_date = datetime.today()):
        '''Fills a sorted date: value dict with zeros if there are gaps in the specified delta.'''
        min_date = fill_date.replace(hour=11, minute=0, second=0, microsecond=0)
        max_date = min_date.replace(hour=14)
        curr_date = min_date
        while curr_date <= max_date:
            if not course_values.get(curr_date, None):
                course_values[curr_date] = 0
            curr_date += delta
        return course_values

    
    def __calculate_mensa_occ(self, search_date):
        search_date_obj = datetime.strptime(search_date, "%d.%m.%Y")
        # Export lunch time schedule
        time_values = {}
        # Go though each event and count courses
        for room_events in self.events_by_date[search_date].values():
            for event in room_events:
                end = self.__round_time(datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%SZ"))
                if end.time() >= time(11) and end.time() < time(14):
                    for lunch_time in [end, end + timedelta(minutes=15), end + timedelta(minutes=30)]:
                        if lunch_time.hour >= 14:
                            continue
                        if time_values.get(lunch_time, None):
                            time_values[lunch_time] += 1
                        else:
                            time_values[lunch_time] = 1
        # Zerofill time_values dict
        time_values = self.__zerofill(time_values, fill_date=search_date_obj)
        # Convert datetime to time
        time_values = {lunch_time.time(): value for lunch_time, value in time_values.items()}
        # Build sorted time_values list
        time_values_list = sorted(list(time_values.items()), key=lambda e: e[0])
        return time_values_list

    
    def __calculate_chart_data(self):
        mensa_occ = {}
        # Calculate charts for the next week
        current = datetime.today()
        end = current + timedelta(days=14)
        # Go though each event and count courses
        while current <= end:
            # Skip weekends (mensa closed)
            if current.weekday() > 4:
                current += timedelta(days=1)
                continue
            event_date = current.strftime("%d.%m.%Y")
            time_values_list = self.__calculate_mensa_occ(event_date)

            # Skip days with 0 courses
            if any([v for _, v in time_values_list]):
                mensa_occ[event_date] = time_values_list

            current += timedelta(days=1)

        # Strip dates and put course counts together indexed by time
        hour_values = {hour[0][0]: [count for _, count in hour]
                    for hour in zip(*mensa_occ.values())}
        # Calculate mean of course counts
        hour_mean = {hour: mean(count) for hour, count in hour_values.items()}
        hour_max = {hour: max(count) for hour, count in hour_values.items()}

        # Save results
        self.mensa_occ = mensa_occ
        self.line_values = [('3-Monate-Durchschnitt', hour_mean), ('3-Monate-Maximum', hour_max)]

    
    def __create_figure(self, date_str):
        events = self.mensa_occ[date_str]
        # Join bar and line chart data
        chart_values = [entry + tuple(line[1][entry[0]]
                                    for line in self.line_values) for entry in events]
        # Create x and y series for bar chart
        y_series = [v for _, v in events]
        x_series = [k for k, _ in events]
        # Create pandas dataframe
        frame = pandas.DataFrame(chart_values, columns=[
                                "Uhrzeit", "Anzahl Kurse in Mittagspause",
                                *[line[0] for line in self.line_values]])
        frame.set_index("Uhrzeit")
        # Style plot
        plt.style.use('seaborn') # Base theme
        plt.style.use(self.options["theme"])
        figure, ax = plt.subplots()
        # Plot bar chart
        frame["Anzahl Kurse in Mittagspause"].plot(
            kind="bar", rot=0, color=self.options["bar_color"], use_index=False)
        # Plot line charts on top
        for description, _ in self.line_values:
            frame[description].plot(
                kind='line', color=self.options[description], ms=10, use_index=False)
        figure.suptitle(f'Mensaauslastung am {date_str}', fontsize=16)
        figure.set_facecolor(self.options["figure_bg"])
        ax.set_facecolor(self.options["grid_bg"])
        ax.get_figure().set_facecolor(self.options["grid_bg"])
        ax.set_ylabel("Anzahl Kurse", fontsize=16, fontweight='bold')
        ax.set_xlabel("Uhrzeit", fontsize=16, fontweight='bold')
        ax.yaxis.grid(True, which='major', linestyle='-',
                    linewidth=self.options["grid_linewidth"])
        ax.xaxis.grid(False)
        legend = ax.legend(fontsize="large", frameon=True,
                        facecolor=self.options["grid_bg"], framealpha=1)
        legend.get_frame().set_linewidth(0.0)
        # Set y ticks distance
        start, end = ax.get_ylim()
        ax.yaxis.set_ticks(np.arange(start, end, 5))

        # Set x tick labels
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.set_xticklabels([date.strftime("%H:%M") for date in x_series])
        # Add bar values
        props = dict(facecolor=self.options["grid_bg"], alpha=1, edgecolor='none')
        for i, v in enumerate(y_series):
            ax.text(i, v + 1, str(v), color=self.options["text_color"],
                    fontweight='bold', ha='center', fontsize=12, alpha=1, bbox=props, zorder=1)
        # Save figure
        day, month, year = date_str.split(".")
        filepath = os.path.join(self.target_path, f"mensa_occ_{year}-{month}-{day}.png")
        figure.savefig(filepath, bbox_inches='tight', dpi=200,
                    facecolor=figure.get_facecolor(), edgecolor='none')
        return figure

    def generate(self):
        # Create target path
        os.makedirs(self.target_path, exist_ok=True)
        print("Cleaning up chart files...")
        # Clean up old files
        for f in os.listdir(self.target_path):
            os.remove(os.path.join(self.target_path, f))
        print("Calculate chart data...")
        # Create chart data
        self.__calculate_chart_data()
        # Export plots
        i, count = 1, len(self.mensa_occ)
        for date_str in self.mensa_occ:
            print(f"Creating chart {i} of {count}...")
            figure = self.__create_figure(date_str)
            plt.close(figure)
            i += 1
        print("Chart generation finished!")

# Testing code
# filepath = os.path.join(sys.path[0], "..", "src", "assets", "rooms.json")
# target_path = os.path.join(sys.path[0], "..", "src", "assets", "mensa_charts")
# with open(filepath) as f:
#     data = json.load(f)
# chart = ChartGenerator(data["events_by_date"], target_path)
# chart.generate()
