import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import axios from "axios";

export default function CreateEventModal ({show, selectedLineItems, setSelectedLineItems, onHide}) {
    const [name, setName] = useState('')
    const [category, setCategory] = useState('')
    const [date, setDate] = useState('')
    const [isDuplicateTransaction, setIsDuplicateTransaction] = useState(false)
    const handleNameChange = (event) => {
        setName(event.target.value)
    }
    const handleCategoryChange = (event) => {
        setCategory(event.target.value)
    }
    const handleDateChange = (event) => {
      setDate(event.target.value)
    }
    const handleIsDuplicateTransactionChange = (event) => {
      setIsDuplicateTransaction(!isDuplicateTransaction)
    }

    const createEvent = (name, category) => {
        var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
        var newEvent = {
            "name": name,
            "category": category,
            "line_items": selectedLineItems,
            "date": date,
            "is_duplicate_transaction": isDuplicateTransaction
        }
        console.log(newEvent);
        axios.post(`${REACT_APP_API_ENDPOINT}api/create_event`, newEvent)
        .then(response => {
            console.log(response.data);
        })
        .then(() => {
            setName('');
            setCategory('');
            setSelectedLineItems([]);
            setDate('');
            setIsDuplicateTransaction(false);
            // TODO: Uncheck all checkboxes
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
            New Event Details
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Name:</Form.Label>
            <Form.Control type="text" value={name} onChange={handleNameChange}/>
          </Form.Group>
          <Form.Group className="mb-3">
          <Form.Label>Category:</Form.Label>
            <Form.Select value={category} onChange={handleCategoryChange}>
                <option value="All">All</option>
                <option value="Alcohol">Alcohol</option>
                <option value="Dining">Dining</option>
                <option value="Entertainment">Entertainment</option>
                <option value="Groceries">Groceries</option>
                <option value="Hobbies">Hobbies</option>
                <option value="Income">Income</option>
                <option value="N/A">N/A</option>
                <option value="Rent">Rent</option>
                <option value="Shopping">Shopping</option>
                <option value="Subscription">Subscription</option>
                <option value="Transit">Transit</option>
                <option value="Travel">Travel</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
          <Form.Label>Override Date:</Form.Label>
            <Form.Control type="date" value={date} onChange={handleDateChange}/>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Check checked={isDuplicateTransaction} onChange={handleIsDuplicateTransactionChange} 
              type="checkbox" label="Duplicate Transaction" />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={onHide} variant="secondary">Cancel</Button>
        <Button onClick={() => createEvent(name, category)} variant="primary">Submit</Button>
      </Modal.Footer>
    </Modal>
  );
}