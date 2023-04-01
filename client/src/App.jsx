import React from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
  BrowserRouter as Router,
  Routes, Route, Link
} from "react-router-dom"
import axios from "axios";

import LineItems from "./LineItems";
import LineItemsToReview from "./LineItemsToReview";
import ConnectedAccounts from "./ConnectedAccounts";
import Events from "./Events";
import Graphs from "./Graphs";

import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import { Button, Spinner } from "react-bootstrap";
import { useState } from "react";

// Make sure to call loadStripe outside of a component’s render to avoid
// recreating the Stripe object on every render.
// This is a public sample test API key.
// Don’t submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.
var STRIPE_PUBLIC_KEY = String(process.env.REACT_APP_STRIPE_PUBLIC_KEY);
var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

export default function App() {

  const [loading, setLoading] = useState(false);

  const handleRefreshData = () => {
    setLoading(true);
    axios.get(`${REACT_APP_API_ENDPOINT}api/refresh_data`)
      .then(response => {
        setLoading(false);
      })
      .catch(error => console.log(error))
  }

  const padding = {
    padding: 20,
    color: "white",
    textDecoration: "none"
  }

  return (
    <React.StrictMode>
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
          <Route path="/" element={<LineItemsToReview />} />
          <Route path="/events" element={<Events />} />
          <Route path="/line_items" element={<LineItems />} />
          <Route path="/connected_accounts" element={<ConnectedAccounts stripePromise={stripePromise} />} />
          <Route path="/graphs" element={<Graphs />} />
        </Routes>
      </Router>
    </React.StrictMode>
  );
}