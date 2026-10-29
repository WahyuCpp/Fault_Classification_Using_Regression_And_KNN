"""MONTREAL-VT Motor Condition Monitoring Web Application.

FastAPI Backend with Real-Time WebSockets, Signal Processing, and ML Classification.
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config.main_config import (
    BASE_DIR,
    CLEANED_DATA_DIR,
    DEMO_MODE,
    MACHINE_CONFIG,
    PROCESSED_DATA_DIR,
)
from src.database.connection import get_db_status
from src.database.repository import ReadingRepository
from src.ml.model_utils import get_all_models_metadata
from src.ml.train_all_models import train_and_compare_all
from src.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline
from src.services.monitoring_service import MonitoringService
from src.services.replay_service import ReplayService
from src.utils.logger import get_logger

logger = get_logger("app", "application.log")

# Core Application Services — created before lifespan so all routes can reference them
monitoring_service = MonitoringService()
replay_service = ReplayService(monitoring_service=monitoring_service)
db_repo = ReadingRepository()


# --- Lifespan Management (replaces deprecated @app.on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup → yield → shutdown pattern required by Starlette ≥ 0.21 / FastAPI ≥ 0.93."""
    logger.info("MONTREAL-VT Web Application starting up...")
    if DEMO_MODE:
        replay_service.start()
        logger.info("Demo Mode active: Started simulated replay.")
    yield
    logger.info("Application shutting down...")
    replay_service.stop()
    monitoring_service.shutdown()


app = FastAPI(
    title="MONTREAL-VT Motor Condition Monitoring",
    description="Real-time condition monitoring, vibration DSP, and ML fault classification",
    version="1.0.0",
    lifespan=lifespan,
)

# Static files & Jinja2 templates
web_dir = BASE_DIR / "web"
app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(web_dir / "templates"))


# --- HTML Page Routes ---
@app.get("/", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"active_page": "dashboard", "machine": MACHINE_CONFIG},
    )


@app.get("/database", response_class=HTMLResponse)
async def page_database(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="database.html",
        context={"active_page": "database", "machine": MACHINE_CONFIG},
    )


@app.get("/datasets", response_class=HTMLResponse)
async def page_datasets(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="datasets.html",
        context={"active_page": "datasets", "machine": MACHINE_CONFIG},
    )


@app.get("/models", response_class=HTMLResponse)
async def page_models(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="models.html",
        context={"active_page": "models", "machine": MACHINE_CONFIG},
    )


# --- WebSocket Real-Time Stream ---
@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    """Continuous high-frequency WebSocket stream delivering DSP & ML packets."""
    await websocket.accept()
    logger.info("WebSocket client connected: %s", websocket.client)
    try:
        while True:
            # Generate processed packet from latest ring buffer window
            packet = monitoring_service.process_latest()
            await websocket.send_json(packet)
            # Stream at ~12-15 packets/second for fluid oscilloscope display
            await asyncio.sleep(0.075)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.warning("WebSocket exception: %s", e)


# --- REST API Endpoints ---
@app.get("/api/status")
async def get_system_status():
    """Return comprehensive system health and configuration status."""
    return {
        "demo_mode": DEMO_MODE,
        "machine": MACHINE_CONFIG,
        "database": get_db_status(),
        "replay": replay_service.get_status(),
        "dsp": {
            "window_size": monitoring_service.current_window_size,
            "fft_window": monitoring_service.current_fft_window,
            "sampling_rate": monitoring_service.sampling_rate,
            "active_ml_model": monitoring_service.predictor.model_name,
        },
    }


@app.get("/api/data/latest")
async def get_latest_data_packet():
    """Poll latest processed metrics."""
    return monitoring_service.process_latest()


class ReplayControlRequest(BaseModel):
    action: str  # 'start', 'pause', 'resume', 'stop', 'reset', 'speed', 'loop', 'load_dataset'
    speed: Optional[str] = None
    loop: Optional[bool] = None
    file_path: Optional[str] = None


@app.post("/api/control/replay")
async def control_replay(req: ReplayControlRequest):
    """Handle continuous simulation replay commands."""
    action = req.action.lower()
    if action == "start":
        replay_service.start()
    elif action == "pause":
        replay_service.pause()
    elif action == "resume":
        replay_service.resume()
    elif action == "stop":
        replay_service.stop()
    elif action == "reset":
        replay_service.reset()
    elif action == "speed" and req.speed:
        replay_service.set_speed(req.speed)
    elif action == "loop" and req.loop is not None:
        replay_service.set_loop(req.loop)
    elif action == "load_dataset" and req.file_path:
        success = replay_service.load_dataset(req.file_path)
        if success:
            replay_service.start()
        return {"success": success, "active_file": req.file_path}

    return {"success": True, "status": replay_service.get_status()}


