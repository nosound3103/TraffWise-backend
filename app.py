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
from schemas.schemas import (
    ModelRequest,
    CameraRequest,
    CaptureRequest,
    Violation,
    AnnotationToggleRequest,
    SystemParameters,
)
from middleware import setup_cors

BASE_DIR = Path(__file__).parent.absolute()
sys.path.append(str(BASE_DIR))

CAPTURES_DIR = BASE_DIR / "captures"
CAPTURES_DIR.mkdir(exist_ok=True)
print(f"Captures will be saved to: {CAPTURES_DIR}")


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
        updated_config = controller.switch_camera(request.camera_id)
        return {
            "status": "success",
            "camera_id": request.camera_id,
            "config": updated_config
        }
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

        global controller

        with open("api\configs\pipeline.yml", "r") as file:
            config = yaml.safe_load(file)

        controller = Controller(config)

        return {"status": "success", "message": "Controller reset to initial state"}
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
async def update_parameters(params: dict):
    try:
        controller.update_parameters(params)

        # Get updated config to verify changes
        updated_config = controller.get_system_config()
        return {
            "success": True,
            "message": "Parameters updated successfully",
            "config": updated_config
        }
    except Exception as e:
        print(f"Error updating parameters: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update parameters: {str(e)}")


@app.post("/api/camera/{camera_id}/parameters")
async def update_camera_parameters(camera_id: str, request: Request):
    """Update parameters for specific camera"""
    try:
        body = await request.json()
        settings = body.get("settings")

        if not settings:
            raise HTTPException(
                status_code=400, detail="Settings not provided")

        controller.update_parameters(settings)

        return {
            "status": "success",
            "camera_id": camera_id,
            "config": settings
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update camera parameters: {str(e)}"
        )


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


@app.get("/api/camera/{camera_id}/config")
async def get_camera_config(camera_id: str):
    """Get configuration for specific camera"""
    try:
        config = controller.get_system_config()
        if config is None:
            raise HTTPException(
                status_code=404, detail="Configuration not found")
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get config: {str(e)}")
