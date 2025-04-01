from middleware import setup_cors
from typing import Literal
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import sys
import time
import cv2
import yaml
import os
from pathlib import Path

from api.source.operators.controller import Controller

BASE_DIR = str(Path(__file__).parent)
sys.path.append(BASE_DIR)


class ModelRequest(BaseModel):
    model_type: Literal["yolo11", "rtdetrv2", "faster_rcnn"]


class CameraRequest(BaseModel):
    camera_id: Literal["1", "2"]


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
