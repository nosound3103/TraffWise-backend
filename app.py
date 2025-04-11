from middleware import setup_cors
from typing import Literal, List, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import sys
import time
import cv2
import yaml
import os
from pathlib import Path
from datetime import datetime

from api.source.operators.controller import Controller

BASE_DIR = Path(__file__).parent.absolute()
sys.path.append(str(BASE_DIR))

# Create captures directory if it doesn't exist
CAPTURES_DIR = BASE_DIR / "captures"
CAPTURES_DIR.mkdir(exist_ok=True)
print(f"Captures will be saved to: {CAPTURES_DIR}")


class ModelRequest(BaseModel):
    model_type: Literal["yolo11", "rtdetrv2", "faster_rcnn"]


class CameraRequest(BaseModel):
    camera_id: Literal["1", "2"]


class CaptureRequest(BaseModel):
    camera_id: Literal["1", "2"]
    model_type: Literal["yolo11", "rtdetrv2", "faster_rcnn"]


class Violation(BaseModel):
    id: str
    plate: str
    type: str
    status: str
    date: str
    location: str
    evidence: str
    speed: Optional[str] = None
    signalTime: Optional[str] = None
    laneDetails: Optional[str] = None


class RewindRequest(BaseModel):
    seconds: int = 10


class AnnotationToggleRequest(BaseModel):
    show_annotations: bool


class SystemParameters(BaseModel):
    speedEstimationEnabled: bool = True
    speedLimit: float = 60
    overspeedBuffer: float = 5
    maxHistorySeconds: float = 3.0

    redLightDetectionEnabled: bool = True
    maxTrackRLV: int = 50

    wrongLaneDetectionEnabled: bool = True
    angleThreshold: float = 90
    straightThreshold: float = 30
    dotThreshold: float = -0.5
    toleranceTime: float = 3

    confidenceThreshold: float = 0.5
    nmsThreshold: float = 0.45
    maxAge: int = 15


app = FastAPI()
# app.add_middleware(LogMiddleware)
setup_cors(app)

with open("api\configs\pipeline.yml", "r") as file:
    config = yaml.safe_load(file)

controller = Controller(config)


@app.post("/set_model")
async def set_model(request: ModelRequest):
    """Sets the model to be used for detection."""
    try:
        controller.switch_model(request.model_type)
        return {"status": "success", "model": request.model_type}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to switch model: {str(e)}")


@app.post("/set_camera")
async def set_camera(request: CameraRequest):
    """Sets the camera to be used for video feed."""
    try:
        controller.switch_camera(request.camera_id)
        return {"status": "success", "camera_id": request.camera_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to switch camera: {str(e)}")


@app.post("/capture_frame")
async def capture_frame(request: CaptureRequest):
    """Captures a single frame from the current video feed and saves it."""
    try:
        # Get current frame without switching camera or model
        frame = controller.get_current_frame()

        if frame is None:
            raise HTTPException(
                status_code=400, detail="No frame available to capture")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cam{request.camera_id}_{request.model_type}_{timestamp}.jpg"
        filepath = str(CAPTURES_DIR / filename)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Debug info
        print(f"Saving capture to: {filepath}")

        # Save the frame
        success = cv2.imwrite(filepath, frame)

        if not success:
            raise HTTPException(
                status_code=500, detail=f"Failed to write image to {filepath}")

        return {
            "status": "success",
            "filename": filename,
            "path": filepath
        }

    except Exception as e:
        print(f"Error in capture_frame: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to capture frame: {str(e)}")


@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        content=controller.yield_from_video(),
        media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/reset")
async def reset_controller(request: dict = None):
    """Reset the controller to initial state."""
    try:
        camera_id = request.get("camera_id") if request else None
        result = controller.reset_state(camera_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset controller: {str(e)}")


@app.post("/toggle_pause")
async def toggle_pause():
    """Toggles the pause state of the video feed."""
    try:
        is_paused = controller.toggle_pause()
        return {"status": "success", "paused": is_paused}
    except Exception as e:
        print(f"Error toggling pause: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle pause: {str(e)}")


@app.post("/toggle_annotations")
async def toggle_annotations(request: AnnotationToggleRequest):
    """Toggles the display of annotations on the video feed."""
    try:
        result = controller.toggle_annotations(request.show_annotations)
        return {"status": "success", "show_annotations": result["show_annotations"]}
    except Exception as e:
        print(f"Error toggling annotations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to toggle annotations: {str(e)}")


@app.post("/api/parameters")
async def update_parameters(params: SystemParameters):
    try:
        controller.update_parameters(params.model_dump())
        return {"success": True, "message": "Parameters updated successfully"}
    except Exception as e:
        print(f"Error updating parameters: {str(e)}")  # Add this line
        raise HTTPException(
            status_code=500, detail=f"Failed to update parameters: {str(e)}")


# Add API endpoints for violations
@app.get("/api/violations", response_model=List[dict])
async def get_violations(limit: Optional[int] = None):
    """Get all traffic violations"""
    try:
        violations = controller.violation_manager.get_violations(limit)
        return violations
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch violations: {str(e)}")


@app.get("/api/violations/{violation_id}")
async def get_violation(violation_id: str):
    """Get a specific violation by ID"""
    try:
        violation = controller.violation_manager.get_violation(violation_id)
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        return violation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch violation: {str(e)}")
