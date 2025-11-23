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

// Response interceptor for handling 401 errors (expired/invalid token)
axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
        // Don't redirect for auth endpoints (login check, etc.)
        const isAuthEndpoint = error.config?.url?.includes('/api/auth/');

        if (error.response?.status === 401 && !isAuthEndpoint) {
            // Token expired or invalid - redirect to login
            // Only redirect if not already on login page
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default axiosInstance
