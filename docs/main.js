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
      });
  },
  data: {
    room: "", // Selected room
    json: null, // JSON object with all data
    lastUpdated: "", // Update time of the JSON file
    // Dates
    date: new Date(), // Selected date
    minDate: new Date(), // Minimum date to select (today)
  },
  computed: {
    /**
     * Calculates "today + 3 months" as date object
     * @returns The maximum date that can be selected
     */
    maxDate() {
      return new Date(
        this.minDate.getFullYear(),
        this.minDate.getMonth() + 3,
        this.minDate.getDate() - 1
      );
    },
    /**
     * Calculates a german date string (dd.mm.yyyy) from the selected date
     * @returns The selected date as string
     */
    dateString() {
      var dateObject = this.date || new Date();
      return dateObject.toLocaleDateString("de-DE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    },
    /**
     * Calculates all events that happen in the selected room on the selected date
     * OR all free rooms on a selected date
     * @returns An array of events
     */
    events() {
      if (!this.json) {
        return ["Termine werden geladen..."];
      }
      // Return all free rooms on selected date
      if (!this.validRoom) {
        const usedRooms = Object.keys(this.json.events_by_date[this.dateString])
        const freeRooms = Object.keys(this.json.events_by_room).filter(r => !usedRooms.includes(r))
        return freeRooms.reverse();
      }
      // Return all events on selected date and room
      try {
        const events = this.json.events_by_date[this.dateString][this.room];
        if (!events) {return ["Keine Termine eingetragen"];}
        const eventsStr = events.map(event => {
          const start = new Date(event.start).toLocaleTimeString(
            "de-DE",
            {
              hour: "2-digit",
              minute: "2-digit",
            }
          );
          const end = new Date(event.end).toLocaleTimeString(
            "de-DE",
            {
              hour: "2-digit",
              minute: "2-digit",
            }
          );
          return `${start}-${end} ${event.title} (${event.course})`
        });
        return eventsStr;
      } catch (error) {
        return ["Fehler:", error];
      }
    },
    /**
     * Checks if the currently entered room is valid
     * @returns True if the current room is a valid room
     */
    validRoom() {
      if (!this.json) {
        return false;
      }
      return Object.keys(this.json.events_by_room).includes(this.room)
    },
    /**
     * Calculates the title for the results message box
     * @returns A title string
     */
    messageTitle() {
      if (!this.validRoom) {
        return "Freie Räume am " + this.dateString;
      }
      return "Raumtermine für den " + this.dateString;
    },
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
            .indexOf(this.room.toLowerCase()) >= 0
        );
      });
    },
    /**
     * Returns a date list of all events that happen in a specific room
     * @returns A list of dates
     */
    eventListByRoom() {
      if (!this.json || !(this.room in this.json.events_by_room)) {
        return [];
      }
      var eventsList = this.json.events_by_room[this.room];
      return Object.keys(eventsList).map((date) => {
        var parts = date.split(".");
        return new Date(parts[2], parts[1] - 1, parts[0]);
      });
    },
  },
});
