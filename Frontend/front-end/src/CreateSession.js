import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Modal } from "react-bootstrap";

function CreateSession() {
  const [showModal, setShowModal] = useState(false);
  const [sessionCode, setSessionCode] = useState("");

  // Function to generate a random session code
  const generateSessionCode = () => {
    return Math.floor(100000 + Math.random() * 900000).toString();
  };

  // Open modal with a new session code
  const handleCreateSession = () => {
    setSessionCode(generateSessionCode());
    setShowModal(true);
  };

  // Close modal
  const handleClose = () => {
    setShowModal(false);
  };

  return (
    <div>
      <Button className="list-group-item list-group-item-action" onClick={handleCreateSession}>
        Create Session
      </Button>

      {/* Modal for session confirmation */}
      <Modal show={showModal} onHide={handleClose} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Session Creation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Your session code: <strong>{sessionCode}</strong></p>
          <p>Are you sure you want to continue?</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>No</Button>
          <Button variant="primary" onClick={handleClose}>Yes</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default CreateSession;
