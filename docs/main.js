new Vue({
  el: "#app",
  /**
   * Main function (called at loading time)
   */
  mounted() {
    fetch("rooms.json")
      .then(response => response.json())
      .then(data => this.json = data);
  },
  data: {
    // Temp
    room: "",
    json: {},
    // Dates
    date: new Date(),
    minDate: new Date(),
  },
  computed: {
    maxDate() {
      return new Date(this.minDate.getFullYear(), this.minDate.getMonth() + 3, this.minDate.getDate());
    },
    dateString() {
      return this.date.toLocaleDateString("de-DE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    },
    events() {
      if (!this.room) {return "Kein Raum ausgewählt"}
      try {
        const eventArray = this.json.events_by_date[this.dateString][this.room];
        return eventArray.sort().join("\n");
      } catch (error) {
        console.log(error);
        return "Keine Termine eingetragen";
      }
    },
    messageTitle() {
      return "Raumtermine für den " + this.dateString
    },
    filteredRoomArray() {
      if (!this.json.rooms) {return []}
      return this.json.rooms.filter((option) => {
          return option
              .toString()
              .toLowerCase()
              .indexOf(this.room.toLowerCase()) >= 0
      })
    },
    eventListByRoom() {
      if (!this.room) {return []}
      var eventsList = this.json.events_by_room[this.room]
      if (!eventsList) {return []}
      var res =  Object.keys(eventsList).map((date) => {
        var parts = date.split('.');
        return new Date(parts[2],parts[1] - 1, parts[0]);
      })
      console.log("list:", res);
      return res;
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
