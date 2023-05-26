<template>
  <div>
    <AuthHeader />
    <h1>Game</h1>
    <p>Current state: {{ currentState }}</p>
    <button @click='connectToGame' :disabled='currentState !== states.loggedIn'>Connect</button>
    <button @click='startGame' :disabled='currentState !== states.connected'>Start</button>
    <button @click='play' :disabled='!isPlayEnabled()'>Play</button>
    <button @click='take' :disabled='!isTakeEnabled()'>Take</button>
    <button @click='pass' :disabled='!isPassEnabled()'>Pass</button>
    <br />
    <button @click='sendMove' :disabled='currentState !== states.playing'>Make a Move</button>
    <button @click='broadcast' :disabled='currentState !== states.playing'>To all</button>
    <button @click='sendNext' :disabled='currentState !== states.playing'>To the next</button>
    <button @click='endGame' :disabled='currentState !== states.playing'>End</button>
    <PlayersList :players=visitors />
  </div>
</template>

<script>
import PlayersList from './PlayersList.vue'
import AuthHeader from './AuthHeader.vue'
import clientState from '@/clientState';

export default {
  inject: ['clientState'],
  components: {
    PlayersList,
    AuthHeader,
  },
  data() {
    return {
      socket: null,
      visitors: [],
      // TODO: Make an enum
      serverState: 'wait',
      gameState: {},
      clientPlayer: null,
      // TODO: Refactor it - remove and use this.clientState
      currentState: clientState.currentState,
      states: clientState.states,
      stateData: clientState.stateData,
    };
  },
  mounted() {
    this.clientState.checkLoggedIn();
    this.clientPlayer = localStorage.getItem('user');
  },
  methods: {
    connectToGame() {
      console.log(this.socket);
      if (this.socket) return;
      this.socket = new WebSocket('ws://localhost:8000/ws/game/');
      this.clientState.checkConnected(this.socket);

      this.socket.addEventListener('open', (event) => {
        console.log('WebSocket connected:', event);
        const token = localStorage.getItem('token');
        this.socket.send(JSON.stringify({ action: 'authenticate', token: token }));
        console.log(token);
      });

      this.socket.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        if (data.action === 'game_state') {
          this.gameState = data;
        }
        else if (data.action === 'server_state') {
          this.visitors = data.visitors;
          this.serverState = data.state;
          this.clientState.checkPlaying(this.serverState);
        }
        else if (data.action === 'error') {
          alert(data.message);
        }
      });

      this.socket.addEventListener('close', (event) => {
        this.socket = null;
        this.clientState.checkConnected(this.socket);
        console.log('WebSocket closed:', event);
      });

      this.socket.addEventListener('error', (event) => {
        console.error('WebSocket error:', event);
      });
    },
    startGame() {
      this.socket.send(JSON.stringify({ action: 'start' }));
    },
    endGame() {
      this.socket.send(JSON.stringify({ action: 'end' }));
    },
    play() {
      this.socket.send(JSON.stringify({ action: 'play' }));
    },
    take() {
      this.socket.send(JSON.stringify({ action: 'take' }));
    },
    pass() {
      this.socket.send(JSON.stringify({ action: 'pass' }));
    },
    // TODO: Refactor - make one function
    isPlayEnabled() {
      return (
        this.currentState === this.states.playing && this.clientPlayer &&
        this.gameState.active_players.includes(this.clientPlayer) &&
        this.gameState.allowed_actions.includes('play')
      )
    },
    isTakeEnabled() {
      return (
        this.currentState === this.states.playing && this.clientPlayer &&
        this.gameState.active_players.includes(this.clientPlayer) &&
        this.gameState.allowed_actions.includes('take')
      )
    },
    isPassEnabled() {
      return (
        this.currentState === this.states.playing && this.clientPlayer &&
        this.gameState.active_players.includes(this.clientPlayer) &&
        this.gameState.allowed_actions.includes('pass')
      )
    },
    sendMove() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const moveData = {}; // TODO: Replace with your actual move data
        this.socket.send(JSON.stringify({ action: 'question', ...moveData }));
      } else {
        console.error('WebSocket is not open. readyState:', this.socket.readyState);
      }
    },
    broadcast() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ action: 'everybody' }));
      } else {
        console.error('WebSocket is not open. readyState:', this.socket.readyState);
      }
    },
    sendNext() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ action: 'next' }));
      } else {
        console.error('WebSocket is not open. readyState:', this.socket.readyState);
      }
    },
    // Add additional methods for handling game logic and making HTTP requests to the server
  },
};
</script>
