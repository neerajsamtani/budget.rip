import React from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { Table } from "react-bootstrap";
import LineItem from './LineItem';
import axios from 'axios';

export default function EventDetailsModal ({show, event, lineItems, onHide}) {

  const deleteEvent = () => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    axios.get(`${REACT_APP_API_ENDPOINT}api/delete_event/${event._id}`)
    .then(response => {
        console.log(response.data);
        onHide();
    })
    .catch(error => console.log(error));
}

  return (
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
  );
}