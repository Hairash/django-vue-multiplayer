<template>
  <div id="app">
    <GameBoard />
  </div>
</template>

<script>
import GameBoard from "./components/GameBoard.vue";

export default {
  components: {
    GameBoard,
  },
};
</script>

<style>
#app {
  background-color: #141618;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
