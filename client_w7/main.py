"""
QuizSolver Client - Windows 7 (Python 3.8)
Triple-click -> screenshot -> REST API -> popup
winocr ishlatilmaydi (Windows 10+ talab qiladi)
"""
import ctypes
import os
import threading
import time

import requests
from PIL import ImageGrab
from pynput import mouse
from pynput.mouse import Controller

# ══════════════════════════════════════════════════════════════
#  SOZLAMALAR
# ══════════════════════════════════════════════════════════════
API_URL = "https://quizsolver-api-production.up.railway.app/answer"
TRIPLE_CLICK_INTERVAL = 0.5

# ══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

click_times = []
is_processing = False


MOVE_OFFSET = 80  # piksel — variantlar oralig'iga qarab sozlang

_DIRECTIONS = {1: (0, -1), 2: (1, 0), 3: (0, 1), 4: (-1, 0)}  # yuqori/o'ng/pastki/chap

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def move_mouse(position):
    """1=yuqori  2=o'nga  3=pastga  4=chapga"""
    d = _DIRECTIONS.get(position)
    if not d:
        return
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    dx, dy = d
    Controller().position = (pt.x + dx * MOVE_OFFSET, pt.y + dy * MOVE_OFFSET)
    print("[mouse] position={} -> ({}, {})".format(
        position, pt.x + dx * MOVE_OFFSET, pt.y + dy * MOVE_OFFSET))


def take_screenshot():
    path = os.path.join(BASE_DIR, "screenshot_{}.png".format(int(time.time())))
    ImageGrab.grab().save(path)
    return path



def process():
    global is_processing
    is_processing = True
    print("[process] boshlandi...")
    try:
        path = take_screenshot()
        print("[process] API: {}".format(API_URL))

        with open(path, "rb") as f:
            resp = requests.post(
                API_URL,
                files={"image": ("screenshot.png", f, "image/png")},
                timeout=60,
            )

        try:
            os.remove(path)
        except OSError:
            pass

        if not resp.ok:
            print("[!] Server xato {}: {}".format(resp.status_code, resp.text[:300]))
            return

        data = resp.json()
        answer   = data.get("answer", "")
        source   = data.get("source", "")
        position = data.get("position", 0)
        print("[process] Javob [{}] pos={}: {}".format(source, position, answer[:80]))

        if not answer:
            print("[process] Javob kelmadi")
            return

        # Sichqon siljishi
        if position:
            time.sleep(0.15)
            move_mouse(position)
        else:
            print("[process] Pozitsiya topilmadi")

    except requests.exceptions.ConnectionError:
        print("[!] Server bilan aloqa yo'q: {}".format(API_URL))
    except Exception as e:
        print("[!] Xato: {}".format(e))
    finally:
        is_processing = False


def on_click(x, y, button, pressed):
    global click_times
    if button != mouse.Button.left or not pressed or is_processing:
        return
    now = time.time()
    click_times.append(now)
    click_times = [t for t in click_times if now - t <= TRIPLE_CLICK_INTERVAL]
    print("[click] count={}".format(len(click_times)))
    if len(click_times) >= 3:
        click_times.clear()
        threading.Thread(target=process, daemon=True).start()


def run():
    print("[*] QuizSolver Client (Windows 7) ishga tushdi")
    print("[*] Server: {}".format(API_URL))
    print("[*] Ishlatish: chap tugmani 3x bosing")
    while True:
        try:
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
        except Exception as e:
            print("[!] Listener xatosi: {}, 3s da qayta...".format(e))
            time.sleep(3)


if __name__ == "__main__":
    run()
