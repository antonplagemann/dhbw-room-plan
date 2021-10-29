new Vue({
  el: "#app",
  /**
   * Main function (called at loading time)
   */
  mounted() {
    fetch("rooms.json")
      .then((response) => response.json())
      .then((data) => {
        this.json = data;
        this.lastUpdated = new Date(data.last_updated).toLocaleDateString(
          "de-DE",
          {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          }
        );
        this.calculateEvents();
        this.calculateMessageTitle();
      });
  },
  data() {
    const minDate = new Date(
      new Date().setDate(new Date().getDate() - 1)
    );
    const maxDate = new Date(
      minDate.getFullYear(),
      minDate.getMonth() + 3,
      minDate.getDate()
    );
    const dateString = new Date().toLocaleDateString("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
    return {
      json: null, // JSON object with all data
      room: "", // Selected valid room
      roomSelector: "", // Direct input of the room selector
      datePickerRoomEvents: [], // List of dates for the datepicker view
      results: ["Daten werden geladen..."],
      lastUpdated: "", // Update time of the JSON file
      // Dates
      minDate, // Minimum date to select (today)
      maxDate, // Maximum date so select (today + 3 Months)
      date: new Date(), // Selected date
      dateString,
      messageTitle: "Initialisierung",
      time: new Date(new Date().setSeconds(0, 0)), // Current time
      manualTime: false,
    };
  },
  computed: {
    /**
     * Filters all room for the room search input field depending on the user input
     * @returns An array of rooms
     */
    filteredRoomArray() {
      if (!this.json) {
        return [];
      }
      return Object.keys(this.json.events_by_room).filter((option) => {
        return (
          option
            .toString()
            .toLowerCase()
            .indexOf(this.roomSelector.toLowerCase()) >= 0
        );
      });
    },
  },
  methods: {
    onRoomChanged(room) {
      this.room = room || "";
      // Update message title
      this.calculateMessageTitle();
      // Update datepicker view
      this.calculateRoomEventDates();
      // Update event list
      this.calculateEvents();
    },
    onDateChanged(date) {
      // Update date string
      this.updateDateString(date);
      // Check and update time
      this.updateTime(date);
      // Update message title
      this.calculateMessageTitle();
      // Update event list
      this.calculateEvents();
    },
    onTimeChanged(date) {
      // Update message title
      this.calculateMessageTitle();
      // Update event list
      this.calculateEvents();
    },
    updateDateString(date) {
      // Update date string
      this.dateString = date.toLocaleDateString("de-DE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    },
    updateTime(date) {
      // Check if new date is current date
      const isCurrentDate =
        new Date().setHours(0, 0, 0, 0) ===
        new Date(date.valueOf()).setHours(0, 0, 0, 0);
      // Do not update time if set to manual
      if (this.manualTime) return;
      // If date set to today, set time to current time
      else if (isCurrentDate) {
        this.time = new Date(new Date().setSeconds(0, 0));
        // If date is not equal to today, set time to 00:00
      } else {
        this.time.setHours(0, 0, 0, 0);
      }
    },
    /**
     * Calculates all events that happen in the selected room on the selected date
     * OR all free rooms on a selected date
     * @returns An array of events
     */
    calculateEvents() {
      if (!this.json) {
        this.results = ["Fehler: Termine konnten nicht geladen werden."];
      } else if (!this.room) {
        // Return all free rooms on selected date and time
        this.calculateFreeRooms();
      } else {
        // Return all events on selected date and room
        this.calculateEventsInRoom();
      }
    },
    calculateFreeRooms() {
      // Calculate used rooms based on time
      const usedRooms = Object.keys(
        this.json.events_by_date[this.dateString]
      ).filter((room) => {
        if (
          this.json.events_by_room[room][this.dateString].every(
            (event) => new Date(event.end) > this.time
          )
        )
          return room;
      });
      // Calculate free rooms
      this.results = Object.keys(this.json.events_by_room).filter(
        (room) => !usedRooms.includes(room)
      );
    },
    calculateEventsInRoom() {
      try {
        const events =
          this.json.events_by_date[this.dateString][this.room];
        if (!events) {
          this.results = ["Keine Termine eingetragen"];
        } else {
          const eventsStr = events.map((event) => {
            const start = new Date(event.start).toLocaleTimeString(
              "de-DE",
              {
                hour: "2-digit",
                minute: "2-digit",
              }
            );
            const end = new Date(event.end).toLocaleTimeString("de-DE", {
              hour: "2-digit",
              minute: "2-digit",
            });
            return `${start}-${end} ${event.title} (${event.course})`;
          });
          this.results = eventsStr;
        }
      } catch (error) {
        this.results = ["Fehler:", error];
      }
    },
    /**
     * Calculates a date list of all events that happen in a specific room
     */
    calculateRoomEventDates() {
      if (!this.room) {
        this.datePickerRoomEvents = [];
      } else {
        var eventsList = this.json.events_by_room[this.room];
        this.datePickerRoomEvents = Object.keys(eventsList).map(
          (date) => {
            var parts = date.split(".");
            return new Date(parts[2], parts[1] - 1, parts[0]);
          }
        );
      }
    },
    /**
     * Calculates the title for the results message box
     */
    calculateMessageTitle() {
      if (this.room)
        this.messageTitle = "Raumtermine für den " + this.dateString;
      else {
        const timeStr = new Date(this.time).toLocaleTimeString("de-DE", {
          hour: "2-digit",
          minute: "2-digit",
        });
        if (timeStr !== "00:00")
          this.messageTitle = `Freie Räume am ${this.dateString} ab ${timeStr}`;
        else this.messageTitle = "Freie Räume am " + this.dateString;
      }
    },
  },
});
