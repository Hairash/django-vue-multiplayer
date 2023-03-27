import { reactive, readonly } from 'vue';

const state = reactive({
  currentState: 'initial',
  states: {
    new: 'new',
    loggedIn: 'loggedIn',
    connected: 'connected',
  },
});

const setState = (newState) => {
  state.currentState = newState;
};

export default {
  state: readonly(state),
  setState,
};