class DspControlRequest(BaseModel):
    window_size: Optional[int] = None
    fft_window: Optional[str] = None
    ml_model: Optional[str] = None


@app.post("/api/control/dsp")
async def control_dsp(req: DspControlRequest):
    """Update window length, FFT window function, or active ML classifier dynamically."""
    if req.window_size is not None:
        monitoring_service.set_window_size(req.window_size)
    if req.fft_window is not None:
        monitoring_service.set_fft_window_function(req.fft_window)
    if req.ml_model is not None:
        monitoring_service.set_active_ml_model(req.ml_model)

    return {
        "window_size": monitoring_service.current_window_size,
        "fft_window": monitoring_service.current_fft_window,
        "ml_model": monitoring_service.predictor.model_name,
    }


@app.get("/api/datasets")
async def list_available_datasets():
    """List all available datasets in cleaned and processed repositories."""
    import pandas as pd
    datasets = []
    active_path = str(replay_service.active_file_path) if replay_service.active_file_path else ""

    for search_dir in [PROCESSED_DATA_DIR, CLEANED_DATA_DIR]:
        for csv_file in sorted(search_dir.rglob("*.csv")):
            try:
                # Fast sample read to get row count and columns
                df = pd.read_csv(csv_file, nrows=10)
                # Count full rows efficiently
                with open(csv_file, "rb") as f:
                    row_count = sum(1 for _ in f) - 1

                # Condition folder name
                condition = csv_file.parent.name
                fault_code = str(df.get("fault_label", ["A"])[0]) if "fault_label" in df.columns else "A"
                fs = 1500.0
                duration_sec = row_count / fs if fs > 0 else 0.0

                datasets.append({
                    "file_name": csv_file.name,
                    "file_path": str(csv_file.resolve()),
                    "condition": condition,
                    "fault_code": fault_code,
                    "row_count": row_count,
                    "sampling_rate_hz": fs,
                    "duration_sec": duration_sec,
                    "is_active": (str(csv_file.resolve()) == active_path),
                })
            except Exception:
                pass

    return datasets


@app.get("/api/database/records")
async def get_database_records(
    limit: int = Query(100, ge=1, le=2000),
    machine_id: Optional[str] = None,
    fault_label: Optional[str] = None,
    source_file: Optional[str] = None,
):
    """Retrieve newest stored records from database."""
    records = db_repo.get_latest_readings(
        limit=limit,
        machine_id=machine_id or None,
        fault_label=fault_label or None,
        source_file=source_file or None,
    )
    total = db_repo.get_total_count()
    status = get_db_status()
    return {
        "records": records,
        "total_count": total,
        "db_type": status["db_type"],
    }


@app.get("/api/database/metadata")
async def get_database_metadata():
    """Retrieve distinct machines, fault classes, and files for UI filtering."""
    return db_repo.get_distinct_metadata()


@app.get("/api/database/export")
async def export_database_csv(limit: int = 10000):
    """Export stored sensor records to downloadable CSV."""
    export_path = BASE_DIR / "data" / "MONTREAL_VT_export.csv"
    db_repo.export_to_csv(export_path, limit=limit)
    return FileResponse(
        path=str(export_path),
        filename="MONTREAL_VT_sensor_readings.csv",
        media_type="text/csv",
    )


class DeleteDataRequest(BaseModel):
    confirm: bool


@app.post("/api/database/delete")
async def delete_database_records(req: DeleteDataRequest):
    """Manually delete historical records with explicit confirmation."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirmation required.")
    deleted = db_repo.delete_historical_data(confirm=True)
    return {"deleted_count": deleted}


@app.get("/api/models")
async def get_models():
    """Return trained classifiers metadata, hyperparameters, and evaluation metrics."""
    return get_all_models_metadata()


@app.post("/api/pipeline/preprocess")
async def trigger_preprocessing():
    """Trigger dataset preprocessing pipeline."""
    results = run_preprocessing_pipeline()
    total = sum(len(f) for f in results.values())
    return {"status": "Complete", "processed_count": total}


@app.post("/api/pipeline/train_models")
async def trigger_model_training():
    """Trigger training across Logistic Regression, Decision Tree, and KNN."""
    train_and_compare_all()
    return {"status": "Complete", "models": get_all_models_metadata()}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

