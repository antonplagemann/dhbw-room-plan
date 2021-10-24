new Vue({
  el: "#app",
  /**
   * Main function (called at loading time)
   */
  mounted() {
    fetch("rooms.json")
      .then(response => response.json())
      .then(data => {
        this.json = data;
        this.lastUpdated = new Date(data.last_updated).toLocaleDateString("de-DE", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });
      });
  },
  data: {
    // Temp
    room: "",
    json: null,
    lastUpdated: "",
    // Dates
    date: new Date(),
    minDate: new Date(),
  },
  computed: {
    maxDate() {
      return new Date(this.minDate.getFullYear(), this.minDate.getMonth() + 3, this.minDate.getDate());
    },
    dateString() {
      var dateObject = this.date || new Date()
      return dateObject.toLocaleDateString("de-DE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    },
    events() {
      if (!this.room) {return ["Kein Raum ausgewählt"]}
      try {
        const eventArray = this.json.events_by_date[this.dateString][this.room];
        return eventArray.sort();
      } catch (error) {
        return ["Keine Termine eingetragen"];
      }
    },
    messageTitle() {
      return "Raumtermine für den " + this.dateString
    },
    filteredRoomArray() {
      if (!this.json) {return []}
      return this.json.rooms.filter((option) => {
          return option
              .toString()
              .toLowerCase()
              .indexOf(this.room.toLowerCase()) >= 0
      })
    },
    eventListByRoom() {
      if (!this.json || !(this.room in this.json.events_by_room)) {return []}
      var eventsList = this.json.events_by_room[this.room]
      return Object.keys(eventsList).map((date) => {
        var parts = date.split('.');
        return new Date(parts[2],parts[1] - 1, parts[0]);
      })
    }
  },
  methods: {
    /**
     * Handle authentication failure
     *
     * @param {URLSearchParams} urlParams All parameters from the url
     */
    some_method(param) {
      // Some method here
    },
    
  },
});
