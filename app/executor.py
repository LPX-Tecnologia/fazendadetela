"""
Executor de Fluxos
-------------------
Interpreta um Flow (lista de passos em JSON) e executa cada passo
sequencialmente em um dispositivo, usando o DeviceManager e o
módulo de vision para validações.

Blocos suportados no MVP:
  open_app, wait, tap, swipe, input_text,
  assert_text (OCR), find_and_tap (template matching),
  screenshot, loop
"""
import json
import time
import tempfile
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .devices import DeviceManager, ADBError
from . import vision


@dataclass
class StepResult:
    step: Dict[str, Any]
    ok: bool
    message: str = ""


@dataclass
class FlowResult:
    ok: bool
    steps: List[StepResult] = field(default_factory=list)
    last_screenshot: str = ""


class FlowExecutor:
    def __init__(self, device_manager: DeviceManager = None):
        self.dm = device_manager or DeviceManager()

    def run(self, serial: str, target_package: str, steps: List[Dict[str, Any]]) -> FlowResult:
        results: List[StepResult] = []
        last_screenshot = ""

        for step in steps:
            action = step.get("action")
            try:
                if action == "open_app":
                    self.dm.open_app(serial, target_package, step.get("activity"))
                    results.append(StepResult(step, True, "app aberto"))

                elif action == "wait":
                    time.sleep(step.get("seconds", 1))
                    results.append(StepResult(step, True, "aguardado"))

                elif action == "tap":
                    self.dm.tap(serial, step["x"], step["y"])
                    results.append(StepResult(step, True, "tap executado"))

                elif action == "swipe":
                    self.dm.swipe(serial, step["x1"], step["y1"], step["x2"], step["y2"], step.get("duration_ms", 300))
                    results.append(StepResult(step, True, "swipe executado"))

                elif action == "input_text":
                    self.dm.input_text(serial, step["text"])
                    results.append(StepResult(step, True, "texto inserido"))

                elif action == "screenshot":
                    path = tempfile.mktemp(suffix=".png")
                    self.dm.screenshot(serial, path)
                    last_screenshot = path
                    results.append(StepResult(step, True, f"print salvo em {path}"))

                elif action == "assert_text":
                    path = tempfile.mktemp(suffix=".png")
                    self.dm.screenshot(serial, path)
                    last_screenshot = path
                    found = vision.assert_text_present(path, step["expected"], lang=step.get("lang", "por"))
                    if not found:
                        results.append(StepResult(step, False, f"texto '{step['expected']}' não encontrado na tela"))
                        return FlowResult(ok=False, steps=results, last_screenshot=last_screenshot)
                    results.append(StepResult(step, True, "texto encontrado"))

                elif action == "find_and_tap":
                    path = tempfile.mktemp(suffix=".png")
                    self.dm.screenshot(serial, path)
                    last_screenshot = path
                    match = vision.find_template(path, step["template"], step.get("threshold", 0.85))
                    if not match.found:
                        results.append(StepResult(step, False, "elemento não localizado na tela"))
                        return FlowResult(ok=False, steps=results, last_screenshot=last_screenshot)
                    self.dm.tap(serial, match.x, match.y)
                    results.append(StepResult(step, True, f"elemento encontrado (conf={match.confidence:.2f}) e tocado"))

                elif action == "loop":
                    times = step.get("times", 1)
                    inner_steps = step.get("steps", [])
                    for _ in range(times):
                        inner_result = self.run(serial, target_package, inner_steps)
                        results.extend(inner_result.steps)
                        if not inner_result.ok:
                            return FlowResult(ok=False, steps=results, last_screenshot=inner_result.last_screenshot)

                else:
                    results.append(StepResult(step, False, f"ação desconhecida: {action}"))
                    return FlowResult(ok=False, steps=results, last_screenshot=last_screenshot)

            except ADBError as e:
                results.append(StepResult(step, False, f"erro ADB: {e}"))
                return FlowResult(ok=False, steps=results, last_screenshot=last_screenshot)

        return FlowResult(ok=True, steps=results, last_screenshot=last_screenshot)


def load_flow_definition(json_str: str) -> List[Dict[str, Any]]:
    return json.loads(json_str)
