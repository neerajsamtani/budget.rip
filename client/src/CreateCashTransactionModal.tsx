import React, { useState, Fragment } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import axiosInstance from './axiosInstance';
import Notification from './Notification';
import { useField } from './hooks/useField';

export default function CreateCashTransactionModal({ show, onHide }: { show: boolean, onHide: () => void }) {
  const [notification, setNotification] = useState(
    {
      heading: "Notification",
      message: "Created Cash Transaction",
      showNotification: false,
    }
  )

  const date = useField("date")
  const person = useField("text")
  const description = useField("text")
  const amount = useField("number")

  const createCashTransaction = () => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    var newCashTransaction = {
      "date": date.value,
      "person": person.value,
      "description": description.value,
      "amount": amount.value
    }
    console.log(newCashTransaction);
    axiosInstance.post(`${REACT_APP_API_ENDPOINT}api/cash_transaction`, newCashTransaction)
      .then(response => {
        console.log(response.data);
      })
      .then(() => {
        date.setEmpty()
        person.setEmpty()
        description.setEmpty()
        amount.setEmpty()
        setNotification({
          ...notification,
          showNotification: true
        })
        // TODO: Uncheck all checkboxes
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
            New Cash Transaction
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <form>
            <div className="form-group">
              {/* TODO: DATE PICKER */}
              <label>Date:</label>
              <input className="form-control" id="event-date" value={date.value} onChange={date.onChange} type={date.type} />
            </div>
            <div className="form-group">
              <label>Person:</label>
              <input className="form-control" id="event-person" value={person.value} onChange={person.onChange} type={person.type} />
            </div>
            <div className="form-group">
              <label>Description:</label>
              <input className="form-control" id="event-description" value={description.value} onChange={description.onChange} type={description.type} />
            </div>
            <div className="form-group">
              <label>Amount:</label>
              <input className="form-control" id="event-amount" value={amount.value} onChange={amount.onChange} type={amount.type} />
            </div>
          </form>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={onHide} variant="secondary">Cancel</Button>
          <Button onClick={createCashTransaction} variant="primary">Submit</Button>
        </Modal.Footer>
      </Modal>
    </Fragment>
  );
}