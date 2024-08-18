import React, { Fragment, useState, useEffect } from 'react';
import axiosInstance from './axiosInstance';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import { useLineItems, useLineItemsDispatch } from "./contexts/LineItemsContext";
import Notification from './Notification';
import defaultNameCleanup from './utils/stringHelpers'
import { useField } from './hooks/useField';

export default function CreateEventModal({ show, onHide }) {

  const lineItems = useLineItems();
  const lineItemsDispatch = useLineItemsDispatch();

  const selectedLineItems = lineItems.filter(lineItem => lineItem.isSelected);
  const selectedLineItemIds = lineItems.filter(lineItem => lineItem.isSelected).map(lineItem => lineItem.id);
  // TODO: Make hints more robust with categories
  useEffect(() => {
    if (!show && selectedLineItems.length === 1) {
      name.setCustomValue(defaultNameCleanup(selectedLineItems[0].description))
    } else if (!show) {
      name.setEmpty()
    }
  }, [selectedLineItems, show])

  const name = useField("text")
  const category = useField("text", "All")
  const date = useField("date")
  const isDuplicateTransaction = useField("checkbox")

  const disableSubmit = name.value === "" || category.value === "" || category.value === "All"

  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Created Event",
      showNotification: false,
    }
  )

  const closeModal = () => {
    name.setEmpty()
    category.setEmpty()
    date.setEmpty()
    isDuplicateTransaction.setCustomValue(false);
    onHide()
  }

  const createEvent = (name, category) => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    var newEvent = {
      "name": name.value,
      "category": category.value,
      "date": date.value,
      "line_items": selectedLineItemIds,
      "is_duplicate_transaction": isDuplicateTransaction.value
    }
    console.log(newEvent);
    axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/events`, newEvent)
      .then(response => {
        console.log(response.data);
      })
      .then(() => {
        closeModal()
        lineItemsDispatch({
          type: 'remove_line_items',
          lineItemIds: selectedLineItemIds
        })
        setNotification({
          ...notification,
          showNotification: true
        })
        // TODO: Uncheck all checkboxes
      })
      .catch(error => console.log(error));
  }

  return (
    <Fragment>
      <Notification notification={notification} setNotification={setNotification} />
      <Modal
        show={show}
        onHide={closeModal}
        size="lg"
        aria-labelledby="contained-modal-title-vcenter"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title id="contained-modal-title-vcenter">
            New Event Details
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Name:</Form.Label>
              <Form.Control type={name.type} value={name.value} onChange={name.onChange} />
            </Form.Group>
            {/* TODO: Can I use a CategoryFilter here? */}
            <Form.Group className="mb-3">
              <Form.Label>Category:</Form.Label>
              <Form.Select value={category.value} onChange={category.onChange}>
                <option value="All">All</option>
                <option value="Alcohol">Alcohol</option>
                <option value="Dining">Dining</option>
                <option value="Entertainment">Entertainment</option>
                <option value="Forma">Forma</option>
                <option value="Groceries">Groceries</option>
                <option value="Hobbies">Hobbies</option>
                <option value="Income">Income</option>
                <option value="Investment">Investment</option>
                <option value="Rent">Rent</option>
                <option value="Shopping">Shopping</option>
                <option value="Subscription">Subscription</option>
                <option value="Transfer">Transfer</option>
                <option value="Transit">Transit</option>
                <option value="Travel">Travel</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Override Date:</Form.Label>
              <Form.Control type={date.type} value={date.value} onChange={date.onChange} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Check checked={isDuplicateTransaction.value} onChange={() => isDuplicateTransaction.setCustomValue(!isDuplicateTransaction.value)}
                type="checkbox" label="Duplicate Transaction" />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={closeModal} variant="secondary">Cancel</Button>
          <Button onClick={() => createEvent(name, category)} variant="primary" disabled={disableSubmit}>Submit</Button>
        </Modal.Footer>
      </Modal>
    </Fragment>
  );
}