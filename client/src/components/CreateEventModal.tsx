import React, { Fragment, useState, useEffect } from 'react';
import axiosInstance from '../utils/axiosInstance';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import { useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import Notification from './Notification';
import defaultNameCleanup from '../utils/stringHelpers'
import { FormField, useField } from '../hooks/useField';
import Stack from 'react-bootstrap/Stack';
import Badge from 'react-bootstrap/Badge';
import { getPrefillFromLineItems } from '.././data/EventHints'
import { Badge as BootstrapBadge } from 'react-bootstrap';

interface Tag {
  id: string;
  text: string;
}

export default function CreateEventModal({ show, onHide }: { show: boolean, onHide: () => void }) {

  const lineItems = useLineItems();
  const lineItemsDispatch = useLineItemsDispatch();

  const selectedLineItems = lineItems.filter(lineItem => lineItem.isSelected);
  const selectedLineItemIds = lineItems.filter(lineItem => lineItem.isSelected).map(lineItem => lineItem.id);
  // TODO: Make hints more robust with categories
  useEffect(() => {
    if (!show && selectedLineItems.length > 0) {
      const prefillSuggestion = getPrefillFromLineItems(selectedLineItems);
      if (prefillSuggestion !== null) {
        name.setCustomValue(prefillSuggestion.name)
        category.setCustomValue(prefillSuggestion.category)
      } else {
        name.setCustomValue(defaultNameCleanup(selectedLineItems[0].description))
      }
    } else if (!show) {
      name.setEmpty()
      category.setEmpty()
    }
  }, [selectedLineItems, show])

  const name = useField<string>("text", "" as string)
  const category = useField("select", "All" as string)
  const date = useField<string>("date", "" as string)
  const isDuplicateTransaction = useField<boolean>("checkbox", false)
  const [tags, setTags] = useState<Tag[]>([]);
  const [tagInput, setTagInput] = useState('');

  const disableSubmit = name.value === "" || category.value === "" || category.value === "All"

  const total = React.useMemo(() => {
    return selectedLineItems.reduce((prev, cur) => {
      if (!!isDuplicateTransaction.value) {
        return prev + cur.amount / 2;
      }
      return prev + cur.amount;
    }, 0);
  }, [selectedLineItems, isDuplicateTransaction]);

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
    setTags([])
    setTagInput('')
    isDuplicateTransaction.setCustomValue(false);
    onHide()
  }

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = {
        id: Math.random().toString(36).substring(2, 9),
        text: tagInput.trim()
      };
      setTags([...tags, newTag]);
      setTagInput('');
    }
  };

  const removeTag = (tagId: string) => {
    setTags(tags.filter(tag => tag.id !== tagId));
  };

  const createEvent = (name: FormField<string>, category: FormField<string>) => {
    var REACT_APP_API_ENDPOINT = String(process.env.REACT_APP_API_ENDPOINT);
    var newEvent = {
      "name": name.value,
      "category": category.value,
      "date": date.value,
      "line_items": selectedLineItemIds,
      "is_duplicate_transaction": isDuplicateTransaction.value,
      "tags": tags.map(tag => tag.text)
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
              <Form.Label>Tags:</Form.Label>
              <div className="d-flex flex-wrap gap-2 mb-2">
                {tags.map(tag => (
                  <BootstrapBadge
                    key={tag.id}
                    bg="primary"
                    className="d-flex align-items-center p-2"
                  >
                    {tag.text}
                    <span
                      onClick={() => removeTag(tag.id)}
                      style={{ marginLeft: '5px', cursor: 'pointer' }}
                    >
                      ×
                    </span>
                  </BootstrapBadge>
                ))}
              </div>
              <Form.Control
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagInputKeyDown}
                placeholder="Type a tag and press Enter"
              />
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
          <Stack className='me-auto' direction="horizontal" gap={3} style={{ width: '100%' }}>
            <Badge className="p-2" bg="secondary">Total: ${total}</Badge>
            <Button className="p-2 ms-auto" onClick={closeModal} variant="secondary">Cancel</Button>
            <Button className="p-2" onClick={() => createEvent(name, category)} variant="primary" disabled={disableSubmit}>Submit</Button>
          </Stack>
        </Modal.Footer>
      </Modal>
    </Fragment >
  );
}
