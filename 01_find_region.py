"""
座標確認用スクリプト

これを実行すると、画面全体のスクリーンショットが
screen_full.png として保存される。

使い方:
1. 寿司打のゲーム画面をブラウザで開いておく（お題が見えている状態にしておくと分かりやすい）
2. このスクリプトを実行する
3. 生成された screen_full.png を画像ビューア（ペイント等）で開く
4. お題テキストが表示されている領域の左上・右下のピクセル座標をメモする
   （ペイントなら画像上でマウスを動かすと左下にピクセル座標が出る）
5. その座標を 02_diff_detect.py の REGION に入力する
"""

import mss
from PIL import Image

with mss.mss() as sct:
    # モニターが複数ある場合、sct.monitors[0] が「全モニターを含む仮想画面全体」
    # sct.monitors[1] が「プライマリモニターだけ」。まずは[1]を使う。
    monitor = sct.monitors[1]
    shot = sct.grab(monitor)
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    img.save("screen_full.png")

print("screen_full.png を保存した。")
print(f"このモニターの解像度: {monitor['width']} x {monitor['height']}")
print("画像を開いて、お題テキストの領域の座標(left, top, width, height)を確認して。")