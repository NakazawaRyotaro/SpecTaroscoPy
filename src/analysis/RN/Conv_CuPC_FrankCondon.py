from scipy.signal import find_peaks
import numpy as np
import matplotlib as plt
import matplotlib.pyplot as plt
import copy
from pathlib import Path


# -------------------- モジュール読み込み --------------------
# sysモジュールをインポート（Pythonのパスや環境に関する操作をするため）
import sys
# osモジュールをインポート（ファイルパスの操作や環境関連の処理に使う）
import os

# sys.path（Pythonのモジュール検索パス）に新しいパスを追加する --> srcディレクトリ が追加される
sys.path.append(
    # os.path.abspath: 相対パスを絶対パスに変換する
    os.path.abspath(
        # os.path.join: 複数のパスをつなげる（この場合、「今のファイルのディレクトリ」と「..（1つ上）」をつなげる）
        os.path.join(
            # os.path.dirname(__file__): このスクリプトファイル（.py）が存在するディレクトリのパスを取得
            os.path.dirname(__file__),
            '..', '..'  # 「..」は1つ上の階層（親ディレクトリ）を意味する
        )
    )
)

# 自作モジュールのインポート（srcを基準にした絶対import）
from RyoPy import defs_for_analysis as rpa
from RyoPy.Spectrum import Spectrum

# srcディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent.parent
# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
second_derivative_setting_path = os.path.join(SRC_PATH, "setting", "second_derivative_setting.txt")

# ファイル選択するときの初期値
VERSION, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "version", type="str")


# -------------------- モジュール読み込み終わり -----------------
"""
CFS-YSとPYSの微分の性能比較。

CFSは、光量で規格化した。
窓の透過率で規格化した。
PEで規格化していない。

PYSはHS-UPSスペクトルを積分したものとする。
光量で規格化した。
窓透過率で規格化した。
PEで規格化しなかった。
微分前のスムージングはSG法を使用する。
"""


# -------------------- 初期条件 --------------------
# ファイル名
filename_pys = 'CuPc_Frankcondon.csv'

x_legend_pys = 'eV'
y_legend_pys = 'intensity'

# Gaussian smoothing
FWHM=0.1

########################################################################
# 現在のスクリプトの位置から '2つ' 上のディレクトリへ移動
# Path(__file__) 今のファイルを読み込み
# .resolve() 絶対パスに変換
# .parent 親ディレクトリ (フォルダーのpath) 
# base_path = Path(__file__).resolve().parent.parent.parent

# 絶対パスを指定する
base_path = Path("/Users/ryotaro/Documents/実験データ/吉田研関連")
# フォルダAの中の fileB を指定
import_file_path_pys = base_path / filename_pys

########################################################################
################################################################
# --- data load ---
pys=Spectrum()
pys.read_labels_from_file_auto(path=import_file_path_pys)
print(pys.label_list)
pys.load_xy_data_from_file_auto(x_legend=x_legend_pys, y_legend=y_legend_pys, encoding="utf-8-sig", plot_spectrum=False)
print(pys.x)
print(pys.y)


##############################################################################
# --- spectrum smoothing ---

pys.generate_spread_function_for_deconvolution(pys.x, 'Gaussian', FWHM)
print(pys.s)
pys.y_smooth = rpa.conv(pys.y, pys.s, step=pys.x_step)

fig, ax = plt.subplots(1, 2, figsize=(8, 3))
for i in range(2):
    ax[i].plot(pys.x, pys.y, label="Raw", color="tab:orange", linewidth=3)
    ax[i].plot(pys.x, pys.y_smooth, label="Conv. Raw with Gauss", color="tab:blue", linewidth=3)
    ax[i].set_ylabel("Intensity (cps)")
    ax[i].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
    ax[i].set_title('Conv. with Gaussian (FWHM='+str(FWHM)+' eV)')
    ax[i].legend(loc='best')
    ax[i].invert_xaxis()

ax[1].set_yscale('log')

plt.show()