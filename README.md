# TraffWise Backend

TraffWise Backend is a comprehensive traffic violation detection system built with FastAPI and Computer Vision technologies. It provides a robust API for real-time video processing, vehicle detection, and traffic rule enforcement monitoring.

## Features

- **Multi-Model Support**: Dynamically switch between YOLOv11, RT-DETRv2, and Faster R-CNN detection models.
- **Real-time Video Processing**: Stream processed video feeds with annotation overlays.
- **Violation Detection**: Built-in logic for detecting various traffic violations:
  - Speed Limit Violations
  - Red Light Infractions
  - Wrong Lane Usage
- **Camera Management**: Support for multiple camera feeds and dynamic camera switching.
- **System Configuration**: Real-time updates to system parameters like speed limits, tolerances, and detection thresholds.
- **OCR Integration**: License plate recognition and processing capabilities.
- **Capture System**: On-demand frame capturing for evidence and debugging.

## Prerequisites

- Python 3.8+
- CUDA-enabled GPU (recommended for real-time performance)
- OpenCV compatible camera or video stream

## Installation

1. Install the required dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Start the development server using the provided runner or directly with uvicorn:

```bash
python server.py
```

Or:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

The server will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

### System Control

- `POST /set_model`: Switch the active object detection model. Supported inputs: `yolo11`, `rtdetrv2`, `faster_rcnn`.
- `POST /set_camera`: Change the active camera source.
- `GET /video_feed`: Stream the processed video feed (MJPEG).
- `POST /toggle_pause`: Pause or resume the video processing loop.
- `POST /toggle_annotations`: Enable or disable visual detection overlays.
- `POST /reset`: Reset the controller to its initial state.

### Traffic Violations

- `GET /api/violations`: Retrieve a list of detected traffic violations.
- `GET /api/violations/{violation_id}`: Retrieve detailed information for a specific violation.

### Configuration

- `POST /api/parameters`: Update global system parameters (e.g., `speedLimit`, `redLightDetectionEnabled`, `wrongLaneDetectionEnabled`).
- `POST /api/camera/{camera_id}/parameters`: Update parameters specific to a camera.
- `GET /api/camera/{camera_id}/config`: Get the current configuration for a camera.

### Testing and Utilities

- `POST /capture_frame`: Capture and save the current frame from the video feed.
- `POST /api/test/ocr`: Upload an image to test the License Plate Recognition (OCR) module.
- `POST /api/test/pipeline`: Upload an image to run and test the full detection pipeline.

## Configuration

The application pipeline is configured via `api/configs/pipeline.yml`. This file defines the initialization parameters for the detection engines and logic controllers.

System parameters such as speed calculation buffers, angular thresholds for wrong-way detection, and confidence levels can be adjusted dynamically through the API or defined in the schemas.
