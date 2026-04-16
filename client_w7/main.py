"""
QuizSolver Client - Windows 7 (Python 3.8)
Triple-click -> screenshot -> pytesseract OCR -> REST API -> javob -> sichqon
"""
import ctypes
import glob
import os
import re
import threading
import time
from difflib import SequenceMatcher

import pytesseract
import requests
from PIL import Image, ImageGrab
from pynput import mouse
from pynput.mouse import Controller

# ══════════════════════════════════════════════════════════════
#  SOZLAMALAR
# ══════════════════════════════════════════════════════════════
API_URL = "https://quizsolver-api-production.up.railway.app/answer"
TRIPLE_CLICK_INTERVAL = 0.5

# ── Tesseract yo'li ────────────────────────────────────────────
for _p in [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
]:
    if os.path.exists(_p):
        pytesseract.pytesseract.tesseract_cmd = _p
        break

# ══════════════════════════════════════════════════════════════
#  DPI
# ══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_user32  = ctypes.windll.user32
_sample  = ImageGrab.grab()
SCALE_X  = _user32.GetSystemMetrics(0) / _sample.width
SCALE_Y  = _user32.GetSystemMetrics(1) / _sample.height

click_times = []
is_processing = False


def delete_old_screenshots():
    for f in glob.glob(os.path.join(BASE_DIR, "screenshot_*.png")):
        try:
            os.remove(f)
        except OSError:
            pass


def take_screenshot():
    path = os.path.join(BASE_DIR, "screenshot_{}.png".format(int(time.time())))
    ImageGrab.grab().save(path)
    return path


def ocr_fast(image_path):
    """pytesseract orqali OCR — har qator uchun markaz koordinat qaytaradi."""
    img = Image.open(image_path)
    data = pytesseract.image_to_data(
        img, lang='eng', output_type=pytesseract.Output.DICT
    )
    lines = {}
    n = len(data['text'])
    for i in range(n):
        if int(data['conf'][i]) < 0:
            continue
        text = data['text'][i].strip()
        if not text:
            continue
        key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        if key not in lines:
            lines[key] = []
        lines[key].append({
            'text': text,
            'x': data['left'][i],
            'y': data['top'][i],
            'w': data['width'][i],
            'h': data['height'][i],
        })

    blocks = []
    for key in sorted(lines.keys()):
        words = lines[key]
        line_text = ' '.join(w['text'] for w in words)
        # Faqat raqam/belgilardan iborat navigatsiya qatorlarini o'tkazib yuborish
        letters_only = re.sub(r'[\d\s\(\)\[\].,;:_\-«»/|°\'\"\*\+\=<>]+', '', line_text)
        if len(letters_only) < 3:
            continue
        mid = words[len(words) // 2]
        cx = mid['x'] + mid['w'] // 2
        cy = mid['y'] + mid['h'] // 2
        blocks.append({'text': line_text, 'x': cx, 'y': cy})
    return blocks


def find_block(answer, blocks):
    UI_SKIP = {'tugatish', 'random', 'test', 'random on', 'random test',
               'att test', 'umumiy', 'yechildi', 'qidiring', 'sunny', 'eng'}

    def norm(t):
        return t.lower().replace('\u02bb', "'").replace('\u2019', "'").strip()

    def sim(a, b):
        return SequenceMatcher(None, norm(a), norm(b)).ratio()

    ans_norm = norm(answer)
    best, best_score = None, 0.0
    for block in blocks:
        t = block['text'].strip().lower()
        if t in UI_SKIP or len(t) < 2:
            continue
        block_norm = norm(block['text'])
        bonus = 0.3 if (ans_norm in block_norm or block_norm in ans_norm) else 0.0
        s = sim(answer, block['text']) + bonus
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

        # pytesseract OCR — koordinatlar uchun
        blocks = ocr_fast(path)
        print("[process] OCR bloklari: {}".format(len(blocks)))
        for b in blocks:
            print("  {}".format(b['text']))

        if not blocks:
            print("[process] OCR hech narsa topmadi")
            return

        ocr_text = "\n".join(b['text'] for b in blocks)
        print("[process] API: {}".format(API_URL))
        with open(path, "rb") as f:
            resp = requests.post(
                API_URL,
                files={"image": ("screenshot.png", f, "image/png")},
                data={"ocr_text": ocr_text},
                timeout=60,
            )
        if not resp.ok:
            print("[!] Server xato {}: {}".format(resp.status_code, resp.text[:300]))
            return

        data = resp.json()
        answer = data.get("answer", "")
        source = data.get("source", "")
        print("[process] Javob [{}]: {}".format(source, answer[:60]))

        if not answer:
            print("[process] Javob kelmadi")
            return

        chosen = find_block(answer, blocks)
        if chosen is None:
            print("[process] Blok topilmadi")
            return

        mx = int(chosen['x'] * SCALE_X)
        my = int(chosen['y'] * SCALE_Y)
        print("[process] Sichqon: ({}, {})".format(mx, my))
        time.sleep(0.2)
        Controller().position = (mx, my)

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
