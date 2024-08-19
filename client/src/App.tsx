import { loadStripe } from "@stripe/stripe-js";
import axiosInstance from "./utils/axiosInstance";
import React, { useState } from "react";
import { Button, Spinner } from "react-bootstrap";
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import {
  BrowserRouter as Router, Link, Route, Routes
} from "react-router-dom";
import ConnectedAccountsPage from "./pages/ConnectedAccountsPage";
import { useLineItemsDispatch } from "./contexts/LineItemsContext";
import EventsPage from "./pages/EventsPage";
import GraphsPage from "./pages/GraphsPage";
import LineItemsPage from "./pages/LineItemsPage";
import LoginPage from "./pages/LoginPage";
import LineItemsToReviewPage from "./pages/LineItemsToReviewPage";
import Notification from "./components/Notification";

// Make sure to call loadStripe outside of a component’s render to avoid
// recreating the Stripe object on every render.
// This is a public sample test API key.
// Don’t submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.
var STRIPE_PUBLIC_KEY = String(process.env.REACT_APP_STRIPE_PUBLIC_KEY);
var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

export default function App() {

  const lineItemsDispatch = useLineItemsDispatch();
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Refreshed data",
      showNotification: false,
    }
  )

  const handleRefreshData = () => {
    setLoading(true);
    axiosInstance.get(`${REACT_APP_API_ENDPOINT}api/refresh/all`)
      .then(response => {
        setNotification({
          ...notification,
          showNotification: true
        })
        setLoading(false);
        lineItemsDispatch({
          type: "populate_line_items",
          fetchedLineItems: response.data.data
        })
      })
      .catch(error => console.log(error))
  }

  const padding = {
    paddingLeft: 20,
    paddingTop: 5,
    paddingBottom: 5,
    color: "white",
    textDecoration: "none"
  }

  return (
    <React.StrictMode>
      <Notification notification={notification} setNotification={setNotification} />
      <Router>
        <Navbar bg="dark" variant="dark" expand="sm">
          <Container>
            <Navbar.Brand>Budgit</Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="me-auto">
                <Link style={padding} to="/">Review</Link>
                <Link style={padding} to="/events">Events</Link>
                <Link style={padding} to="/line_items">Line Items</Link>
                <Link style={padding} to="/connected_accounts">Connected Accounts</Link>
                <Link style={padding} to="/graphs">Graphs</Link>
                <Link style={padding} to="/login">Login</Link>
              </Nav>
              <Nav>
                <Button onClick={handleRefreshData}>
                  {
                    loading ?
                      <Spinner
                        as="span"
                        animation="border"
                        size="sm"
                        role="status"
                        aria-hidden="true"
                      />
                      :
                      <>Refresh Data</>
                  }
                </Button>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Routes>
          <Route path="/" element={<LineItemsToReviewPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/line_items" element={<LineItemsPage />} />
          <Route path="/connected_accounts" element={<ConnectedAccountsPage stripePromise={stripePromise} />} />
          <Route path="/graphs" element={<GraphsPage />} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </Router>
    </React.StrictMode>
  );
}