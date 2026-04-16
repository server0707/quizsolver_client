"""
QuizSolver Client (Windows)
Triple-click → screenshot → REST API → javob → sichqon
"""
import ctypes
import glob
import os
import threading
import time
from difflib import SequenceMatcher

import requests
import winocr
from PIL import Image, ImageGrab
from pynput import mouse
from pynput.mouse import Controller

# ══════════════════════════════════════════════════════════════
#  SOZLAMALAR
# ══════════════════════════════════════════════════════════════
API_URL = "https://quizsolver-api-production.up.railway.app/answer"
TRIPLE_CLICK_INTERVAL = 0.5

# ══════════════════════════════════════════════════════════════
#  DPI
# ══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_user32  = ctypes.windll.user32
_sample  = ImageGrab.grab()
SCALE_X  = _user32.GetSystemMetrics(0) / _sample.width
SCALE_Y  = _user32.GetSystemMetrics(1) / _sample.height

click_times: list[float] = []
is_processing = False


def delete_old_screenshots():
    for f in glob.glob(os.path.join(BASE_DIR, "screenshot_*.png")):
        try:
            os.remove(f)
        except OSError:
            pass


def take_screenshot() -> str:
    path = os.path.join(BASE_DIR, f"screenshot_{int(time.time())}.png")
    ImageGrab.grab().save(path)
    return path


def ocr_fast(image_path: str) -> list[dict]:
    img = Image.open(image_path)
    result = winocr.recognize_pil_sync(img, "en")
    blocks = []
    for line in result["lines"]:
        words = line["words"]
        if not words:
            continue
        line_text = " ".join(w["text"] for w in words)
        mid = words[len(words) // 2]
        r = mid["bounding_rect"]
        cx = int(r["x"] + r["width"] / 2)
        cy = int(r["y"] + r["height"] / 2)
        blocks.append({"text": line_text, "x": cx, "y": cy})
    return blocks


def find_block(answer: str, blocks: list[dict]) -> dict | None:
    UI_SKIP = {'tugatish', 'random', 'test', 'random on', 'random test',
               'att test', 'umumiy', 'yechildi', 'qidiring', 'sunny', 'eng'}

    def norm(t):
        return t.lower().replace('\u02bb', "'").replace('\u2019', "'").strip()

    def sim(a, b):
        return SequenceMatcher(None, norm(a), norm(b)).ratio()

    ans_norm = norm(answer)
    best, best_score = None, 0.0
    for block in blocks:
        t = block["text"].strip().lower()
        if t in UI_SKIP or len(t) < 2:
            continue
        block_norm = norm(block["text"])
        bonus = 0.3 if (ans_norm in block_norm or block_norm in ans_norm) else 0.0
        s = sim(answer, block["text"]) + bonus
        if s > best_score:
            best_score = s
            best = block

    return best if best and best_score >= 0.4 else None


def process():
    global is_processing
    is_processing = True
    print("[process] boshlandi...")
    try:
        delete_old_screenshots()
        path = take_screenshot()

        # WinOCR — koordinatlar uchun
        blocks = ocr_fast(path)
        print(f"[process] OCR bloklari: {len(blocks)}")
        for b in blocks:
            print(f"  {b['text']}")

        if not blocks:
            print("[process] OCR hech narsa topmadi")
            return

        ocr_text = "\n".join(b["text"] for b in blocks)
        print(f"[process] API: {API_URL}")
        with open(path, "rb") as f:
            resp = requests.post(
                API_URL,
                files={"image": ("screenshot.png", f, "image/png")},
                data={"ocr_text": ocr_text},
                timeout=60,
            )
        if not resp.ok:
            print(f"[!] Server xato {resp.status_code}: {resp.text[:300]}")
            return
        data = resp.json()
        answer = data.get("answer", "")
        source = data.get("source", "")
        print(f"[process] Javob [{source}]: {answer[:60]}")

        if not answer:
            print("[process] Javob kelmadi")
            return

        # Blok topish
        chosen = find_block(answer, blocks)
        if chosen is None:
            print("[process] Blok topilmadi")
            return

        mx = int(chosen["x"] * SCALE_X)
        my = int(chosen["y"] * SCALE_Y)
        print(f"[process] Sichqon: ({mx}, {my})")
        time.sleep(0.2)
        Controller().position = (mx, my)

    except requests.exceptions.ConnectionError:
        print(f"[!] Server bilan aloqa yo'q: {API_URL}")
    except Exception as e:
        print(f"[!] Xato: {e}")
    finally:
        is_processing = False


def on_click(x, y, button, pressed):
    global click_times
    if button != mouse.Button.left or not pressed or is_processing:
        return
    now = time.time()
    click_times.append(now)
    click_times = [t for t in click_times if now - t <= TRIPLE_CLICK_INTERVAL]
    print(f"[click] count={len(click_times)}")
    if len(click_times) >= 3:
        click_times.clear()
        threading.Thread(target=process, daemon=True).start()


def run():
    print(f"[*] QuizSolver Client ishga tushdi")
    print(f"[*] Server: {API_URL}")
    print("[*] Ishlatish: chap tugmani 3x bosing")
    while True:
        try:
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
        except Exception as e:
            print(f"[!] Listener xatosi: {e}, 3s da qayta...")
            time.sleep(3)


if __name__ == "__main__":
    run()
