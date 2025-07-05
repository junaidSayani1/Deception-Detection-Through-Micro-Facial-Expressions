import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Modal, Button, Form } from "react-bootstrap";
import VideoUpload from "./VideoUpload";

function App() {
  // State for Create Session
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [sessionCode, setSessionCode] = useState("");
  
  // State for Join Session
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinSessionCode, setJoinSessionCode] = useState("");

  // Function to generate a random session code
  const generateSessionCode = () => {
    return Math.floor(100000 + Math.random() * 900000).toString();
  };

  // Open create session modal with a new session code
  const handleCreateSession = () => {
    setSessionCode(generateSessionCode());
    setShowCreateModal(true);
  };

  // Close create session modal
  const handleCreateClose = () => {
    setShowCreateModal(false);
  };
  
  // Open join session modal
  const handleJoinSession = () => {
    setShowJoinModal(true);
  };
  
  // Close join session modal
  const handleJoinClose = () => {
    setShowJoinModal(false);
  };
  
  // Handle join session
  const handleJoinClick = () => {
    if (joinSessionCode.trim()) {
      handleJoinClose();
      window.location.href = `/video-upload/${joinSessionCode}`;
    }
  };

  return (
    <Router>
      <div className="d-flex flex-column vh-100">
        {/* Navbar */}
        <nav className="navbar navbar-dark bg-dark px-3">
          <span className="navbar-brand">Lie To Us</span>
        </nav>

        <Routes>
          <Route path="/" element={
            <div className="d-flex flex-grow-1">
              {/* Sidebar */}
              <div className="bg-light p-3 border-end" style={{ width: "250px" }}>
                <h4>Session Control</h4>
                <button onClick={handleCreateSession} className="btn btn-primary w-100 mb-2 text-decoration-none">Create Session</button>
                <button onClick={handleJoinSession} className="btn btn-success w-100 text-decoration-none">Join Session</button>
              </div>

              {/* Main Content */}
              <div className="flex-grow-1 d-flex align-items-center justify-content-center">
                <p className="text-muted fs-5">Welcome! Select an option to proceed.</p>
              </div>
            </div>
          } />
          <Route path="/video-upload/:sessionCode" element={<VideoUpload />} />
        </Routes>

        {/* Modal for session creation confirmation */}
        <Modal show={showCreateModal} onHide={handleCreateClose} centered>
          <Modal.Header closeButton>
            <Modal.Title>Confirm Session Creation</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p>Your session code: <strong>{sessionCode}</strong></p>
            <p>Are you sure you want to continue?</p>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCreateClose}>No</Button>
            <Button variant="primary" onClick={() => {
              handleCreateClose();
              // Redirect to video upload page with session code
              window.location.href = `/video-upload/${sessionCode}`;
            }}>Yes</Button>
          </Modal.Footer>
        </Modal>
        
        {/* Modal for join session */}
        <Modal show={showJoinModal} onHide={handleJoinClose} centered>
          <Modal.Header closeButton>
            <Modal.Title>Join Session</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group>
              <Form.Label>Enter session code to join</Form.Label>
              <Form.Control
                type="text"
                value={joinSessionCode}
                onChange={(e) => setJoinSessionCode(e.target.value)}
                placeholder="Session Code"
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleJoinClose}>Cancel</Button>
            <Button variant="primary" onClick={handleJoinClick}>Join</Button>
          </Modal.Footer>
        </Modal>
      </div>
    </Router>
  );
}

export default App;
