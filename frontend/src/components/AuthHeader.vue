<template>
  <div>
    <span v-if="isLoggedIn">
      Welcome, {{ username }}
      <router-link to="/auth">Log out</router-link>
    </span>
    <router-link v-else to="/auth">Log in</router-link>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isLoggedIn: false,
      username: '',
    };
  },
  async created() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    if (token && user) {
      this.isLoggedIn = true;
      this.username = user;
    }
    else {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },
};
</script>
