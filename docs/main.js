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
  /**
   * Initializes the main data object
   * @returns The main data as object
   */
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
      results: ["Daten werden geladen..."], // All results to display (array of strings)
      lastUpdated: "", // Update time of the JSON file
      minDate, // Minimum date to select in calendar view (today)
      maxDate, // Maximum date so select calendar view (today + 3 Months)
      date: new Date(), // Currently selected date
      dateString, // Currently selected date as dd.mm.yyyy
      messageTitle: "Initialisierung", // Title of the results box
      time: new Date(new Date().setSeconds(0, 0)), // Currently selected time
      manualTime: false, // Value of the 'manual time' checkbox
      isBrightMode: false, // Switch for light mode
      modalActive: false, // If mensa occupancy modal is open
    };
  },
  /**
   * Continuesly computed properties
   */
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
    displayModeButtonText() {
      if (this.isBrightMode) return "Dunklen Modus aktivieren";
      return "Hellen Modus aktivieren";
    },
  },
  methods: {
    changeDisplayMode() {
      this.isBrightMode = !this.isBrightMode;
      if (!this.isBrightMode)
        document
          .getElementsByTagName("body")[0]
          .setAttribute(
            "style",
            'background-image: url("background_dark.jpg");'
          );
      else
        document
          .getElementsByTagName("body")[0]
          .setAttribute(
            "style",
            'background-image: url("background_light.jpg");'
          );
    },
    /**
     * Triggered on selected or cleared room.
     * @param {String} room
     */
    onRoomChanged(room) {
      this.room = room || "";
      // Update message title
      this.calculateMessageTitle();
      // Update datepicker view
      this.calculateRoomEventDates();
      // Update event list
      this.calculateEvents();
    },
    /**
     * Triggered on a selected date.
     */
    onDateChanged() {
      // Update date string
      this.calculateDateString();
      // Check and update time
      this.updateTime();
      // Update message title
      this.calculateMessageTitle();
      // Update event list
      this.calculateEvents();
    },
    /**
     * Triggered on a selected time.
     */
    onTimeChanged() {
      // Update message title
      this.calculateMessageTitle();
      // Update event list
      this.calculateEvents();
    },
    /**
     * Calculates a dd.mm.yyyy date string.
     */
    calculateDateString() {
      // Update date string
      this.dateString = this.date.toLocaleDateString("de-DE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    },
    /**
     * Updates the time value based on current date
     */
    updateTime() {
      // Do not update time if set to manual
      if (this.manualTime) return;
      // Check if new date is current date
      const isCurrentDate =
        new Date().setHours(0, 0, 0, 0) ===
        new Date(this.date.valueOf()).setHours(0, 0, 0, 0);
      // If date set to today, set time to current time
      if (isCurrentDate) {
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
    /**
     * Calculates all free rooms on the selected date.
     */
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
    /**
     * Calculates all events in a selected room on a selected date.
     */
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
