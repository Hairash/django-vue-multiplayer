import { createRouter, createWebHistory } from 'vue-router';
import AuthField from '../components/AuthField.vue';
import GameBoard from '../components/GameBoard.vue';

const routes = [
  {
    path: '/',
    name: 'GameBoard',
    component: GameBoard,
  },
  {
    path: '/auth',
    name: 'AuthField',
    component: AuthField,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
