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
import { ProtectedRoute, PublicOnlyRoute } from "./components/ProtectedRoute";
import { useAuth } from "./contexts/AuthContext";
import { useLineItemsDispatch } from "./contexts/LineItemsContext";
import { useRefreshAllData } from "./hooks/useApi";
import ConnectedAccountsPage from "./pages/ConnectedAccountsPage";
import EventHintsSettingsPage from "./pages/EventHintsSettingsPage";
import EventsPage from "./pages/EventsPage";
import GraphsPage from "./pages/GraphsPage";
import LineItemsPage from "./pages/LineItemsPage";
import LineItemsToReviewPage from "./pages/LineItemsToReviewPage";
import LoginPage from "./pages/LoginPage";
import { showErrorToast, showSuccessToast } from "./utils/toast-helpers";

// Make sure to call loadStripe outside of a component's render to avoid
// recreating the Stripe object on every render.
// This is a public sample test API key.
// Don't submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.
const STRIPE_PUBLIC_KEY = String(import.meta.env.VITE_STRIPE_PUBLIC_KEY);
const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

export default function App() {

  const lineItemsDispatch = useLineItemsDispatch();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const refreshMutation = useRefreshAllData();
  const { isAuthenticated, logout } = useAuth();

  const handleRefreshData = () => {
    refreshMutation.mutate(undefined, {
      onSuccess: (data) => {
        showSuccessToast("Refreshed data", "Notification");
        lineItemsDispatch({
          type: "populate_line_items",
          fetchedLineItems: data
        })
      },
      onError: (error) => {
        showErrorToast(error);
      }
    });
  }


  return (
    <React.StrictMode>
      <Toaster position="top-right" richColors closeButton />
      <Router>
        <Navbar className="bg-white shadow-sm border-b">
          <div className="container mx-auto flex justify-between items-center px-4 md:px-6 h-16">
            <NavbarBrand className="text-foreground font-heading font-semibold text-lg">
              <Link
                to="/"
              >
                Budgit
              </Link>
            </NavbarBrand>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center space-x-2 xl:space-x-4">
              {isAuthenticated && (
                <div className="flex space-x-1">
                  <Link
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 text-sm xl:text-base whitespace-nowrap"
                    to="/"
                  >
                    Review
                  </Link>
                  <Link
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 text-sm xl:text-base whitespace-nowrap"
                    to="/events"
                  >
                    Events
                  </Link>
                  <Link
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 text-sm xl:text-base whitespace-nowrap"
                    to="/line_items"
                  >
                    Line Items
                  </Link>
                  <Link
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 text-sm xl:text-base whitespace-nowrap"
                    to="/connected_accounts"
                  >
                    Connected Accounts
                  </Link>
                  <Link
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 text-sm xl:text-base whitespace-nowrap"
                    to="/graphs"
                  >
                    Graphs
                  </Link>
                  <Link
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 text-sm xl:text-base whitespace-nowrap"
                    to="/settings/event-hints"
                  >
                    Settings
                  </Link>
                  <button
                    className="text-foreground hover:text-primary px-2 xl:px-3 py-2 no-underline font-body font-medium transition-colors duration-150 cursor-pointer text-sm xl:text-base whitespace-nowrap"
                    onClick={() => logout()}
                  >
                    Log Out
                  </button>
                </div>
              )}

              {isAuthenticated && (
                <Button onClick={handleRefreshData} variant="default" size="sm" disabled={refreshMutation.isPending} className="whitespace-nowrap">
                  {refreshMutation.isPending ? <Spinner size="sm" /> : "Refresh Data"}
                </Button>
              )}
            </div>

            {/* Mobile Navigation */}
            <div className="lg:hidden flex items-center gap-2">
              {isAuthenticated && (
                <Button onClick={handleRefreshData} variant="default" size="sm" disabled={refreshMutation.isPending}>
                  {refreshMutation.isPending ? <Spinner size="sm" /> : "Refresh"}
                </Button>
              )}
              <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="sm" aria-label="Open navigation menu">
                    <MenuIcon className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="!w-[250px] sm:!w-[300px] !max-w-none">
                  <nav className="flex flex-col gap-4">
                    {isAuthenticated ? (
                      <>
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
                          to="/settings/event-hints"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          Settings
                        </Link>
                        <button
                          className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted text-left cursor-pointer"
                          onClick={() => {
                            logout();
                            setMobileMenuOpen(false);
                          }}
                        >
                          Log Out
                        </button>
                      </>
                    ) : (
                      <Link
                        className="text-foreground hover:text-primary px-3 py-2 no-underline font-body font-medium transition-colors duration-150 rounded-md hover:bg-muted"
                        to="/login"
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        Log In
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
          <Route path="/settings/event-hints" element={<ProtectedRoute><EventHintsSettingsPage /></ProtectedRoute>} />
          <Route path="/login" element={<PublicOnlyRoute><LoginPage /></PublicOnlyRoute>} />
        </Routes>
      </Router>
    </React.StrictMode>
  );
}