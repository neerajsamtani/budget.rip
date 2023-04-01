import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import axios from "axios";

export default function CreateCashTransactionModal({ show, onHide }) {
  const [date, setDate] = useState('')
  const [person, setPerson] = useState('')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')

  const handleDateChange = (event) => {
    setDate(event.target.value)
  }
  const handlePersonChange = (event) => {
    setPerson(event.target.value)
  }
  const handleDescriptionChange = (event) => {
    setDescription(event.target.value)
  }
  const handleAmountChange = (event) => {
    setAmount(event.target.value)
  }

  const createCashTransaction = () => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    var newCashTransaction = {
      "date": date,
      "person": person,
      "description": description,
      "amount": amount
    }
    console.log(newCashTransaction);
    axios.post(`${REACT_APP_API_ENDPOINT}api/create_cash_transaction`, newCashTransaction)
      .then(response => {
        console.log(response.data);
      })
      .then(() => {
        setDate('');
        setPerson('');
        setDescription('');
        setAmount('');
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
          New Cash Transaction
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <form>
          <div className="form-group">
            {/* TODO: DATE PICKER */}
            <label>Date:</label>
            <input type="date" className="form-control" id="event-date" value={date} onChange={handleDateChange} />
          </div>
          <div className="form-group">
            <label>Person:</label>
            <input type="text" className="form-control" id="event-person" value={person} onChange={handlePersonChange} />
          </div>
          <div className="form-group">
            <label>Description:</label>
            <input type="text" className="form-control" id="event-description" value={description} onChange={handleDescriptionChange} />
          </div>
          <div className="form-group">
            <label>Amount:</label>
            <input type="number" className="form-control" id="event-amount" value={amount} onChange={handleAmountChange} />
          </div>
        </form>
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={onHide} variant="secondary">Cancel</Button>
        <Button onClick={createCashTransaction} variant="primary">Submit</Button>
      </Modal.Footer>
    </Modal>
  );
}