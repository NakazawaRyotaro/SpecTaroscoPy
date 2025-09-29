import customtkinter
import copy
import platform
from pathlib import Path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox

# -------------------- モジュール読み込み --------------------
import sys
import os

# matplotlibのバックエンドをmacOS用に設定
if platform.system() == "Darwin":
    import matplotlib
    matplotlib.use('tkagg')  # GUIありバックエンド
# 自作モジュールのインポートのため、srcディレクトリをsys.pathに追加
CURRENT_DIR = Path(__file__).resolve().parent          # このファイルのあるディレクトリ（例: src/analysis）
SRC_PATH = CURRENT_DIR.parent                          # 1つ上が src/
sys.path.append(str(SRC_PATH))                         # str()で文字列に変換してappendする

# 自作モジュールのインポート（srcを基準にした絶対import）
from RyoPy import defs_for_analysis as rpa
from RyoPy.MBS_A1 import MBS_A1
from RyoPy.PlotControl import ImagePlotControl, PlotControl
from analysis.arpes_image import App as AppArpesImage


# -------------------- ファイルパスの設定 --------------------
SETTING_PATH = SRC_PATH / "setting"
default_setting_path = SETTING_PATH / "default_setting.txt"
arpes_image_setting_path = SETTING_PATH / "ARPES_image_setting.txt"

# -------------------- 設定ファイルからの読み込み --------------------
# フォルダパスを取得（なければデフォルトにする）
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
if not has_IDIR:
    IDIR = SRC_PATH.parent.parent  # 念のためsrcよりさらに2つ上へ（必要なら調整）

# ユーザー名などのその他設定
USER, _ = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")

FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")
COLORMAP, has_COLORMAP = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "colormap_photoemission_intensity_map", type="str")
if not has_COLORMAP:
    COLORMAP = "viridis"

# EDC(s)　plotのカラー
SPECTRAL_COLOR_='darkslateblue'
SPECTRAL_COLOR, has_SPECTRAL_COLOR = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "color_edc", type="str")
if not has_SPECTRAL_COLOR:
    SPECTRAL_COLOR=SPECTRAL_COLOR_
    
# 表示する桁数
ORDER_X = 10
ORDER_Y = copy.copy(ORDER_X)    
ORDER_Z = 10


# 大枠
class App(AppArpesImage):
    def __init__(self):
        super().__init__()
        self.title("SpecTaroscoPy — Deflector Map")
    
# overrideしていく関数
# setup_form
# image....
    
# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(True, True)
    app.mainloop()