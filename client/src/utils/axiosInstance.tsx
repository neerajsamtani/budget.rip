import axios from "axios";

const axiosInstance = axios.create({
    baseURL: String(import.meta.env.VITE_API_ENDPOINT),
    withCredentials: true
})

export default axiosInstance
