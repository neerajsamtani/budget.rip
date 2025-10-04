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
import { useLineItemsDispatch } from "./contexts/LineItemsContext";
import { showErrorToast, showSuccessToast } from "./utils/toast-helpers";
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
const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

export default function App() {

  const lineItemsDispatch = useLineItemsDispatch();
  const [loading, setLoading] = useState(false);

  const handleRefreshData = () => {
    setLoading(true);
    axiosInstance.get(`api/refresh/all`)
      .then(response => {
        showSuccessToast("Refreshed data", "Notification");
        setLoading(false);
        lineItemsDispatch({
          type: "populate_line_items",
          fetchedLineItems: response.data.data
        })
      })
      .catch((error) => {
        showErrorToast(new Error("Error refreshing data"), "Notification");
        setLoading(false);
      })
  }


  return (
    <React.StrictMode>
      <Toaster position="top-right" richColors />
      <Router>
        <Navbar className="bg-white shadow-sm border-b">
          <div className="container mx-auto flex justify-between items-center px-6 h-16">
            <NavbarBrand className="text-foreground font-heading font-semibold text-lg">
              Budgit
            </NavbarBrand>
            <div className="flex items-center space-x-6">
              <div className="flex space-x-1">
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/"
                >
                  Review
                </Link>
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/events"
                >
                  Events
                </Link>
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/line_items"
                >
                  Line Items
                </Link>
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/connected_accounts"
                >
                  Connected Accounts
                </Link>
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/graphs"
                >
                  Graphs
                </Link>
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/test"
                >
                  Test Shadcn
                </Link>
                <Link
                  className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                  to="/login"
                >
                  Login
                </Link>
              </div>
              <Button onClick={handleRefreshData} variant="default">
                {loading ? <Spinner size="sm" /> : "Refresh Data"}
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