<template>
  <div
    id="app"
    class="dark-bg"
  >
    <b-navbar
      :transparent="true"
      type="is-dark"
      tag="a"
    >
      <template #brand>
        <b-navbar-item>
          <img
            src="./assets/dhbw_light.png"
            alt="DHBW-Mannheim"
          >
        </b-navbar-item>
      </template>
      <template #end>
        <b-navbar-item tag="div">
          <div class="buttons">
            <a
              class="button is-primary"
              @click="modalActive = true"
            >
              Mensaauslastung anzeigen
            </a>
          </div>
        </b-navbar-item>
      </template>
    </b-navbar>
    <!--Mensa occupancy modal-->
    <b-modal
      :active.sync="modalActive"
      :width="640"
      scroll="clip"
      style="padding-left: 20px; padding-right: 20px"
    >
      <div
        class="card has-text-primary-light has-background-dark"
      >
        <div class="card-image">
          <figure class="image is-4by3">
            <img
              src="./assets/mensa_dark.png"
              alt="Image"
            >
          </figure>
        </div>
        <div class="card-content">
          <div class="content">
            Das Diagramm zeigt die potenzielle Anzahl an Kursen in der Mensa am {{ lastUpdated.split(",")[0] }}.<br>
            Mensa-Öffungszeiten: Mo-Fr von 11:30-14:00<br>
            Für Details zur Berechnung siehe
            <a href="https://github.com/antonplagemann/dhbw-room-plan">Readme auf GitHub</a>.<br>
            <small>
              Diagramm erstellt am {{ lastUpdated }} <br> 
            </small>
          </div>
        </div>
      </div>
    </b-modal>
    <section class="hero is-fullheight">
      <div
        class="hero-body"
        style="padding: 0px 0px 48px 0px"
      >
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
            <b-tooltip
              position="is-top"
              :active="tooltipActive"
              :always="tooltipVisible"
              animated
              :delay="1000"
            >
              <template v-slot:content>
                <span>Neu: Tagesaktueller Mensa-Auslastungsplan ⟶</span>
              </template>
              <b-field
                label="Raum auswählen"
                custom-class="has-text-white"
                type="is-dark"
                style="margin-bottom: 1cm"
              >
                <b-autocomplete
                  v-model="roomSelector"
                  rounded
                  custom-class="has-text-white has-background-dark"
                  :data="filteredRoomArray"
                  placeholder="z.B. Raum 048B"
                  icon="magnify"
                  clearable
                  @select="onRoomChanged($event)"
                >
                  <template #empty>
                    Keine Ergebnisse gefunden
                  </template>
                </b-autocomplete>
              </b-field>
            </b-tooltip>
            <!--Date picker-->
            <b-field
              label="Tag auswählen"
              custom-class="has-text-white"
              type="is-dark"
              style="margin-bottom: 1cm"
            >
              <b-datepicker
                v-model="date"
                custom-class="has-text-white has-background-dark is-dark"
                :mobile-native="false"
                placeholder="Bitte ein Datum eingeben oder auswählen..."
                :min-date="minDate"
                :max-date="maxDate"
                :events="datePickerRoomEvents"
                indicators="bars"
                icon="calendar-today"
                locale="de-DE"
                :first-day-of-week="1"
                append-to-body
                @input="onDateChanged()"
              />
              <b-checkbox
                v-model="manualTime"
                class="has-text-white"
                style="margin-left: 20px"
              >
                Manuelle Zeiteingabe
              </b-checkbox>
            </b-field>
            <b-field
              v-if="manualTime"
              label="Zeit wählen"
              custom-class="has-text-white"
              style="margin-bottom: 1cm"
            >
              <b-clockpicker
                v-model="time"
                custom-class="has-text-white is-dark has-background-dark"
                rounded
                placeholder="Bitte Zeit auswählen..."
                icon="clock"
                hour-format="24"
                @input="onTimeChanged()"
              />
            </b-field>
            <!--Results display-->
            <b-message
              :closable="false"
              :title="messageTitle"
              has-icon
              type="is-primary has-background-dark"
              style="overflow-y: auto; min-height: 200px"
            >
              <b-message
                v-for="item in results"
                id="eventsId"
                :key="item"
                type="has-background-dark"
              >
                {{ item }}
              </b-message>
              <b-taglist
                attached
                style="margin-top: 25px !important"
              >
                <b-tag type="is-primary">
                  <a href="https://github.com/antonplagemann/dhbw-room-plan">
                    Zuletzt aktualisiert:
                  </a>
                </b-tag>
                <b-tag
                  type="is-info is-dark"
                >
                  {{ lastUpdated }}
                </b-tag>
              </b-taglist>
            </b-message>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import json from './assets/rooms.json'

