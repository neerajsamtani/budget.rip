import 'bootstrap/dist/css/bootstrap.min.css';
import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import { LineItemsProvider } from "./contexts/LineItemsContext";

ReactDOM.render(
    <LineItemsProvider>
        <App />
    </LineItemsProvider>
    , document.getElementById("root"));