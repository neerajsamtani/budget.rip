import axios from "axios";
import Cookies from "js-cookie";

const axiosInstance = axios.create({
    baseURL: String(import.meta.env.VITE_API_ENDPOINT),
    withCredentials: true
})

// Add interceptor to include CSRF token from cookie in request headers
axiosInstance.interceptors.request.use((config) => {
    const csrfToken = Cookies.get('csrf_access_token');

    if (csrfToken && config.method && ['post', 'put', 'delete', 'patch'].includes(config.method.toLowerCase())) {
        config.headers['X-CSRF-TOKEN'] = csrfToken;
    }

    return config;
});

export default axiosInstance
