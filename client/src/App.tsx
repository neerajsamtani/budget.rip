import { Button } from "@/components/ui/button";
import { Navbar, NavbarBrand } from "@/components/ui/navbar";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Toaster } from "@/components/ui/sonner";
import { Spinner } from "@/components/ui/spinner";
import { loadStripe } from "@stripe/stripe-js";
import { MenuIcon } from "lucide-react";
import React, { useState } from "react";
import {
  Link, Route,
  BrowserRouter as Router,
  Routes
} from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
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

function AppContent() {
  const lineItemsDispatch = useLineItemsDispatch();
  const [loading, setLoading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated } = useAuth();

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
    <>
      <Router>
        <Navbar className="bg-white shadow-sm border-b">
          <div className="container mx-auto flex justify-between items-center px-4 md:px-6 h-16">
            <NavbarBrand className="text-foreground font-heading font-semibold text-lg">
              Budgit
            </NavbarBrand>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-4 lg:space-x-6">
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
                {!isAuthenticated && (
                  <Link
                    className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150"
                    to="/login"
                  >
                    Login
                  </Link>
                )}
              </div>
              <Button onClick={handleRefreshData} variant="default" size="sm">
                {loading ? <Spinner size="sm" /> : "Refresh Data"}
              </Button>
            </div>

            {/* Mobile Navigation */}
            <div className="md:hidden flex items-center gap-2">
              <Button onClick={handleRefreshData} variant="default" size="sm">
                {loading ? <Spinner size="sm" /> : "Refresh"}
              </Button>
              <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm" aria-label="Open navigation menu">
                    <MenuIcon className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[250px] sm:w-[300px]">
                  <nav className="flex flex-col gap-4">
                    <Link
                      className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                      to="/"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Review
                    </Link>
                    <Link
                      className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                      to="/events"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Events
                    </Link>
                    <Link
                      className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                      to="/line_items"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Line Items
                    </Link>
                    <Link
                      className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                      to="/connected_accounts"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Connected Accounts
                    </Link>
                    <Link
                      className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                      to="/graphs"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Graphs
                    </Link>
                    <Link
                      className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                      to="/test"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Test Shadcn
                    </Link>
                    {!isAuthenticated && (
                      <Link
                        className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                        to="/login"
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        Login
                      </Link>
                    )}
                  </nav>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </Navbar>

        <Routes>
          <Route path="/" element={<ProtectedRoute><LineItemsToReviewPage /></ProtectedRoute>} />
          <Route path="/events" element={<ProtectedRoute><EventsPage /></ProtectedRoute>} />
          <Route path="/line_items" element={<ProtectedRoute><LineItemsPage /></ProtectedRoute>} />
          <Route path="/connected_accounts" element={<ProtectedRoute><ConnectedAccountsPage stripePromise={stripePromise} /></ProtectedRoute>} />
          <Route path="/graphs" element={<ProtectedRoute><GraphsPage /></ProtectedRoute>} />
          <Route path="/test" element={<ProtectedRoute><ShadcnTestPage /></ProtectedRoute>} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </Router>
    </>
  );
}

export default function App() {
  return (
    <React.StrictMode>
      <Toaster position="top-right" richColors />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </React.StrictMode>
  );
}