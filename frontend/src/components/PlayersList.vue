<template>
  <div>
    <h3>{{ header }}</h3>
    <ul>
      <li v-for="player in players" :key="player">{{ player }}</li>
    </ul>
  </div>
</template>

<script>
export default {
  props: {
    header: String,
    players: Array,
  },
};
</script>
