"""
差分検知スクリプト（③のコア部分）

やっていること:
- 指定した画面領域(REGION)を高速ループで繰り返しキャプチャする
- 直前のフレームと今のフレームの「平均的な差の大きさ」を計算する
- その差が閾値(THRESHOLD)を超えたら「画面が変化した」と判定し、
  その瞬間のフレームを captures/ フォルダに保存する
- 一度検知したら COOLDOWN 秒は再検知しない（同じ変化を何度も拾わないため）

このループ自体は軽い処理（キャプチャ＋簡単な数値計算だけ）なので、
1秒間に何十回も回せる。ここではまだOCRはしていない
（OCRは重いので「変化した瞬間」だけに絞って次のステップで使う）。
"""

import time
import os
from datetime import datetime

import mss
import numpy as np
from PIL import Image

# ---- ここを 01_find_region.py で確認した座標に書き換える ----
REGION = {
    "left": 615,
    "top": 596,
    "width": 668,
    "height": 155,
}
# --------------------------------------------------------

THRESHOLD = 8.0      # この値より差が大きければ「変化」とみなす。誤検知が多ければ上げる、拾えなければ下げる
COOLDOWN = 1.0        # 検知後、次の検知までの待機秒数
POLL_INTERVAL = 0.05  # 何秒おきにキャプチャするか（0.05 = 1秒間に20回）

os.makedirs("captures", exist_ok=True)


def capture(sct):
    shot = sct.grab(REGION)
    return np.array(Image.frombytes("RGB", shot.size, shot.rgb), dtype=np.int16)


def main():
    with mss.mss() as sct:
        prev = capture(sct)
        print("監視開始。Ctrl+Cで停止。")

        while True:
            time.sleep(POLL_INTERVAL)
            current = capture(sct)

            diff = np.mean(np.abs(current - prev))
            prev = current

            if diff > THRESHOLD:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                path = f"captures/{ts}.png"
                Image.fromarray(current.astype(np.uint8)).save(path)
                print(f"[変化検知] diff={diff:.2f}  -> {path} に保存")

                # クールダウン：この間は監視を止めて、直後の余計な検知を防ぐ
                time.sleep(COOLDOWN)
                prev = capture(sct)  # クールダウン明けの状態を新しい基準にする


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("停止した。")