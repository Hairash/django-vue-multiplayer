import { reactive, computed } from 'vue';

const stateData = reactive({
  isLoggedIn: false,
  isConnected: false,
});

const states = {
  new: 'new',
  loggedIn: 'loggedIn',
  connected: 'connected',
}

const currentState = computed(() => {
  if (!stateData.isLoggedIn) {
    return states.new;
  } else if (!stateData.isConnected) {
    return states.loggedIn;
  } else {
    return states.connected;
  }
});

function checkLoggedIn() {
  stateData.isLoggedIn = !!localStorage.getItem('token');
}

function checkConnected(socket) {
  stateData.isConnected = !!socket;
}

export default {
  stateData,
  states,
  currentState,
  checkLoggedIn,
  checkConnected,
};
