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
            '..'  # 「..」は1つ上の階層（親ディレクトリ）を意味する
        )
    )
)

# 自作モジュールのインポート（srcを基準にした絶対import）
from RyoPy import defs_for_analysis as rpa
from RyoPy.Spectrum import Spectrum

# srcディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent
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
normalize_T=False
normalize_PE=True # PFPEを読み込んだ前提でTrueならなにもしない。
smooth_SG=False # Savitzky-Golay smoothing
smooth_gauss=True # Gaussian smoothing
show_log_scale_CFS_BGvsDPYS_BG=True # linear scale
show_log_scale_CFSvsDPYS=True # log scale
plot_2d_pys = False # 2階微分をプロットするか
save_output = False # saveするか (saveしないとき図が出力される)


# ファイル名
# imported filename
# PYSとCFSで分ける。
# filename = 'C60forVer3.txt' # C60 木全
# filename = 'C60forVer3_木全_池上.txt' # C60 木全
# filename = 'C60forVer3_木全_渡辺.txt' # C60 木全
# filename = 'Alq3forVer3.txt' # Alq3
# filename = 'PEN_Maruyama.csv'

# filename_pys = 'C60_tateno_PYS接続re.csv' # D2
# filename_pys = 'd2_4_5_6_8_9_10_11.4_NAKAZAWA.csv' # D2
# filename_pys = 'C60_hoshikawa_4_9.csv' # D2
filename_pys = '20251215_tatenoPYS_con_FITexp.csv' # D2
# filename_pys = 'C60_tateno_PYS.csv' # D2
filename_cfs = 'C60_tateno_CFS.csv' # D2

# 読み込みラベル名
x_legend_cfs = 'X'
y_legend_cfs = 'Y'
PE_legend_cfs = 'PE'

x_legend_pys = 'X'
y_legend_pys = 'Y'

# SG smoothing
sg_order=2
sg_window_length=9
sg_iteration=7


# Gaussian smoothing
FWHM=0.2
background=0
# plotパラメータ （Fig4, CFSとDPYSの比較）
mult_y_pys_dif=1.2e-0
# mult_y_pys_dif=3e-11
mult_y_pys_dif_dif=1e-5

####################################################################


########################################################################
# 現在のスクリプトの位置から '2つ' 上のディレクトリへ移動
# Path(__file__) 今のファイルを読み込み
# .resolve() 絶対パスに変換
# .parent 親ディレクトリ (フォルダーのpath) 
# base_path = Path(__file__).resolve().parent.parent.parent

# 絶対パスを指定する
base_path = Path("/Users/ryotaro/Library/Group Containers/UBF8T346G9.OneDriveStandaloneSuite/OneDrive.noindex/OneDrive/ドキュメント/論文執筆/2025_ACS_BEE/図/PYS_DPYSvsCFS")
# フォルダAの中の fileB を指定
import_file_path_cfs = base_path / filename_cfs
import_file_path_pys = base_path / filename_pys
print(f"import_file_path: {import_file_path_cfs}")
import_file_path_window= base_path / '20210915新PF割る現PF.csv'
########################################################################
if save_output:
    import matplotlib.pyplot
    matplotlib.use('Agg')  # 描画はファイル保存に限る（GUIウィンドウ表示なし）

########################################################################
# --- CFS ---
# C60 spectrum
cfsys=Spectrum()
cfsys.read_labels_from_file_auto(path=import_file_path_cfs)
print(cfsys.label_list)
cfsys.load_xy_data_from_file_auto(x_legend=x_legend_cfs, y_legend=y_legend_cfs, plot_spectrum=False)
# PE

# PE規格化「しない」場合 (する場合コメントアウト)
if normalize_PE==False:
    PE_CFSYS=Spectrum()
    PE_CFSYS.read_labels_from_file_auto(path=import_file_path_cfs)
    PE_CFSYS.load_xy_data_from_file_auto(x_legend=PE_legend_cfs, y_legend=y_legend_cfs, plot_spectrum=False)
    cfsys.y*=PE_CFSYS.x

# plot
fig, ax = plt.subplots(1, 2, figsize=(8, 3))
# C60
ax[0].scatter(cfsys.x, cfsys.y, label="CFS", color="tab:blue", alpha=0.3, s=10)
ax[1].scatter(cfsys.x, cfsys.y, label="CFS", color="tab:blue", alpha=0.3, s=10)

# --- 窓で規格化 ---
if normalize_T:
    # 分光器・チャンバー間 透過率
    t_window=Spectrum()
    t_window.read_labels_from_file_auto(path=import_file_path_window)
    t_window.load_xy_data_from_file_auto(x_legend=PE_legend_cfs, y_legend='T')
    t_window.x, t_window.y = rpa.spline_ver2(t_window.x, t_window.y, t_window.x_min, t_window.x_max, cfsys.x_step)
    # 規格化
    cfsys.y=cfsys.y/t_window.y

    # mult
    mult_c60_cfs_y_NT=3
    # plot
    ax[0].plot(t_window.x, t_window.y, label='t_window', color='tab:red')
    ax[0].plot(cfsys.x, cfsys.y*mult_c60_cfs_y_NT, label='CFS/T', color='blue')
    ax[1].plot(cfsys.x, cfsys.y*mult_c60_cfs_y_NT, label='CFS/T', color='blue')

