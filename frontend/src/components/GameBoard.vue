<template>
  <div>
    <AuthHeader />
    <h1>Game</h1>
    <p>Current state: {{ currentState }}</p>
    <button @click='connectToGame' :disabled='currentState !== states.loggedIn'>Connect</button>
    <button @click='startGame' :disabled='currentState !== states.connected'>Start</button>
    <br />
    <button @click='take' :disabled='!isTakeEnabled()'>Take</button>
    <button @click='pass' :disabled='!isPassEnabled()'>Pass</button>
    <br />
    Cards
    <button v-for='card in cards'
      :key='card.rank + card.suit'
      @click='play(card)'
      :disabled='!isPlayEnabled()'>
      {{ card.rank }}{{ card.suit }}
    </button>
    <br />
    Table
    <label v-for='card in gameState.table' :key='card.rank + card.suit'>
      {{ card.rank }}{{ card.suit }}
    </label>
    <br />
    <button @click='endGame' :disabled='currentState !== states.playing'>End</button>
    <PlayersList header='Connected players' :players=visitors />
    <PlayersList header='Active players' :players=participants />
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
      participants: [],
      // TODO: Refactoring. Make an enum
      serverState: 'wait',
      clientPlayer: null,
      // TODO: Refactoring. Remove and use this.clientState
      currentState: clientState.currentState,
      states: clientState.states,
      stateData: clientState.stateData,

      gameState: {},
      cards: [],
    };
  },
  mounted() {
    this.clientState.checkLoggedIn();
    this.clientPlayer = localStorage.getItem('user');
  },
  methods: {
    connectToGame() {
      if (this.socket) return;
      this.socket = new WebSocket('ws://localhost:8000/ws/game/');
      this.clientState.checkConnected(this.socket);

      this.socket.addEventListener('open', (event) => {
        console.log('WebSocket connected:', event);
        const token = localStorage.getItem('token');
        this.socket.send(JSON.stringify({ action: 'authenticate', token: token }));
      });

      this.socket.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        if (data.action === 'hand') {
          this.cards = data.cards;
        }
        if (data.action === 'game_state') {
          this.gameState = data;
        }
        else if (data.action === 'server_state') {
          this.visitors = data.visitors;
          this.participants = data.participants;
          this.serverState = data.state;
          this.clientState.checkWaiting(this.serverState);
          this.clientState.checkPlaying(this.participants, this.clientPlayer);
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
      if (window.confirm("Are you sure you want to end the game?")) {
        this.socket.send(JSON.stringify({ action: 'end' }));
      }
    },
    play(card) {
      this.socket.send(JSON.stringify({ action: 'play', card: card, player: this.clientPlayer }));
    },
    take() {
      this.socket.send(JSON.stringify({ action: 'take' }));
    },
    pass() {
      this.socket.send(JSON.stringify({ action: 'pass' }));
    },
    // TODO: Refactoring. Make one function
    isPlayEnabled() {
      return (
        this.currentState === this.states.playing && this.clientPlayer &&
        Object.keys(this.gameState).length &&
        this.gameState.active_players.includes(this.clientPlayer) &&
        this.gameState.allowed_actions.includes('play')
      )
    },
    isTakeEnabled() {
      return (
        this.currentState === this.states.playing && this.clientPlayer &&
        Object.keys(this.gameState).length &&
        this.gameState.active_players.includes(this.clientPlayer) &&
        this.gameState.allowed_actions.includes('take')
      )
    },
    isPassEnabled() {
      return (
        this.currentState === this.states.playing && this.clientPlayer &&
        Object.keys(this.gameState).length &&
        this.gameState.active_players.includes(this.clientPlayer) &&
        this.gameState.allowed_actions.includes('pass')
      )
    },
  },
};
</script>
