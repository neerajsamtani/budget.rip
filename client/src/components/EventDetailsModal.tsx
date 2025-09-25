import React, { Fragment, useState } from 'react';
import { Badge, Table } from "react-bootstrap";
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { LineItemInterface } from '../contexts/LineItemsContext';
import axiosInstance from '../utils/axiosInstance';
import { EventInterface } from './Event';
import LineItem from './LineItem';
import Notification from './Notification';

export default function EventDetailsModal({ show, event, lineItemsForEvent, onHide }:
  { show: boolean, event: EventInterface, lineItemsForEvent: LineItemInterface[], onHide: () => void }) {

  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Deleted Event",
      showNotification: false,
    }
  )

  const deleteEvent = () => {
    var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.delete(`${VITE_API_ENDPOINT}api/events/${event._id}`)
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
              {lineItemsForEvent.map(lineItem =>
                <LineItem key={lineItem._id} lineItem={lineItem} />
              )}
            </tbody>
          </Table>
          {event.tags && event.tags.length > 0 && (
            <div className="mb-3">
              <strong>Tags: </strong>
              <div className="d-flex flex-wrap gap-2">
                {event.tags.map((tag, index) => (
                  <Badge key={index} bg="primary" className="p-2">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={onHide} variant="secondary">Cancel</Button>
          <Button onClick={deleteEvent} variant="danger">Delete</Button>
        </Modal.Footer>
      </Modal>
    </Fragment>
  );
}