ax[0].set_ylabel("Intensity (cps)")
ax[0].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
ax[0].set_title('CFSYS C60')
ax[0].legend(loc='best')
ax[0].invert_xaxis()
# ax[0].set_yscale('log')
ax[0].set_ylabel("Intensity (cps)")
ax[0].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
ax[0].set_title('CFSYS normarization')
ax[0].legend(loc='best')

ax[1].set_yscale('log')
ax[1].set_ylabel("Intensity (cps)")
ax[1].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
ax[1].set_title('CFSYS C60')
ax[1].legend(loc='best')
ax[1].invert_xaxis()
ax[1].set_ylabel("Intensity (cps)")
ax[1].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
ax[1].set_title('CFSYS normarization')

################################################################
# --- PYS ---
# --- data load ---
pys=Spectrum()
pys.read_labels_from_file_auto(path=import_file_path_pys)
pys.load_xy_data_from_file_auto(x_legend=x_legend_pys, y_legend=y_legend_pys, plot_spectrum=False)
print(pys.x)
print(pys.y)
"""
if filename=='C60forVer3_木全_池上.txt':
    PM=Spectrum()
    PM.read_labels_from_file_auto(path=import_file_path)
    PM.load_xy_data_from_file_auto(x_legend='PE_pys_normalize', y_legend='PM_pys_normalize', plot_spectrum=False)

    QE=Spectrum()
    QE.read_labels_from_file_auto(path=import_file_path)
    QE.load_xy_data_from_file_auto(x_legend='PE_pys_normalize', y_legend='QE_pys_normalize', plot_spectrum=False)

    x_min=np.amin(PM.x)
    x_max=np.amax(PM.x)
    x_step=pys.x_step
    # spline
    pys.x, pys.y = rpa.spline_ver2(pys.x, pys.y, x_min, x_max, x_step)
    PM.x, PM.y = rpa.spline_ver2(PM.x, PM.y, x_min, x_max, x_step)
    QE.x, QE.y = rpa.spline_ver2(QE.x, QE.y, x_min, x_max, x_step)
    # 規格化
    pys.y = pys.y / PM.y * QE.y
"""


# --- plot ---
# 窓で規格化
if normalize_T:
    t_window.x, t_window.y = rpa.spline_ver2(t_window.x, t_window.y, t_window.x_min, t_window.x_max, cfsys.x_step)
    pys.y_normT=pys.y/t_window.y


##############################################################################
# --- PYS -> DPYS, 2DPYS ---
# --- BG処理なし PYS ---
# SG smoothing
if smooth_SG:
    pys.smooth_spectra_by_SG(pys.y, sg_order, sg_window_length, sg_iteration) # 生
    pys.y_smooth = copy.deepcopy(pys.y_sg_lst[-1])
# gaussainスムージング
elif smooth_gauss:
    pys.generate_spread_function_for_deconvolution(pys.x, 'Gaussian', FWHM)
    print(pys.s)
    pys.y_smooth = rpa.conv(pys.y, pys.s, step=pys.x_step)
else:
    pys.y_smooth = pys.y
# 微分
pys.y_sg_dif=np.gradient(pys.y_smooth, pys.x, edge_order=1)
# 二階微分
pys.y_sg_dif_dif=np.gradient(pys.y_sg_dif, pys.x, edge_order=1)
# plot

fig, ax = plt.subplots(1, 2, figsize=(8, 3))
ax[0].scatter(pys.x, pys.y, alpha=0.3,label="PYS", color="tab:gray", s=10)
if smooth_SG==True or smooth_gauss==True:
    ax[0].plot(pys.x, pys.y_smooth, label="PYS smooth", color="tab:gray")
# ax[0].plot(pys.x, pys.y_sg_dif, label="DPYS", color="tab:orange")
# その他設定
ax[0].plot([min(pys.x), max(pys.x)], [0,0], color="black", linewidth=1, zorder=0)
ax[0].set_ylabel("Intensity (cps)")
ax[0].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
ax[0].set_title('Derivative raw PYS')
ax[0].legend(loc='best')
ax[0].invert_xaxis()

ax[1].scatter(pys.x, pys.y, alpha=0.3,label="PYS", color="tab:gray", s=10)
if smooth_SG==True or smooth_gauss==True:
    ax[1].plot(pys.x, pys.y_smooth, label="PYS smooth", color="tab:gray")
# ax[1].plot(pys.x, pys.y_sg_dif, label="DPYS", color="tab:orange")
# その他設定
ax[1].set_yscale('log')
ax[1].set_ylabel("Intensity (cps)")
ax[1].set_xlabel("Photon Energy (eV)") # labelがあれば追加。
ax[1].set_title('Derivative raw PYS')
ax[1].legend(loc='best')
ax[1].invert_xaxis()

