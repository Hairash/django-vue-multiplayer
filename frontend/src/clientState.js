import { reactive, computed } from 'vue';

const stateData = reactive({
  isLoggedIn: false,
  isConnected: false,
  isPlaying: false,
});

const states = {
  new: 'new',
  loggedIn: 'loggedIn',
  connected: 'connected',
  waiting: 'waiting',
  playing: 'playing',
}

const currentState = computed(() => {
  if (!stateData.isLoggedIn) {
    return states.new;
  } else if (!stateData.isConnected) {
    return states.loggedIn;
  } else if (!stateData.isWaiting) {
    return states.connected;
  } else if (!stateData.isPlaying) {
    return states.waiting;
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

function checkWaiting(serverState) {
  stateData.isWaiting = serverState === 'game';
}

function checkPlaying(participants, player) {
  stateData.isPlaying = participants.includes(player);
}

export default {
  stateData,
  states,
  currentState,
  checkLoggedIn,
  checkConnected,
  checkWaiting,
  checkPlaying,
};
