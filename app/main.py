import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict

from .devices import DeviceManager, ADBError
from .models.db import SessionLocal, Flow, FlowRun, init_db
from .tasks import dispatch_to_devices

app = FastAPI(
    title="QA Device Farm",
    description="Plataforma de automação e orquestração de testes Android multi-dispositivo",
    version="0.1.0",
)

dm = DeviceManager()


@app.on_event("startup")
def startup():
    init_db()


# ---------- Dispositivos ----------

@app.get("/devices")
def list_devices():
    try:
        devices = dm.list_devices()
    except ADBError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return [d.__dict__ for d in devices]


@app.post("/devices/{serial}/screenshot")
def screenshot(serial: str):
    import tempfile
    path = tempfile.mktemp(suffix=".png")
    try:
        dm.screenshot(serial, path)
    except ADBError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"path": path}


@app.post("/devices/{serial}/reboot")
def reboot(serial: str):
    try:
        dm.reboot(serial)
    except ADBError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}


# ---------- Fluxos ----------

class FlowIn(BaseModel):
    name: str
    target_package: str
    steps: List[Dict[str, Any]]


@app.post("/flows")
def create_flow(flow_in: FlowIn):
    db = SessionLocal()
    try:
        flow = Flow(name=flow_in.name, target_package=flow_in.target_package, definition=json.dumps(flow_in.steps))
        db.add(flow)
        db.commit()
        db.refresh(flow)
        return {"id": flow.id, "name": flow.name}
    finally:
        db.close()


@app.get("/flows")
def list_flows():
    db = SessionLocal()
    try:
        flows = db.query(Flow).all()
        return [{"id": f.id, "name": f.name, "target_package": f.target_package} for f in flows]
    finally:
        db.close()


# ---------- Execução ----------

class RunIn(BaseModel):
    flow_id: int
    device_serials: List[str]  # executa em N dispositivos em paralelo


@app.post("/runs")
def trigger_run(run_in: RunIn):
    db = SessionLocal()
    try:
        flow = db.query(Flow).get(run_in.flow_id)
        if not flow:
            raise HTTPException(status_code=404, detail="flow não encontrado")
    finally:
        db.close()

    task_ids = dispatch_to_devices(run_in.flow_id, run_in.device_serials)
    return {"dispatched": len(task_ids), "task_ids": task_ids}


@app.get("/runs")
def list_runs(flow_id: int = None):
    db = SessionLocal()
    try:
        q = db.query(FlowRun)
        if flow_id:
            q = q.filter(FlowRun.flow_id == flow_id)
        runs = q.order_by(FlowRun.started_at.desc()).limit(100).all()
        return [
            {
                "id": r.id,
                "flow_id": r.flow_id,
                "device_serial": r.device_serial,
                "status": r.status,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
            }
            for r in runs
        ]
    finally:
        db.close()


@app.get("/runs/{run_id}")
def get_run(run_id: int):
    db = SessionLocal()
    try:
        r = db.query(FlowRun).get(run_id)
        if not r:
            raise HTTPException(status_code=404, detail="run não encontrada")
        return {
            "id": r.id,
            "flow_id": r.flow_id,
            "device_serial": r.device_serial,
            "status": r.status,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "log": r.log,
            "screenshot_path": r.screenshot_path,
        }
    finally:
        db.close()