################################################################
# --- CFS-YSとPYSの比較 ---

# --- BG処理なし PYS ---
# plot
fig, ax = plt.subplots(1, 2, figsize=(8, 3))
ax[0].plot(cfsys.x, cfsys.y, label="CFS", color="tab:blue")
ax[0].plot(pys.x, pys.y_sg_dif*mult_y_pys_dif, label="DPYS", color="tab:orange")#, s=10)
if plot_2d_pys:
    ax[0].scatter(pys.x, pys.y_sg_dif_dif*mult_y_pys_dif_dif, label="2DPYS", color="tab:red", s=10)

ax[0].set_ylabel("Intensity (cps)")
ax[0].set_xlabel("Binding Energy from VL (eV)") # labelがあれば追加。

ax[0].set_title('CFS-YS vs. DPYS (Raw data)')
ax[0].legend(loc='best')
ax[0].invert_xaxis()


ax[1].plot(cfsys.x, cfsys.y, label="CFS", color="tab:blue")
ax[1].plot(pys.x, pys.y_sg_dif*mult_y_pys_dif, label="DPYS", color="tab:orange")#, s=10)
if plot_2d_pys:
    ax[1].scatter(pys.x, pys.y_sg_dif_dif*mult_y_pys_dif_dif, label="2DPYS", color="tab:red", s=10)
ax[1].set_yscale('log')

ax[1].set_ylabel("Intensity (cps)")
ax[1].set_xlabel("Binding Energy from VL (eV)") # labelがあれば追加。

ax[1].set_title('CFS-YS vs. DPYS (Raw data)')
ax[1].legend(loc='best')
ax[1].invert_xaxis()

plt.tight_layout()
plt.show()

#####################################################################
# --- output ---
if save_output:
    import matplotlib
    matplotlib.use('Agg')  # 描画はファイル保存に限る（GUIウィンドウ表示なし）
    import matplotlib.pyplot as plt
    
    # folder作成
    output_folder_name = f'STPy_{VERSION}_DerivativePYS'
    output_folder_name=output_folder_name.replace('.','_')
    output_folder_path = base_path / output_folder_name
    rpa.create_folder_at_current_path(output_folder_path, output_folder_name)

    # fileのpath作成
    # 元のファイル名と拡張子に分割
    n = 0
    name, ext = os.path.splitext(filename_cfs)
    output_file_path = output_folder_path / f'out_{name}_{n}{ext}'

    # ファイルが存在するか確認して連番で保存
    
    while os.path.exists(output_file_path):
        new_filename = f'{name}_{n}{ext}'  # 例: file_1.txt, file_2.txt
        output_file_path = output_folder_path / f'out_{new_filename}'
        n += 1

    def save(savefilepath):    
        # ヘッダー作成
        added_header=[] #テキストファイルに出力する実験条件などを格納する変数

        # info
        added_header.append('Author: R Nakazawa')
        added_header.append('Contact: https://www.researchgate.net/profile/Ryotaro-Nakazawa')
        added_header.append(f"Version: {VERSION}")
        added_header.append("--- info ---")
        added_header.append(f"SG smoothing\t{smooth_SG}")
        if smooth_SG:
            added_header.append(f'order\t{sg_order}')
            added_header.append(f'iteration\t{sg_iteration}')
            added_header.append(f'points\t{sg_window_length}')
        added_header.append(f"Gaussian smoothing\t{smooth_gauss}")
        if smooth_gauss:
            added_header.append(f'FWHM\t{FWHM}')
        added_header.append('')
        added_header.append('DATA:')

        # saveする数値データ作成
        data = [] # テキストファイルに出力する数値データを格納するリスト
        label = ['PE_PYS\tY_PYS\tY_DPYS\tY_2DPYS']

        for i in range(len(pys.x)):
            data.append(f'{pys.x[i]}\t{pys.y[i]}\t{pys.y_sg_dif[i]}\t{pys.y_sg_dif_dif[i]}')
                    
        # output file全体
        output_lines= added_header + label + data

        with open(savefilepath, 'w', errors='replace', encoding='utf-8') as f:
            for line in output_lines:
                f.write(line + '\n')

    # save
    if not os.path.isfile(output_file_path): # saveファイルが重複しない場合はsave
        save(output_file_path)
        print(f"Data was saved to {output_file_path}.")
        print("Data was saved.")
    else: # saveファイルが存在する場合、上書きするか確認する
        overwrite = rpa.ask_me("Confirmation of save", "Do you want to overwrite existing file? (y/n)") # popup
        if overwrite == 'y': # yesを選択すればsave
            save(output_file_path)
            print(f"Data was saved to {output_file_path}.")
            print("Data was saved.")
        else: # noを選択すれば保存しない
            print('Aborted.')    
