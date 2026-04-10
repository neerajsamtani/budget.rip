import { Button } from "@/components/ui/button";
import { Navbar, NavbarBrand } from "@/components/ui/navbar";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Toaster } from "@/components/ui/sonner";
import { Spinner } from "@/components/ui/spinner";
import { loadStripe } from "@stripe/stripe-js";
import { BellIcon, MenuIcon } from "lucide-react";
import React, { Suspense, useState } from "react";
import {
  Link, Route,
  BrowserRouter as Router,
  Routes
} from "react-router-dom";
import { ProtectedRoute, PublicOnlyRoute } from "./components/ProtectedRoute";
import { useAuth } from "./contexts/AuthContext";
import { useLineItemsDispatch } from "./contexts/LineItemsContext";
import { NotificationItem, useMarkNotificationsRead, useNotifications, useRefreshAllData } from "./hooks/useApi";
import LineItemsToReviewPage from "./pages/LineItemsToReviewPage";

const ConnectedAccountsPage = React.lazy(() => import("./pages/ConnectedAccountsPage"));
const EventDetailsPage = React.lazy(() => import("./pages/EventDetailsPage"));
const EventsPage = React.lazy(() => import("./pages/EventsPage"));
const GraphsPage = React.lazy(() => import("./pages/GraphsPage"));
const LineItemsPage = React.lazy(() => import("./pages/LineItemsPage"));
const LoginPage = React.lazy(() => import("./pages/LoginPage"));
const SettingsPage = React.lazy(() => import("./pages/SettingsPage"));
import { Badge } from "./components/ui/badge";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import { showErrorToast, showSuccessToast } from "./utils/toast-helpers";

// Make sure to call loadStripe outside of a component's render to avoid
// recreating the Stripe object on every render.
// This is a public sample test API key.
// Don't submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.
const STRIPE_PUBLIC_KEY = String(import.meta.env.VITE_STRIPE_PUBLIC_KEY);
const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

function NotificationEntry({ n, onNavigate }: { n: NotificationItem; onNavigate?: () => void }) {
  const content = (
    <div className="text-sm p-2 rounded bg-muted/50 border-l-2 border-amber-500">
      {n.message}
    </div>
  );
  return n.event_id ? (
    <Link to={`/events/${n.event_id}`} onClick={onNavigate} className="block no-underline hover:opacity-80">
      {content}
    </Link>
  ) : content;
}

export default function App() {

  const lineItemsDispatch = useLineItemsDispatch();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const refreshMutation = useRefreshAllData();
  const { isAuthenticated, logout } = useAuth();
  const { data: notifications } = useNotifications(isAuthenticated);
  const markReadMutation = useMarkNotificationsRead();

  const handleDismissAll = () => {
    if (notifications?.length) {
      markReadMutation.mutate(notifications.map(n => n.id), {
        onSuccess: () => setNotificationsOpen(false),
      });
    }
  };

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
                    to="/settings"
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
                <Popover open={notificationsOpen} onOpenChange={setNotificationsOpen}>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="relative" aria-label="Notifications">
                      <BellIcon className="h-4 w-4" />
                      {notifications && notifications.length > 0 && (
                        <Badge variant="destructive" className="absolute -top-1 -right-1 h-4 min-w-4 px-1 text-[10px] flex items-center justify-center">
                          {notifications.length}
                        </Badge>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-80" align="center" sideOffset={12}>
                    <div className="space-y-3 p-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm">Notifications</h4>
                        {notifications && notifications.length > 0 && (
                          <Button variant="ghost" size="sm" className="text-xs h-6" onClick={handleDismissAll} disabled={markReadMutation.isPending}>
                            Dismiss all
                          </Button>
                        )}
                      </div>
                      {!notifications?.length ? (
                        <p className="text-sm text-muted-foreground">No new notifications</p>
                      ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {notifications.map(n => (
                            <NotificationEntry key={n.id} n={n} onNavigate={() => setNotificationsOpen(false)} />
                          ))}
                        </div>
                      )}
                    </div>
                  </PopoverContent>
                </Popover>
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
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="relative" aria-label="Notifications">
                      <BellIcon className="h-4 w-4" />
                      {notifications && notifications.length > 0 && (
                        <Badge variant="destructive" className="absolute -top-1 -right-1 h-4 min-w-4 px-1 text-[10px] flex items-center justify-center">
                          {notifications.length}
                        </Badge>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-72" align="center" sideOffset={12}>
                    <div className="space-y-3 p-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm">Notifications</h4>
                        {notifications && notifications.length > 0 && (
                          <Button variant="ghost" size="sm" className="text-xs h-6" onClick={handleDismissAll} disabled={markReadMutation.isPending}>
                            Dismiss all
                          </Button>
                        )}
                      </div>
                      {!notifications?.length ? (
                        <p className="text-sm text-muted-foreground">No new notifications</p>
                      ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {notifications.map(n => (
                            <NotificationEntry key={n.id} n={n} onNavigate={() => setNotificationsOpen(false)} />
                          ))}
                        </div>
                      )}
                    </div>
                  </PopoverContent>
                </Popover>
              )}
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
                          to="/settings"
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

        <Suspense fallback={<div className="flex justify-center py-20"><Spinner size="md" /></div>}>
          <Routes>
            <Route path="/" element={<ProtectedRoute><LineItemsToReviewPage /></ProtectedRoute>} />
            <Route path="/events" element={<ProtectedRoute><EventsPage /></ProtectedRoute>} />
            <Route path="/events/:eventId" element={<ProtectedRoute><EventDetailsPage /></ProtectedRoute>} />
            <Route path="/line_items" element={<ProtectedRoute><LineItemsPage /></ProtectedRoute>} />
            <Route path="/connected_accounts" element={<ProtectedRoute><ConnectedAccountsPage stripePromise={stripePromise} /></ProtectedRoute>} />
            <Route path="/graphs" element={<ProtectedRoute><GraphsPage /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
            <Route path="/login" element={<PublicOnlyRoute><LoginPage /></PublicOnlyRoute>} />
          </Routes>
        </Suspense>
      </Router>
    </React.StrictMode>
  );
}