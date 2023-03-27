import { createApp } from 'vue'
import App from './App.vue'
import router from './router';
import gameState from './gameState';

const app = createApp(App);
app.use(router);
app.provide('gameState', gameState);
app.mount('#app');
