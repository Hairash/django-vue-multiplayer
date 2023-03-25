<template>
  <div>
    <h1>Game</h1>
    <button @click="connectToGame">Connect</button>
    <button @click="sendMove">Make a Move</button>
    <!-- Add your game elements here -->
  </div>
</template>

<script>
// import axios from "axios";

export default {
  data() {
    return {
      socket: null,
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
        if (data.action === "update") {
          this.gameState = data.game_state;
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
        this.socket.send(JSON.stringify({ action: "move", ...moveData }));
      } else {
        console.error("WebSocket is not open. readyState:", this.socket.readyState);
      }
    },
    // Add additional methods for handling game logic and making HTTP requests to the server
  },
};
</script>
