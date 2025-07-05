from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from datetime import datetime
import uuid
from run_prediction import DeceptionDetector
from fpdf import FPDF
from fastapi.responses import FileResponse, JSONResponse
import matplotlib.pyplot as plt
import traceback
import pandas as pd
from Model.ReportGenerator import ReportGenerator
import cv2

app = FastAPI(title="Deception Detection System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "Videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create reports directory if it doesn't exist
REPORTS_DIR = "Reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

deceptionDetector = DeceptionDetector()
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

@app.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
):
    # Validate file content type
    content_type = file.content_type
    print("The content type is: ", content_type)
    if not content_type or not content_type.startswith('video/'):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Only video files are accepted."
        )
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(file.filename)[1]
    new_filename = f"{timestamp}_{file_id}{file_extension}"
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, new_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    filePath = file_path
    cap = cv2.VideoCapture(filePath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return {
        "status": "success",
        "message": "Video uploaded successfully",
        "details": {
            "filename": new_filename,
            "original_filename": file.filename,
            "content_type": content_type,
            "file_path": file_path,
            "fps": fps,
            "uploaded_at": timestamp
        }
    }

@app.get("/report")
async def get_report(filePath: str):
    try:
        # Get video frame rate using OpenCV
        cap = cv2.VideoCapture(filePath)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        print(f"Video frame rate: {fps} FPS")
        
        results = deceptionDetector.process_video(filePath)
        
        # Use the ReportGenerator class to create the PDF report
        report_generator = ReportGenerator(reports_dir=REPORTS_DIR)
        report_path = report_generator.generate_report(
            file_path=filePath,
            results=results,
            analysis_image_path="deception_analysis.png"
        )
        
        # Get the report filename from the path
        report_filename = os.path.basename(report_path)
        # report_filename="deception_report_20250501_023329.pdf"
        # Return the PDF file directly
        return FileResponse(
            path="Reports/" + report_filename,
            filename=report_filename,
            media_type="application/pdf"
        )
    except Exception as e:
        print("An error occurred: ", e)
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.get("/prediction-data")
async def get_prediction_data():
    try:
        if os.path.exists("prediction_results.csv"):
            # Read the CSV file
            prediction_data = pd.read_csv("prediction_results.csv")
            
            # Convert to dictionary format
            data_dict = prediction_data.to_dict(orient='records')
            
            return JSONResponse(content={"status": "success", "data": data_dict})
        else:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Prediction data not found. Run a report first."}
            )
    except Exception as e:
        print("An error occurred: ", e)
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/video/{video_path:path}")
async def get_video(video_path: str):
    try:
        # The video_path might be a full path or just a filename
        # First check if it's a relative path within the Videos directory
        video_absolute_path = os.path.join(UPLOAD_DIR, os.path.basename(video_path))
        
        # If not found in the Videos directory, try the full path
        if not os.path.exists(video_absolute_path):
            video_absolute_path = video_path
            
            # Security check: Ensure we're not accessing files outside allowed directories
            # Convert to absolute paths for comparison
            videos_abs_path = os.path.abspath(UPLOAD_DIR)
            requested_abs_path = os.path.abspath(video_absolute_path)
            
            # Only allow access if the file is within the Videos directory
            if not requested_abs_path.startswith(videos_abs_path) and os.path.exists(video_absolute_path):
                return JSONResponse(
                    status_code=403,
                    content={"status": "error", "message": "Access to the requested file is forbidden"}
                )
        
        # Check if the file exists
        if not os.path.exists(video_absolute_path):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Video file not found: {video_path}"}
            )
        
        # Return the video file with the correct media type
        file_extension = os.path.splitext(video_absolute_path)[1].lower()
        media_type = "video/mp4"  # Default media type
        
        # Map common video extensions to media types
        if file_extension == ".webm":
            media_type = "video/webm"
        elif file_extension == ".ogg" or file_extension == ".ogv":
            media_type = "video/ogg"
        elif file_extension == ".mov":
            media_type = "video/quicktime"
        elif file_extension == ".avi":
            media_type = "video/x-msvideo"
        elif file_extension == ".wmv":
            media_type = "video/x-ms-wmv"
        
        return FileResponse(
            path=video_absolute_path,
            media_type=media_type
        )
    except Exception as e:
        print("An error occurred serving the video: ", e)
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
