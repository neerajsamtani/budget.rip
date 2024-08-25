import { axiosInstance } from "./utils";

export const getLineItems = async (
    params: {
        payment_method?: string;
        month?: string;
        year?: string;
    } = {}
) => {
    try {
        // TODO: Get the REACT_APP_API_ENDPOINT in the process environment variable
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        REACT_APP_API_ENDPOINT = "http://dev.localhost:4242/";
        const { data } = await axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/line_items`, {
            params,
        });
        return data.data;
    } catch (error) {
        console.error("Error fetching line items:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
};

export const getPaymentMethods = async () => {
    try {
        // TODO: Get the REACT_APP_API_ENDPOINT in the process environment variable
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        REACT_APP_API_ENDPOINT = "http://dev.localhost:4242/";
        const { data } = await axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/payment_methods`);
        return data;
    } catch (error) {
        console.error("Error fetching payment methods:", error);
        throw error; // Re-throw the error for handling in the caller function
    }
};