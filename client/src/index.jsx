import 'bootstrap/dist/css/bootstrap.min.css';
import React from "react";
import { createRoot } from 'react-dom/client';
import App from "./App";
import { LineItemsProvider } from "./contexts/LineItemsContext";

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
    <LineItemsProvider>
        <App />
    </LineItemsProvider>
);