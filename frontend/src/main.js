import { createApp, reactive } from 'vue'
import App from './App.vue'
import router from './router';
import clientState from '@/clientState';

const app = createApp(App);

app.use(router);
app.provide('clientState', reactive(clientState));
app.mount('#app');
