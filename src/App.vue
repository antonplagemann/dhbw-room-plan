<template>
  <div id="app">
    <b-navbar :transparent="true" type="is-dark">
      <template #brand>
        <b-navbar-item>
          <img
            src="./assets/dhbw_light.png"
            alt="DHBW-Mannheim"
            v-if="!isBrightMode"
          />
          <img
            src="./assets/dhbw_dark.png"
            alt="DHBW-Mannheim"
            v-if="isBrightMode"
          />
        </b-navbar-item>
      </template>
      <template #start>
        <b-navbar-item
          href="#"
          v-bind:class="{
            'has-text-black': isBrightMode,
            'has-text-white': !isBrightMode,
          }"
          @click="modalActive = true"
        >
          Mensaauslastung anzeigen
        </b-navbar-item>
        <b-navbar-item
          href="#"
          v-bind:class="{
            'has-text-black': isBrightMode,
            'has-text-white': !isBrightMode,
          }"
          @click="changeDisplayMode()"
        >
          {{ displayModeButtonText }}
        </b-navbar-item>
      </template>
    </b-navbar>
    <b-modal
      :active.sync="modalActive"
      :width="640"
      scroll="clip"
      style="padding-left: 20px; padding-right: 20px"
    >
      <div class="card">
        <div class="card-image">
          <figure class="image is-4by3">
            <img src="./assets/mensa_occupancy.png" alt="Image" />
          </figure>
        </div>
        <div class="card-content">
          <div class="content">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus
            nec iaculis mauris.
            <br />
            <small>{{ lastUpdated }}</small>
          </div>
        </div>
      </div>
    </b-modal>
    <section class="hero is-fullheight">
      <div class="hero-body" style="padding: 0px 0px 48px 0px">
        <div class="columns container is-fluid is-centered">
          <div
            class="column is-6"
            style="
              display: flex;
              flex-direction: column;
              max-height: calc(100vh - 80px);
              min-height: 450px;
            "
          >
            <!--Room picker-->
            <b-field
              label="Raum auswählen"
              v-bind:custom-class="{ 'has-text-white': !isBrightMode }"
              style="margin-bottom: 1cm"
            >
              <b-autocomplete
                rounded
                v-model="roomSelector"
                :data="filteredRoomArray"
                placeholder="z.B. Raum 048B"
                icon="magnify"
                clearable
                @select="onRoomChanged($event)"
              >
                <template #empty>Keine Ergebnisse gefunden</template>
              </b-autocomplete>
            </b-field>
            <!--Date picker-->
            <b-field
              label="Tag auswählen"
              v-bind:custom-class="{ 'has-text-white': !isBrightMode }"
              style="margin-bottom: 1cm"
            >
              <b-datepicker
                :mobile-native="false"
                v-model="date"
                placeholder="Bitte ein Datum eingeben oder auswählen..."
                :min-date="minDate"
                :max-date="maxDate"
                :events="datePickerRoomEvents"
                indicators="bars"
                icon="calendar-today"
                locale="de-DE"
                first-day-of-week="1"
                @input="onDateChanged()"
                append-to-body
              >
              </b-datepicker>
              <b-checkbox
                v-bind:class="{ 'has-text-white': !isBrightMode }"
                v-model="manualTime"
                style="margin-left: 20px"
              >
                Manuelle Zeiteingabe
              </b-checkbox>
            </b-field>
            <b-field
              v-if="manualTime"
              label="Zeit wählen"
              v-bind:custom-class="{ 'has-text-white': !isBrightMode }"
              style="margin-bottom: 1cm"
            >
              <b-clockpicker
                rounded
                v-model="time"
                placeholder="Bitte Zeit auswählen..."
                icon="clock"
                hour-format="24"
                @input="onTimeChanged()"
              >
              </b-clockpicker>
            </b-field>
            <!--Results display-->
            <b-message
              :closable="false"
              :title="messageTitle"
              has-icon
              type="is-primary"
              style="overflow-y: auto; min-height: 200px"
            >
              <b-message
                type="is-primary"
                v-for="item in results"
                id="eventsId"
                v-bind:key="item"
              >
                {{ item }}
              </b-message>
              <b-taglist attached style="margin-top: 25px !important">
                <b-tag type="is-dark"
                  ><a href="https://github.com/antonplagemann/dhbw-room-plan"
                    >Zuletzt aktualisiert:</a
                  ></b-tag
                >
                <b-tag
                  type="is-primary"
                  @dblclick.native="
                    isBrightMode = !isBrightMode;
                    changeDisplayMode();
                  "
                  >{{ lastUpdated }}</b-tag
                >
              </b-taglist>
            </b-message>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
