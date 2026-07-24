"""
Módulo de Visão Computacional / OCR
------------------------------------
Usado pelo Executor para:
  - validar se um texto esperado está presente na tela (OCR);
  - localizar um botão/ícone por template matching (OpenCV),
    evitando depender de coordenadas fixas de tela.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

try:
    import pytesseract
except ImportError:
    pytesseract = None


@dataclass
class MatchResult:
    found: bool
    x: Optional[int] = None
    y: Optional[int] = None
    confidence: float = 0.0


def read_text(image_path: str, lang: str = "por") -> str:
    """Extrai todo o texto visível de um print de tela."""
    if pytesseract is None:
        raise RuntimeError("pytesseract não instalado. `pip install pytesseract` e o binário tesseract-ocr.")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, lang=lang)


def assert_text_present(image_path: str, expected: str, lang: str = "por") -> bool:
    text = read_text(image_path, lang=lang)
    return expected.strip().lower() in text.lower()


def find_template(screen_path: str, template_path: str, threshold: float = 0.85) -> MatchResult:
    """Localiza um ícone/botão de referência (template_path) dentro do print de tela."""
    screen = cv2.imread(screen_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if screen is None or template is None:
        raise FileNotFoundError("Imagem de tela ou template não encontrada.")

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return MatchResult(found=True, x=center_x, y=center_y, confidence=float(max_val))
    return MatchResult(found=False, confidence=float(max_val))
