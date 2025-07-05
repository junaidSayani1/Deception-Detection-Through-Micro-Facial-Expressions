import React, { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

function JoinSession() {
  const [sessionCode, setSessionCode] = useState("");
  const navigate = useNavigate();

  const handleJoinClick = () => {
    if (sessionCode.trim()) {
      // Navigate to the VideoUpload component with the session code as a parameter
      navigate(`/video-upload/${sessionCode}`);
    }
  };

  return (
    <div className="d-flex">
      {/* Simplified Sidebar */}
      <div className="bg-success p-4 text-white" style={{ width: "250px" }}>
        <h5>Enter session code to join</h5>
        <div className="d-flex flex-column">
          <Form.Control
            type="text"
            value={sessionCode}
            onChange={(e) => setSessionCode(e.target.value)}
            placeholder="Session Code"
            className="mb-2"
          />
          <Button variant="primary" onClick={handleJoinClick}>Join</Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-grow-1 d-flex flex-column align-items-center justify-content-center">
        <h4>Join a Deception Detection Session</h4>
        <p className="text-muted">Enter your session code and click "Join" to continue</p>
      </div>
    </div>
  );
}

export default JoinSession;
