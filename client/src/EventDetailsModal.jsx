import axios from 'axios';
import React, { Fragment, useState } from 'react';
import { Table } from "react-bootstrap";
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import LineItem from './LineItem';
import Notification from './Notification';

export default function EventDetailsModal({ show, event, lineItems, onHide }) {

  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Deleted Event",
      showNotification: false,
    }
  )

  const deleteEvent = () => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axios.delete(`${REACT_APP_API_ENDPOINT}api/events/${event._id}`)
      .then(response => {
        console.log(response.data);
        setNotification({
          ...notification,
          showNotification: true
        })
        onHide();
      })
      .catch(error => console.log(error));
  }

  return (
    <Fragment>
      <Notification notification={notification} setNotification={setNotification} />
      <Modal
        show={show}
        onHide={onHide}
        size="lg"
        aria-labelledby="contained-modal-title-vcenter"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title id="contained-modal-title-vcenter">
            {event.name} | {event.category}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Date</th>
                <th>Payment Method</th>
                <th>Description</th>
                <th>Name</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {lineItems.map(lineItem =>
                <LineItem key={lineItem._id} lineItem={lineItem} />
              )}
            </tbody>
          </Table>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={onHide} variant="secondary">Cancel</Button>
          <Button onClick={deleteEvent} variant="danger">Delete</Button>
        </Modal.Footer>
      </Modal>
    </Fragment>
  );
}