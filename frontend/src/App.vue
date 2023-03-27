<template>
  <div id="app">
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  components: {
  },
  data() {
    const STATES = {
      NEW: 'new',
      LOGEDIN: 'logedIn',
      CONNECTED: 'connected',
    };
    const state = STATES.NEW;
    return {
      STATES,
      state,
    }
  }
};
</script>

<style>
body {
  background-color: #141618;
  /* top: 0; */
  /* margin-top: 0; */
}

#app {
  background-color: #141618;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #5c6e80;
  margin-top: 60px;
}
</style>
