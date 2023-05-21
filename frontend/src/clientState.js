import { reactive, computed } from 'vue';

const stateData = reactive({
  isLoggedIn: false,
  isConnected: false,
  isPlaying: false,
});

// TODO: Add wait state - if you connected, but the game has been already started
const states = {
  new: 'new',
  loggedIn: 'loggedIn',
  connected: 'connected',
  playing: 'playing',
}

const currentState = computed(() => {
  if (!stateData.isLoggedIn) {
    return states.new;
  } else if (!stateData.isConnected) {
    return states.loggedIn;
  } else if (!stateData.isPlaying) {
    return states.connected;
  } else {
    return states.playing;
  }
});

function checkLoggedIn() {
  stateData.isLoggedIn = !!localStorage.getItem('token');
}

function checkConnected(socket) {
  stateData.isConnected = !!socket;
}

function checkPlaying(serverState) {
  stateData.isPlaying = serverState === 'game';
}

export default {
  stateData,
  states,
  currentState,
  checkLoggedIn,
  checkConnected,
  checkPlaying,
};
