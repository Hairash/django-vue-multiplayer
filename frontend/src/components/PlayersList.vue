<template>
  <div>
    <h3>Connected Players:</h3>
    <ul>
      <li v-for="player in players" :key="player">{{ player }}</li>
    </ul>
  </div>
</template>

<script>
export default {
  props: {
    players: Array,
  },
};
</script>
