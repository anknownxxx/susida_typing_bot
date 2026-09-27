"""
座標確認ツール

使い方:
1. screen_full.png と同じフォルダでこのスクリプトを実行する
2. 画像が表示されるので、
   ① お題テキスト領域の左上をクリック
   ② お題テキスト領域の右下をクリック
   の順にクリックする
3. ターミナルに REGION の値がそのまま出力される
   （そのまま 02_diff_detect.py にコピペできる形式）
4. ウィンドウを閉じれば終了

※ 拡大したい場合は、matplotlibウィンドウの虫眼鏡アイコン（拡大ツール）で
  先に領域を拡大してからクリックすると精度が上がる。
  拡大した状態でクリックしても、表示されるのは元画像のピクセル座標なので問題ない。
"""

import matplotlib.pyplot as plt
from PIL import Image

IMAGE_PATH = "screen_full.png"

img = Image.open(IMAGE_PATH)
clicks = []

fig, ax = plt.subplots()
ax.imshow(img)
ax.set_title("① 左上をクリック → ② 右下をクリック")


def on_click(event):
    if event.xdata is None or event.ydata is None:
        return  # 画像の外側をクリックした場合は無視

    x, y = int(event.xdata), int(event.ydata)
    clicks.append((x, y))
    print(f"クリック{len(clicks)}: (x={x}, y={y})")

    if len(clicks) == 2:
        (x1, y1), (x2, y2) = clicks
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)

        print("\n----- 02_diff_detect.py にコピペする値 -----")
        print("REGION = {")
        print(f'    "left": {left},')
        print(f'    "top": {top},')
        print(f'    "width": {width},')
        print(f'    "height": {height},')
        print("}")
        print("---------------------------------------------")
        print("\nウィンドウを閉じて終了してOK。")


fig.canvas.mpl_connect("button_press_event", on_click)
plt.show()
