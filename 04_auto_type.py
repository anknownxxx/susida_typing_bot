"""
寿司打 自動タイピング（内容比較版）

これまでの「ピクセルの変化量」で切り替わりを判定する方式(差分検知)は、
背景の皿の重なりなど本題と関係ない動きに振り回されて、
どうしても一部の切り替わりを取りこぼす問題が解決しなかった。

そこで方針転換：
- 一定間隔でOCRを回し続ける
- 「読み取れた文字列が、前回タイプしたものと違うか」だけで判定する
- 背景がどう動こうが、OCRの中身（ローマ字）が変わらない限り何もしない

このやり方だと差分検知特有の「閾値」や「安定待ち」のようなチューニングが
不要になり、皿の動きなどのノイズにも影響されにくくなる。

起動後、START_DELAY秒のカウントダウンがあるので、その間に
ブラウザの寿司打ゲーム画面を手動でクリックしてフォーカスを合わせておくこと。
"""

import os
import re
import time
import webbrowser
from datetime import datetime

import mss
import numpy as np
import pyautogui
import pytesseract
from PIL import Image

GAME_URL = "https://sushida.net/play.html"

SAVE_DEBUG = True  # 原因調査用に、キャプチャした生画像をdebug_auto/に保存する
if SAVE_DEBUG:
    os.makedirs("debug_auto", exist_ok=True)

# ---- 環境依存の設定 ----
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

REGION = {
    "left": 615,
    "top": 596,
    "width": 668,
    "height": 155,
}

# ---- OCR前処理の設定 ----
CROP_TOP_RATIO = 0.55
CROP_SIDE_RATIO = 0.16
CROP_BOTTOM_RATIO = 0.1  # 下側をこの割合分削る（皿の重なりが透けて見える帯を除外するため）

# ---- ポーリング設定 ----
OCR_POLL_INTERVAL = 0.2  # 何秒おきにOCRを試みるか

# ---- タイピングの設定 ----
TYPE_INTERVAL = 0.02    # 1文字ずつ送信する間隔(秒)。速すぎて入力が抜ける場合は上げる

# ---- 起動時の猶予 ----
START_DELAY = 8  # ブラウザが開いてからコースを選んでスタートするまでの猶予秒数


def capture_array(sct):
    shot = sct.grab(REGION)
    return np.array(Image.frombytes("RGB", shot.size, shot.rgb), dtype=np.int16)


def preprocess(img_array):
    img = Image.fromarray(img_array.astype("uint8"))
    w, h = img.size

    left = int(w * CROP_SIDE_RATIO)
    right = int(w * (1 - CROP_SIDE_RATIO))
    top = int(h * CROP_TOP_RATIO)
    bottom = int(h * (1 - CROP_BOTTOM_RATIO))
    cropped = img.crop((left, top, right, bottom))

    upscaled = cropped.resize((cropped.width * 3, cropped.height * 3), Image.LANCZOS)
    gray = upscaled.convert("L")
    bw = gray.point(lambda p: 255 if p > 140 else 0)
    return bw


def extract_romaji(img_array):
    processed = preprocess(img_array)
    config = "--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz-"
    raw_text = pytesseract.image_to_string(processed, config=config)

    tokens = raw_text.split()
    cleaned_tokens = ["".join(re.findall(r"[a-zA-Z\-]+", t)).lower() for t in tokens]
    real_tokens = [t for t in cleaned_tokens if len(t) >= 2]
    return "".join(real_tokens)


def main():
    print("ブラウザで寿司打を開く。")
    webbrowser.open(GAME_URL)

    print(f"{START_DELAY}秒後に監視を始める。その間にコースを選んでスタートしておいて。")
    for i in range(START_DELAY, 0, -1):
        print(i)
        time.sleep(1)
    print("監視開始。Ctrl+Cで停止。")

    last_typed = ""

    with mss.mss() as sct:
        while True:
            time.sleep(OCR_POLL_INTERVAL)
            frame = capture_array(sct)
            romaji = extract_romaji(frame)

            # 空文字、または前回タイプしたものと同じなら何もしない
            if not romaji or romaji == last_typed:
                continue

            print(f"認識: {romaji}")

            if SAVE_DEBUG:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                debug_path = f"debug_auto/{ts}_raw.png"
                Image.fromarray(frame.astype("uint8")).save(debug_path)

            pyautogui.write(romaji, interval=TYPE_INTERVAL)
            last_typed = romaji

            if SAVE_DEBUG:
                # 認識・タイピングに使い終わったので、溜まらないようすぐ消す
                os.remove(debug_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("停止した。")