export default {
  name: 'App',
  components: {
    // HelloWorld
  },
  /**
   * Initializes the main data object
   * @returns The main data as object
   */
  data() {
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
      modalActive: false, // If mensa occupancy modal is open
      tooltipActive: true,  // If the new features tooltip is active
      tooltipVisible: true  // If the new features tooltip is visible
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
    filteredRoomArray() {
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
    }
  },
  /**
   * Main function (called at loading time)
   */
  mounted() {
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
    // Diable tooltip after 5 seconds
    setTimeout(() => {
      this.tooltipVisible = false
      this.tooltipActive = false
    }, 5000)
  },
  methods: {
    /**
     * Triggered on selected or cleared room.
     * @param {String} room
     */
    onRoomChanged(room) {
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
    onDateChanged() {
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
    onTimeChanged() {
      // Update message title
      this.calculateMessageTitle()
      // Update event list
      this.calculateEvents()
    },
    /**
     * Calculates a dd.mm.yyyy date string.
     */
    calculateDateString() {
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
    updateTime() {
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
    calculateEvents() {
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
    calculateFreeRooms() {
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
    calculateEventsInRoom() {
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
    calculateRoomEventDates() {
      if (!this.room) {
        this.datePickerRoomEvents = []
      } else {
        var eventsList = this.json.events_by_room[this.room]
        this.datePickerRoomEvents = Object.keys(eventsList).map((date) => {
          var parts = date.split('.')
          return new Date(
            Number(parts[2]),
            Number(parts[1]) - 1,
            Number(parts[0])
          )
        })
      }
    },
    /**
     * Calculates the title for the results message box
     */
    calculateMessageTitle() {
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
::placeholder {
  color: #707070 !important;
}
.dropdown-content {
  background-color: #363636 !important;
  color: #fff !important;
}
.dropdown-item {
  color: #fff !important;
}
a.dropdown-item:hover {
  background-color: #485fc7 !important;
}
.datepicker-cell.is-selectable {
  color: #fff !important;
}
.datepicker-cell.is-unselectable {
  color: #818181 !important;
}
.pagination-next, .pagination-previous {
  border-color: #6f6f6f !important
}
select, option {
  background-color: #363636 !important;
  color: #fff !important;
  border-color: #6f6f6f !important
}
.textarea {
    color: #fff !important;
}
.card {
  background-color: #363636 !important;
  color: #fff !important;
}
.b-clockpicker-body .b-clockpicker-face {
  background-color: #4a4a4a !important;
}
.message.is-primary .message-body {
  color: #fff !important;
}

/*Center Buttons */
.buttons {
  text-align: center;
  display: block !important;
}

/* Dark mode */
.dark-bg {
  
  background-color: rgb(61, 73, 108);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
}
/*Set no scrolling*/
body,
html {
  height: 100%;
  width: 100%;
  background-color: rgb(61, 73, 108);
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
  min-height: calc(100vh - 52px) !important;
  display: block !important; /*Fix content on top*/
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
  /*margin-bottom: 10px;*/
}

/*Make navbar menu transparent*/
.navbar-menu {
  margin-left: 7px;
  background-color: transparent !important;
  text-align: center;
}

/* No hover background for navbar items*/
a.navbar-item:hover {
  background-color: unset !important;
}
</style>
