import os
from celery import Celery
from datetime import datetime

from .executor import FlowExecutor, load_flow_definition
from .models.db import SessionLocal, Flow, FlowRun, RunStatus

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("qa_farm", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task(name="run_flow_on_device")
def run_flow_on_device(flow_id: int, serial: str) -> dict:
    db = SessionLocal()
    try:
        flow = db.query(Flow).get(flow_id)
        if not flow:
            return {"ok": False, "message": "flow não encontrado"}

        run = FlowRun(flow_id=flow_id, device_serial=serial, status=RunStatus.RUNNING)
        db.add(run)
        db.commit()
        db.refresh(run)

        steps = load_flow_definition(flow.definition)
        executor = FlowExecutor()
        result = executor.run(serial, flow.target_package, steps)

        run.status = RunStatus.SUCCESS if result.ok else RunStatus.FAILED
        run.finished_at = datetime.utcnow()
        run.log = "\n".join(f"[{'OK' if s.ok else 'FAIL'}] {s.step.get('action')}: {s.message}" for s in result.steps)
        run.screenshot_path = result.last_screenshot
        db.commit()

        return {"ok": result.ok, "run_id": run.id, "log": run.log}
    finally:
        db.close()


def dispatch_to_devices(flow_id: int, serials: list[str]) -> list[str]:
    """Dispara a execução do mesmo fluxo em N dispositivos em paralelo."""
    task_ids = []
    for serial in serials:
        async_result = run_flow_on_device.delay(flow_id, serial)
        task_ids.append(async_result.id)
    return task_ids