// import HelloWorld from './components/HelloWorld.vue'
import json from './assets/rooms.json'

export default {
  name: 'App',
  components: {
    // HelloWorld
  },
  /**
   * Main function (called at loading time)
   */
  mounted () {
    this.lastUpdated = new Date(this.json.last_updated).toLocaleDateString(
      'de-DE',
      {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }
    )
    this.calculateEvents()
    this.calculateMessageTitle()
  },
  /**
   * Initializes the main data object
   * @returns The main data as object
   */
  data () {
    const minDate = new Date(new Date().setDate(new Date().getDate() - 1))
    const maxDate = new Date(
      minDate.getFullYear(),
      minDate.getMonth() + 3,
      minDate.getDate()
    )
    const dateString = new Date().toLocaleDateString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
    return {
      json: json, // JSON object with all data
      room: '', // Selected valid room
      roomSelector: '', // Direct input of the room selector
      datePickerRoomEvents: [], // List of dates for the datepicker view
      results: ['Daten werden geladen...'], // All results to display (array of strings)
      lastUpdated: '', // Update time of the JSON file
      minDate, // Minimum date to select in calendar view (today)
      maxDate, // Maximum date so select calendar view (today + 3 Months)
      date: new Date(), // Currently selected date
      dateString, // Currently selected date as dd.mm.yyyy
      messageTitle: 'Initialisierung', // Title of the results box
      time: new Date(new Date().setSeconds(0, 0)), // Currently selected time
      manualTime: false, // Value of the 'manual time' checkbox
      isBrightMode: false, // Switch for light mode
      modalActive: false // If mensa occupancy modal is open
    }
  },
  /**
   * Continuesly computed properties
   */
  computed: {
    /**
     * Filters all room for the room search input field depending on the user input
     * @returns An array of rooms
     */
    filteredRoomArray () {
      if (!this.json) {
        return []
      }
      return Object.keys(this.json.events_by_room).filter((option) => {
        return (
          option
            .toString()
            .toLowerCase()
            .indexOf(this.roomSelector.toLowerCase()) >= 0
        )
      })
    },
    displayModeButtonText () {
      if (this.isBrightMode) return 'Dunklen Modus aktivieren'
      return 'Hellen Modus aktivieren'
    }
  },
  methods: {
    changeDisplayMode () {
      this.isBrightMode = !this.isBrightMode
      if (!this.isBrightMode) {
        document
          .getElementsByTagName('body')[0]
          .setAttribute(
            'style',
            'background-image: url("./assets/background_dark.jpg");'
          )
      } else {
        document
          .getElementsByTagName('body')[0]
          .setAttribute(
            'style',
            'background-image: url("./assets/background_light.jpg");'
          )
      }
    },
    /**
     * Triggered on selected or cleared room.
     * @param {String} room
     */
    onRoomChanged (room) {
      this.room = room || ''
      // Update message title
      this.calculateMessageTitle()
      // Update datepicker view
      this.calculateRoomEventDates()
      // Update event list
      this.calculateEvents()
    },
    /**
     * Triggered on a selected date.
     */
    onDateChanged () {
      // Update date string
      this.calculateDateString()
      // Check and update time
      this.updateTime()
      // Update message title
      this.calculateMessageTitle()
      // Update event list
      this.calculateEvents()
    },
    /**
     * Triggered on a selected time.
     */
    onTimeChanged () {
      // Update message title
      this.calculateMessageTitle()
      // Update event list
      this.calculateEvents()
    },
    /**
     * Calculates a dd.mm.yyyy date string.
     */
    calculateDateString () {
      // Update date string
      this.dateString = this.date.toLocaleDateString('de-DE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    },
    /**
     * Updates the time value based on current date
     */
    updateTime () {
      // Do not update time if set to manual
      if (this.manualTime) return
      // Check if new date is current date
      const isCurrentDate =
        new Date().setHours(0, 0, 0, 0) ===
        new Date(this.date.valueOf()).setHours(0, 0, 0, 0)
      // If date set to today, set time to current time
      if (isCurrentDate) {
        this.time = new Date(new Date().setSeconds(0, 0))
        // If date is not equal to today, set time to 00:00
      } else {
        this.time.setHours(0, 0, 0, 0)
      }
    },
    /**
     * Calculates all events that happen in the selected room on the selected date
     * OR all free rooms on a selected date
     * @returns An array of events
     */
    calculateEvents () {
      if (!this.json) {
        this.results = ['Fehler: Termine konnten nicht geladen werden.']
      } else if (!this.room) {
        // Return all free rooms on selected date and time
        this.calculateFreeRooms()
      } else {
        // Return all events on selected date and room
        this.calculateEventsInRoom()
      }
    },
    /**
     * Calculates all free rooms on the selected date.
     */
    calculateFreeRooms () {
      // Calculate used rooms based on time
      const usedRooms = Object.keys(
        this.json.events_by_date[this.dateString]
      ).filter((room) => {
        if (
          this.json.events_by_room[room][this.dateString].every(
            (event) => new Date(event.end) > this.time
          )
        ) {
          return room
        }
      })
      // Calculate free rooms
      this.results = Object.keys(this.json.events_by_room).filter(
        (room) => !usedRooms.includes(room)
      )
    },
    /**
     * Calculates all events in a selected room on a selected date.
     */
    calculateEventsInRoom () {
      try {
        const events = this.json.events_by_date[this.dateString][this.room]
        if (!events) {
          this.results = ['Keine Termine eingetragen']
        } else {
          const eventsStr = events.map((event) => {
            const start = new Date(event.start).toLocaleTimeString('de-DE', {
              hour: '2-digit',
              minute: '2-digit'
            })
            const end = new Date(event.end).toLocaleTimeString('de-DE', {
              hour: '2-digit',
              minute: '2-digit'
            })
            return `${start}-${end} ${event.title} (${event.course})`
          })
          this.results = eventsStr
        }
      } catch (error) {
        this.results = ['Fehler:', error]
      }
    },
    /**
     * Calculates a date list of all events that happen in a specific room
     */
    calculateRoomEventDates () {
      if (!this.room) {
        this.datePickerRoomEvents = []
      } else {
        var eventsList = this.json.events_by_room[this.room]
        this.datePickerRoomEvents = Object.keys(eventsList).map((date) => {
          var parts = date.split('.')
          return new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]))
        })
      }
    },
    /**
     * Calculates the title for the results message box
     */
    calculateMessageTitle () {
      if (this.room) {
        this.messageTitle = 'Raumtermine für den ' + this.dateString
      } else {
        const timeStr = new Date(this.time).toLocaleTimeString('de-DE', {
          hour: '2-digit',
          minute: '2-digit'
        })
        if (timeStr !== '00:00') {
          this.messageTitle = `Freie Räume am ${this.dateString} ab ${timeStr}`
        } else this.messageTitle = 'Freie Räume am ' + this.dateString
      }
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
/*Set background image*/
body,
html {
  height: 100%;
  width: 100%;
  background-image: url("./assets/background_dark.jpg");
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow-y: auto;
  overflow-x: hidden;
  /* Hide scrollbar for IE, Edge and Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  scrollbar-width: none; /* Firefox */
}

/* Hide scrollbar for Chrome, Safari and Opera */
::-webkit-scrollbar {
  display: none;
}

/*Disable scrolling on hero*/
.hero.is-fullheight {
  min-height: calc(100vh - 50px);
}

/*Disable transparent modal background*/
.modal-background {
  position: unset;
}

/*Disable unwanted scrolling*/
.media-content {
  overflow-y: hidden !important;
}

/*Make message box smaller*/
#eventsId .message-body {
  padding-top: 5px !important;
  padding-bottom: 5px !important;
}

/*Make space between message boxes smaller*/
#eventsId {
  margin-bottom: 10px !important;
}
/*Make navbar transparent*/
nav.navbar.is-dark {
  background: transparent;
}
/*Make navbar menu transparent*/
.navbar-menu {
  margin-left: 7px;
  background-color: transparent;
  padding-bottom: 1rem;
}
/* No hover background for navbar items*/
a.navbar-item:hover {
  background-color: unset;
}
</style>
