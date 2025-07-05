import React, { useState, useEffect, useRef } from "react";
import { Button, Modal, Spinner } from "react-bootstrap";
import { useDropzone } from "react-dropzone";
import { ArrowUpCircle } from "react-bootstrap-icons";
import { useParams } from "react-router-dom";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import annotationPlugin from 'chartjs-plugin-annotation';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  annotationPlugin
);

function VideoUpload() {
  const { sessionCode } = useParams();
  const [showModal, setShowModal] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedFilePath, setUploadedFilePath] = useState(null);
  const [canGenerateReport, setCanGenerateReport] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [predictionData, setPredictionData] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState(0);
  const [chartVisibleRange, setChartVisibleRange] = useState({ min: 0, max: 15 });
  const [videoFps, setVideoFps] = useState(30); // Default FPS, will be updated from API
  const videoRef = useRef(null);
  const chartRef = useRef(null);

  // Constants for time conversion (30 frames per chunk at variable FPS)
  const FRAMES_PER_CHUNK = 30;
  // Store SECONDS_PER_CHUNK in state since it depends on videoFps
  const [secondsPerChunk, setSecondsPerChunk] = useState(FRAMES_PER_CHUNK / videoFps);
  
  // Viewport width in seconds - how much of the graph is visible at once
  const VIEWPORT_WIDTH = 15; // 15 seconds visible at a time

  useEffect(() => {
    // Show the upload modal automatically when component mounts
    setShowModal(true);
  }, []);

  // Update SECONDS_PER_CHUNK when videoFps changes
  useEffect(() => {
    setSecondsPerChunk(FRAMES_PER_CHUNK / videoFps);
  }, [videoFps]);

  // Update chart visible range when current time changes
  useEffect(() => {
    if (videoDuration > 0 && currentTime > 0) {
      // Calculate new visible range - keep current time in the middle 1/3 of the viewport
      let newMin = Math.max(0, currentTime - VIEWPORT_WIDTH / 2);
      let newMax = newMin + VIEWPORT_WIDTH;
      
      // If max exceeds video duration, adjust both min and max
      if (newMax > videoDuration) {
        newMax = videoDuration;
        newMin = Math.max(0, newMax - VIEWPORT_WIDTH);
      }
      
      setChartVisibleRange({ min: newMin, max: newMax });
    }
  }, [currentTime, videoDuration]);

  const handleClose = (file) => {
    setShowModal(false);
    if (file) {
      setUploadedFile(file);
      setStatusMessage("Processing Data and Generating Report!");
    } else {
      setUploadedFile(null);
    }
  };

  const onDrop = (acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setUploadedFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: "video/*",
    multiple: false,
  });

  const uploadToServer = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("sessionCode", sessionCode);

    try {
      setStatusMessage("Uploading video...");
      const response = await fetch("http://localhost:8000/upload-video", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        setStatusMessage(`Upload failed: ${errorData.detail || response.statusText}`);
        return;
      }

      const data = await response.json();
      setUploadedFilePath(data.details.file_path);
      setCanGenerateReport(true);
      if (data.details.fps) {
        setVideoFps(parseFloat(data.details.fps));
      }
      setVideoUrl(`http://localhost:8000/video/${encodeURIComponent(data.details.file_path)}`);
      
      // If FPS is provided in the API response, update the state
      
      setStatusMessage("Video uploaded successfully! Click 'Generate Analysis Report' to proceed.");
    } catch (error) {
      console.error("Error uploading video:", error);
      setStatusMessage(`Upload error: ${error.message}`);
    }
  };

  const generateReport = async () => {
    if (!uploadedFilePath) return;

    try {
      setIsGeneratingReport(true);
      setStatusMessage("Generating analysis report... This may take a few minutes.");

      const reportResponse = await fetch(
        `http://localhost:8000/report?filePath=${encodeURIComponent(uploadedFilePath)}&sessionCode=${sessionCode}`,
        { method: "GET" }
      );

      if (!reportResponse.ok) {
        const errorData = await reportResponse.json();
        throw new Error(errorData.message || reportResponse.statusText);
      }

      const blob = await reportResponse.blob();
      const url = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = 'deception_analysis_report.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // After generating the report, fetch the prediction data
      await fetchPredictionData();
      
      setStatusMessage("Analysis complete! Report downloaded.");
    } catch (error) {
      setStatusMessage(`Report generation failed: ${error.message}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const fetchPredictionData = async () => {
    try {
      const response = await fetch("http://localhost:8000/prediction-data");
      if (!response.ok) {
        throw new Error("Failed to fetch prediction data");
      }
      const data = await response.json();
      if (data.status === "success") {
        // Process the data to adjust time values for correct display
        const processedData = data.data.map((item, index) => ({
          ...item,
          // Ensure we have numeric values 
          Chunk_Start_Time: parseFloat(item.Chunk_Start_Time),
          Chunk_End_Time: parseFloat(item.Chunk_End_Time),
          Time_Seconds: parseFloat(item.Time_Seconds),
          Deception_Score: parseFloat(item.Deception_Score),
          Confidence: parseFloat(item.Confidence),
          Binary_Prediction: parseInt(item.Binary_Prediction),
          // Add a VideoTime property that matches video playback time
          VideoTime: parseFloat(item.Chunk_Start_Time)
        }));
        
        setPredictionData(processedData);
        
        // Update FPS from the prediction data if available
        if (data.fps) {
          setVideoFps(parseFloat(data.fps));
        }
      } else {
        throw new Error(data.message || "Failed to get prediction data");
      }
    } catch (error) {
      console.error("Error fetching prediction data:", error);
      setStatusMessage(`Error loading prediction data: ${error.message}`);
    }
  };

  // Handle video metadata loaded - get duration
  const handleMetadataLoaded = () => {
    if (videoRef.current) {
      const duration = videoRef.current.duration;
      setVideoDuration(duration);
      // Initialize viewport to show first 15 seconds (or full video if shorter)
      setChartVisibleRange({ min: 0, max: Math.min(VIEWPORT_WIDTH, duration) });
    }
  };

  // Handle video time update
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  // Find the current data point based on video time
  const getCurrentDataPoint = () => {
    if (!predictionData || predictionData.length === 0) return null;
    
    // Find the chunk that contains the current time
    const matchingPoint = predictionData.find((item, index) => {
      const nextItem = predictionData[index + 1];
      // If we're at the last item, check if current time is within its chunk
      if (!nextItem) {
        return currentTime >= item.Chunk_Start_Time;
      }
      // Otherwise check if current time is between this chunk and the next
      return currentTime >= item.Chunk_Start_Time && currentTime < nextItem.Chunk_Start_Time;
    });
    
    return matchingPoint || predictionData[0]; // Default to first point if no match
  };

  // Get current chunk index
  const getCurrentChunkIndex = () => {
    if (!predictionData || predictionData.length === 0) return -1;
    
    return predictionData.findIndex((item, index) => {
      const nextItem = predictionData[index + 1];
      if (!nextItem) {
        // Last chunk - check if we're in its time range
        return currentTime >= item.Chunk_Start_Time;
      }
      return currentTime >= item.Chunk_Start_Time && currentTime < nextItem.Chunk_Start_Time;
    });
  };

  const currentDataPoint = getCurrentDataPoint();
  const currentChunkIndex = getCurrentChunkIndex();

  // Prepare chart data
  const chartData = {
    labels: predictionData ? predictionData.map(item => item.VideoTime) : [],
    datasets: [
      {
        label: 'Deception Score',
        data: predictionData ? predictionData.map(item => item.Deception_Score) : [],
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        pointRadius: predictionData 
          ? predictionData.map((item, index) => 
              index === currentChunkIndex ? 8 : 
              Math.abs(item.VideoTime - currentTime) < secondsPerChunk ? 5 : 2)
          : [],
        pointBackgroundColor: predictionData
          ? predictionData.map(item => 
              item.Binary_Prediction === 1 ? 'rgba(255, 0, 0, 0.8)' : 'rgba(0, 255, 0, 0.8)')
          : [],
        pointBorderColor: predictionData
          ? predictionData.map((item, index) => 
              index === currentChunkIndex ? '#000' : 'transparent')
          : [],
        pointBorderWidth: 2,
        tension: 0.2,
        stepped: 'before' // Makes the graph step at each chunk
      }
    ]
  };

  // Calculate the maximum time from prediction data
  const maxDataTime = predictionData ? 
    Math.max(...predictionData.map(item => item.Chunk_End_Time)) : 0;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Deception Analysis in Real-time',
        font: {
          size: 16
        }
      },
      tooltip: {
        callbacks: {
          title: function(context) {
            const item = predictionData[context[0].dataIndex];
            return `Time: ${item.VideoTime.toFixed(1)}s (Chunk ${context[0].dataIndex + 1})`;
          },
          label: function(context) {
            const dataPoint = predictionData[context.dataIndex];
            const label = [];
            label.push(`Deception Score: ${context.parsed.y.toFixed(4)}`);
            label.push(`Prediction: ${dataPoint.Binary_Prediction === 0 ? 'Truthful' : 'Deceptive'}`);
            label.push(`Confidence: ${(dataPoint.Confidence * 100).toFixed(2)}%`);
            return label;
          }
        }
      },
      annotation: {
        annotations: currentTime > 0 ? {
          line1: {
            type: 'line',
            xMin: currentTime,
            xMax: currentTime,
            borderColor: 'black',
            borderWidth: 2,
            label: {
              display: true,
              content: 'Current',
              position: 'start'
            }
          },
          threshold: {
            type: 'line',
            yMin: 0.5,
            yMax: 0.5,
            borderColor: 'rgba(255, 0, 0, 0.5)',
            borderWidth: 2,
            borderDash: [6, 4],
            label: {
              display: true,
              content: 'Threshold',
              position: 'end',
              backgroundColor: 'rgba(255, 0, 0, 0.3)',
              color: 'black',
              font: {
                size: 10
              }
            }
          }
        } : {}
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Video Time (seconds)'
        },
        min: chartVisibleRange.min,
        max: chartVisibleRange.max,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 10
        }
      },
      y: {
        title: {
          display: true,
          text: 'Deception Score'
        },
        min: 0,
        max: 1,
        grid: {
          color: function(context) {
            if (context.tick.value === 0.5) {
              return 'rgba(255, 0, 0, 0.3)';
            }
            return 'rgba(0, 0, 0, 0.1)';
          },
          lineWidth: function(context) {
            if (context.tick.value === 0.5) {
              return 2;
            }
            return 1;
          }
        }
      }
    },
    animation: {
      duration: 0 // disables animation for performance
    },
    interaction: {
      mode: 'index',
      intersect: false
    }
  };

  // Add custom controls to zoom in/out and reset the visible range
  const zoomIn = () => {
    const duration = Math.max(chartVisibleRange.max - chartVisibleRange.min, 2);
    const center = (chartVisibleRange.min + chartVisibleRange.max) / 2;
    const newDuration = Math.max(2, duration / 1.5);
    setChartVisibleRange({
      min: Math.max(0, center - newDuration / 2),
      max: Math.min(videoDuration, center + newDuration / 2)
    });
  };

  const zoomOut = () => {
    const duration = chartVisibleRange.max - chartVisibleRange.min;
    const center = (chartVisibleRange.min + chartVisibleRange.max) / 2;
    const newDuration = Math.min(videoDuration, duration * 1.5);
    setChartVisibleRange({
      min: Math.max(0, center - newDuration / 2),
      max: Math.min(videoDuration, center + newDuration / 2)
    });
  };

  const resetZoom = () => {
    setChartVisibleRange({ min: 0, max: Math.min(VIEWPORT_WIDTH, videoDuration) });
  };

  const jumpToCurrent = () => {
    // Center the view on the current time
    const halfViewport = VIEWPORT_WIDTH / 2;
    let newMin = Math.max(0, currentTime - halfViewport);
    let newMax = Math.min(videoDuration, currentTime + halfViewport);
    
    // Adjust if we're near the end
    if (newMax > videoDuration) {
      newMax = videoDuration;
      newMin = Math.max(0, newMax - VIEWPORT_WIDTH);
    }
    
    setChartVisibleRange({ min: newMin, max: newMax });
  };

  const handleUploadClick = async () => {
    if (uploadedFile) {
      await uploadToServer(uploadedFile);
      setShowModal(false);
    }
  };

  const openUploadModal = () => {
    setShowModal(true);
  };

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12 mt-4">
          <h3 className="text-center mb-4">Session: {sessionCode}</h3>
          
          {!uploadedFile && !showModal && (
            <div className="text-center mb-4">
              <Button variant="primary" onClick={openUploadModal}>
                Upload Video
              </Button>
            </div>
          )}

          {/* Main Content Area with Status and Generate Report Button */}
          <div className="d-flex flex-column align-items-center justify-content-center">
            {statusMessage && !predictionData && (
              <div className="text-center">
                <h5>{statusMessage}</h5>
                {canGenerateReport && !isGeneratingReport && (
                  <Button 
                    variant="success" 
                    onClick={generateReport} 
                    className="mt-3"
                    style={{ fontSize: "1.1rem", padding: "0.5rem 1.5rem" }}
                  >
                    Generate Analysis Report
                  </Button>
                )}
                {isGeneratingReport && (
                  <div className="d-flex align-items-center justify-content-center mt-3">
                    <Spinner animation="border" role="status" className="me-2" />
                    <span>Generating report...</span>
                  </div>
                )}
              </div>
            )}

            {/* Video Player and Graph Section */}
            {videoUrl && predictionData && (
              <div className="container mt-4">
                <div className="row">
                  <div className="col-md-6">
                    <div className="card">
                      <div className="card-header d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">Video Player</h5>
                        {currentDataPoint && (
                          <div className="d-flex align-items-center">
                            <div className={`badge ${currentDataPoint.Binary_Prediction === 0 ? 'bg-success' : 'bg-danger'} me-2`}
                              style={{fontSize: '1rem', padding: '0.5rem'}}>
                              {currentDataPoint.Binary_Prediction === 0 ? 'Truthful' : 'Deceptive'}
                            </div>
                            <div className="small text-muted">
                              Confidence: {(currentDataPoint.Confidence * 100).toFixed(1)}%
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="card-body">
                        <video
                          ref={videoRef}
                          src={videoUrl}
                          controls
                          width="100%"
                          onTimeUpdate={handleTimeUpdate}
                          onLoadedMetadata={handleMetadataLoaded}
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="col-md-6">
                    <div className="card">
                      <div className="card-header d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">Real-time Deception Analysis</h5>
                        <div className="btn-group btn-group-sm">
                          <Button variant="outline-secondary" onClick={zoomIn} title="Zoom In">
                            <i className="bi bi-zoom-in">+</i>
                          </Button>
                          <Button variant="outline-secondary" onClick={zoomOut} title="Zoom Out">
                            <i className="bi bi-zoom-out">-</i>
                          </Button>
                          <Button variant="outline-secondary" onClick={resetZoom} title="Reset Zoom">
                            <i className="bi bi-arrows-fullscreen">↺</i>
                          </Button>
                          <Button variant="outline-primary" onClick={jumpToCurrent} title="Jump to Current Time">
                            <i className="bi bi-cursor">➡</i>
                          </Button>
                        </div>
                      </div>
                      <div className="card-body">
                        <div style={{ height: '300px' }}>
                          <Line ref={chartRef} data={chartData} options={chartOptions} />
                        </div>
                        <div className="mt-3">
                          <div className="d-flex justify-content-between align-items-center">
                            <div>
                              <span className="d-inline-block me-2" style={{ width: '15px', height: '15px', backgroundColor: 'rgba(0, 255, 0, 0.8)', borderRadius: '50%' }}></span>
                              <span className="small">Truthful</span>
                            </div>
                            <div>
                              <span className="d-inline-block me-2" style={{ width: '15px', height: '15px', backgroundColor: 'rgba(255, 0, 0, 0.8)', borderRadius: '50%' }}></span>
                              <span className="small">Deceptive</span>
                            </div>
                            <div>
                              <span className="fw-bold small">Current Time:</span>
                              <span className="small ms-2">{currentTime.toFixed(2)}s</span>
                              {currentDataPoint && (
                                <span className="small ms-2">(Chunk {currentChunkIndex + 1})</span>
                              )}
                            </div>
                          </div>
                        </div>
                        {videoDuration > 0 && (
                          <div className="small text-muted mt-2 text-center">
                            Video duration: {videoDuration.toFixed(2)}s | Data points: {predictionData?.length || 0} | 
                            Viewing: {chartVisibleRange.min.toFixed(1)}s - {chartVisibleRange.max.toFixed(1)}s
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="col-12 mt-3">
                    <div className="card">
                      <div className="card-body py-2">
                        <div className="d-flex justify-content-between align-items-center">
                          <div className="small text-muted">
                            Video FPS: {videoFps} | Chunk size: {FRAMES_PER_CHUNK} frames ({secondsPerChunk.toFixed(2)} seconds)
                          </div>
                          <div className="small text-muted">
                            <button className="btn btn-sm btn-outline-secondary" onClick={generateReport}>
                              Regenerate Report
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Video Upload Modal */}
      <Modal show={showModal} onHide={() => handleClose(uploadedFile)} centered size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Upload your video file</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div
            {...getRootProps()}
            className="border border-dashed p-5 text-center position-relative d-flex justify-content-center align-items-center"
            style={{ cursor: "pointer", borderRadius: "8px", minHeight: "300px", position: "relative" }}
          >
            <input {...getInputProps()} />
            {!uploadedFile && (
              <div className="position-absolute text-muted d-flex flex-column align-items-center" style={{ opacity: 0.3 }}>
                <ArrowUpCircle size={100} />
                <p>Drag & drop your video here or click to upload</p>
              </div>
            )}
            {uploadedFile && <p className="mt-4">{uploadedFile.name}</p>}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => handleClose(null)}>
            Cancel
          </Button>
          <Button variant="success" onClick={handleUploadClick} disabled={!uploadedFile}>
            Upload!
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default VideoUpload; 