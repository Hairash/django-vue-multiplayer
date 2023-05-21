import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: 'https://durak-game-backend.onrender.com',
});

export default axiosInstance;
