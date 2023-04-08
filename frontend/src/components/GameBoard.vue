<template>
  <div>
    <AuthHeader />
    <h1>Game</h1>
    <p>Current state: {{ currentState }}</p>
    <button @click="connectToGame" :disabled="currentState !== states.loggedIn">Connect</button>
    <button @click="sendMove" :disabled="currentState !== states.connected">Make a Move</button>
    <button @click="broadcast" :disabled="currentState !== states.connected">To all</button>
    <button @click="sendNext" :disabled="currentState !== states.connected">To the next</button>
    <PlayersList :players=players />
  </div>
</template>

<script>
import PlayersList from './PlayersList.vue'
import AuthHeader from './AuthHeader.vue'
import gameState from '@/gameState';

export default {
  inject: ['gameState'],
  components: {
    PlayersList,
    AuthHeader,
  },
  data() {
    return {
      socket: null,
      players: [],
      currentState: gameState.currentState,
      states: gameState.states,
      stateData: gameState.stateData,
    };
  },
  mounted() {
    this.gameState.checkLoggedIn();
  },
  methods: {
    connectToGame() {
      console.log(this.socket);
      if (this.socket) return;
      this.socket = new WebSocket("ws://localhost:8000/ws/game/");
      this.gameState.checkConnected(this.socket);

      this.socket.addEventListener("open", (event) => {
        console.log("WebSocket connected:", event);
        const token = localStorage.getItem('token');
        this.socket.send(JSON.stringify({ action: "authenticate", token: token }));
        console.log(token);
      });

      this.socket.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        if (data.action === "list") {
          this.players = data.players;
        }
        if (data.action === "error") {
          alert(data.message);
        }
      });

      this.socket.addEventListener("close", (event) => {
        this.socket = null;
        this.gameState.checkConnected(this.socket);
        console.log("WebSocket closed:", event);
      });

      this.socket.addEventListener("error", (event) => {
        console.error("WebSocket error:", event);
      });
    },
    sendMove() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const moveData = {}; // Replace with your actual move data
        this.socket.send(JSON.stringify({ action: "question", ...moveData }));
      } else {
        console.error("WebSocket is not open. readyState:", this.socket.readyState);
      }
    },
    broadcast() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ action: "everybody" }));
      } else {
        console.error("WebSocket is not open. readyState:", this.socket.readyState);
      }
    },
    sendNext() {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ action: "next" }));
      } else {
        console.error("WebSocket is not open. readyState:", this.socket.readyState);
      }
    },
    // Add additional methods for handling game logic and making HTTP requests to the server
  },
};
</script>
