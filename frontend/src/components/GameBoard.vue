<template>
  <div>
    <h1>Game</h1>
    <button @click="connectToGame">Connect</button>
    <button @click="sendMove">Make a Move</button>
    <button @click="broadcast">To all</button>
    <button @click="sendNext">To the next</button>
    <PlayersList :players=players />
    <!-- Add your game elements here -->
  </div>
</template>

<script>
import PlayersList from './PlayersList.vue'

export default {
  components: {
    PlayersList,
  },
  data() {
    return {
      socket: null,
      players: [],
      gameState: {},
    };
  },
  methods: {
    connectToGame() {
      this.socket = new WebSocket("ws://localhost:8000/ws/game/");

      this.socket.addEventListener("open", (event) => {
        console.log("WebSocket connected:", event);
      });

      this.socket.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        if (data.action === "list") {
          this.players = data.players;
        }
      });

      this.socket.addEventListener("close", (event) => {
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
