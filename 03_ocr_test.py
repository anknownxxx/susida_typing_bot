"""
OCRテストスクリプト

captures/ フォルダの中の画像を1枚ずつ読み込んで、
ローマ字部分だけをOCRで抽出してターミナルに表示する。

やっていること:
- お題ボックスは「かな/漢字の行」＋「ローマ字の行」の2段構成なので、
  画像の下半分（ローマ字が書かれている側）だけを切り出してOCRにかける
- OCR結果から a-z の文字だけを正規表現で抜き出す
  （かな漢字が多少誤認識で紛れ込んでも、ここでノイズとして除去できる）

まずはこれで「実際どれくらい正確に読み取れるか」を目視確認する。
"""

import glob
import os
import re

import pytesseract
from PIL import Image

SAVE_DEBUG = True  # Trueにすると前処理後の画像をdebug/フォルダに保存する（見た目確認用）
if SAVE_DEBUG:
    os.makedirs("debug", exist_ok=True)

# Tesseract本体をインストールした場所を指定する
# インストール先が違う場合はここを書き換える
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ローマ字の行は画像の下側にある想定。上から何%を切り捨てるかの割合
CROP_TOP_RATIO = 0.55  # 上半分（かな漢字の行）を切り捨てて、下半分だけを見る

# ボックスの縁（角丸の線など）が写り込んで誤認識の原因になるので、
# 左右・下にも余白としてこの割合だけ切り捨てる
CROP_SIDE_RATIO = 0.08    # 左右、それぞれこの割合分を削る
CROP_BOTTOM_RATIO = 0     # 下は削らない（不要と判断したため0に設定）


def preprocess(cropped):
    # 拡大：小さい文字・細い記号（ハイフンなど）はそのままだと潰れやすいので
    # 3倍に拡大してからOCRにかけると認識率が上がる
    w, h = cropped.size
    upscaled = cropped.resize((w * 3, h * 3), Image.LANCZOS)

    # グレースケール化 → 二値化（白黒はっきりさせる）
    gray = upscaled.convert("L")
    # 156より明るい部分を白、それ以外を黒にする（背景が暗いボックスなので閾値は要調整）
    bw = gray.point(lambda p: 255 if p > 140 else 0)

    return bw


def extract_romaji(image_path):
    img = Image.open(image_path)
    w, h = img.size

    # 下半分だけ切り出す（＋左右・下の余白も削ってボックスの縁を除去）
    left = int(w * CROP_SIDE_RATIO)
    right = int(w * (1 - CROP_SIDE_RATIO))
    top = int(h * CROP_TOP_RATIO)
    bottom = int(h * (1 - CROP_BOTTOM_RATIO))
    cropped = img.crop((left, top, right, bottom))
    processed = preprocess(cropped)

    if SAVE_DEBUG:
        base = os.path.splitext(os.path.basename(image_path))[0]
        processed.save(f"debug/{base}_processed.png")

    # OCR実行。--psm 7 は「1行のテキストとして扱う」モード
    # tessedit_char_whitelist で「出現しうる文字」をa-zとハイフンだけに絞り、誤読を減らす
    config = "--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz-"
    raw_text = pytesseract.image_to_string(processed, config=config)

    # スペース区切りでトークンに分解する。
    # ボックスの縁の装飾がノイズとして「a」や「-」単体の別トークンで
    # 混ざってくることがあるので、各トークンからa-zとハイフン以外を除去したうえで、
    # 1文字しかないトークン（ノイズの可能性が高い）は捨てて、残りを連結する。
    # 本物の単語は常に1つの連続した文字列として書かれているはず、という前提。
    tokens = raw_text.split()
    cleaned_tokens = ["".join(re.findall(r"[a-zA-Z\-]+", t)).lower() for t in tokens]
    real_tokens = [t for t in cleaned_tokens if len(t) >= 2]
    romaji = "".join(real_tokens)

    return raw_text.strip(), romaji


def main():
    files = sorted(glob.glob("captures/*.png"))
    if not files:
        print("captures/ に画像が見つからない。先に02_diff_detect.pyを実行して。")
        return

    for path in files:
        raw, romaji = extract_romaji(path)
        print(f"[{path}]")
        print(f"  OCR生データ : {raw!r}")
        print(f"  抽出結果    : {romaji}")
        print()


if __name__ == "__main__":
    main()