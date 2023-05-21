<template>
    <div>
      <h2>Login</h2>
      <form @submit.prevent="login">
        <input v-model="username" placeholder="Username" />
        <input v-model="password" placeholder="Password" type="password" />
        <button>Login</button>
      </form>

      <h2>Register</h2>
      <form @submit.prevent="register">
        <input v-model="newUsername" placeholder="Username" />
        <input v-model="newEmail" placeholder="Email" />
        <input v-model="newPassword" placeholder="Password" type="password" />
        <button>Register</button>
      </form>
    </div>
  </template>

  <script>
  import axiosInstance from '../axiosInstance';

  export default {
    inject: ['clientState'],
    data() {
      return {
        username: '',
        password: '',
        newUsername: '',
        newEmail: '',
        newPassword: '',
      };
    },
    methods: {
      async login() {
        try {
          const response = await axiosInstance.post('/api/user_auth/login/', {
            username: this.username,
            password: this.password,
          });
          this.saveCredentials(response.data.token, this.username);
          this.$router.push('/');
        } catch (error) {
          console.error('Login failed:', error);
        }
      },

      async register() {
        try {
          const response = await axiosInstance.post('/api/user_auth/register/', {
            username: this.newUsername,
            email: this.newEmail,
            password: this.newPassword,
          });
          this.saveCredentials(response.data.token, this.newUsername);
          this.$router.push('/');
        } catch (error) {
          console.error('Registration failed:', error);
        }
      },

      saveCredentials(token, username) {
        localStorage.setItem('token', token);
        localStorage.setItem('user', username);
        this.clientState.checkLoggedIn();
      }
    },
  };
  </script>
