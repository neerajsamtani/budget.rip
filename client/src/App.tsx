import { Button } from "@/components/ui/button";
import { Navbar, NavbarBrand } from "@/components/ui/navbar";
import { Toaster } from "@/components/ui/sonner";
import { Spinner } from "@/components/ui/spinner";
import { loadStripe } from "@stripe/stripe-js";
import React, { useState } from "react";
import {
  Link, Route,
  BrowserRouter as Router,
  Routes
} from "react-router-dom";
import { toast } from "sonner";
import { useLineItemsDispatch } from "./contexts/LineItemsContext";
import ConnectedAccountsPage from "./pages/ConnectedAccountsPage";
import EventsPage from "./pages/EventsPage";
import GraphsPage from "./pages/GraphsPage";
import LineItemsPage from "./pages/LineItemsPage";
import LineItemsToReviewPage from "./pages/LineItemsToReviewPage";
import LoginPage from "./pages/LoginPage";
import ShadcnTestPage from "./pages/ShadcnTestPage";
import axiosInstance from "./utils/axiosInstance";

// Make sure to call loadStripe outside of a component's render to avoid
// recreating the Stripe object on every render.
// This is a public sample test API key.
// Don't submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.
const STRIPE_PUBLIC_KEY = String(import.meta.env.VITE_STRIPE_PUBLIC_KEY);
const VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

export default function App() {

  const lineItemsDispatch = useLineItemsDispatch();
  const [loading, setLoading] = useState(false);

  const handleRefreshData = () => {
    setLoading(true);
    axiosInstance.get(`${VITE_API_ENDPOINT}api/refresh/all`)
      .then(response => {
        toast.success("Notification", {
          description: "Refreshed data",
          duration: 3500,
        });
        setLoading(false);
        lineItemsDispatch({
          type: "populate_line_items",
          fetchedLineItems: response.data.data
        })
      })
      .catch(() => {
        toast.error("Notification", {
          description: "Error refreshing data",
          duration: 3500,
        });
        setLoading(false);
      })
  }


  return (
    <React.StrictMode>
      <Toaster position="top-right" richColors />
      <Router>
        <Navbar className="bg-slate-900 text-white">
          <div className="container mx-auto flex justify-between items-center px-4">
            <NavbarBrand className="text-white">Budgit</NavbarBrand>
            <div className="flex items-center space-x-4">
              <div className="flex space-x-4">
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/">Review</Link>
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/events">Events</Link>
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/line_items">Line Items</Link>
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/connected_accounts">Connected Accounts</Link>
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/graphs">Graphs</Link>
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/test">Test Shadcn</Link>
                <Link className="text-white hover:text-gray-300 px-3 py-2 no-underline" to="/login">Login</Link>
              </div>
              <Button onClick={handleRefreshData} variant="secondary">
                {
                  loading ?
                    <Spinner
                      size="sm"
                    />
                    :
                    <>Refresh Data</>
                }
              </Button>
            </div>
          </div>
        </Navbar>

        <Routes>
          <Route path="/" element={<LineItemsToReviewPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/line_items" element={<LineItemsPage />} />
          <Route path="/connected_accounts" element={<ConnectedAccountsPage stripePromise={stripePromise} />} />
          <Route path="/graphs" element={<GraphsPage />} />
          <Route path="/test" element={<ShadcnTestPage />} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </Router>
    </React.StrictMode>
  );
}