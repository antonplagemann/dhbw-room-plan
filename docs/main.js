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
        this.minDate.getDate()
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
     * @returns An array of events
     */
    events() {
      if (!this.room) {
        return ["Kein Raum ausgewählt"];
      }
      try {
        return this.json.events_by_date[this.dateString][this.room];
      } catch (error) {
        return ["Keine Termine eingetragen"];
      }
    },
    /**
     * Calculates the title for the results message box
     * @returns A title string
     */
    messageTitle() {
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
