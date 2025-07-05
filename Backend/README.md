# FastAPI Server

A Deception Detection System API built with FastAPI.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Server

Start the server with:
```
python app.py
```

Or using uvicorn directly:
```
uvicorn app:app --reload
```

The server will run at `http://localhost:8000`

## API Endpoints

- **GET /ping**: Health check endpoint that returns a pong response
- **POST /upload-video**: Upload a video file for deception detection analysis
- **GET /docs**: Swagger UI for API documentation

## Testing the API

### Health Check
```
curl http://localhost:8000/ping
```

Expected response:
```json
{"status":"ok","message":"pong"}
```

### Upload Video
```
curl -X POST http://localhost:8000/upload-video \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/video.mp4" \
  -F "description=Sample video for analysis"
```

Expected response:
```json
{
  "status": "success",
  "message": "Video uploaded successfully",
  "details": {
    "filename": "20230615_123456_a1b2c3d4.mp4",
    "original_filename": "video.mp4",
    "content_type": "video/mp4",
    "description": "Sample video for analysis",
    "file_path": "uploads/20230615_123456_a1b2c3d4.mp4",
    "uploaded_at": "20230615_123456"
  }
}
``` 