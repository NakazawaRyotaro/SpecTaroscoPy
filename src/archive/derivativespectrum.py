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




# -------------------- 初期条件 --------------------
smooth_SG=False # Savitzky-Golay smoothing
smooth_gauss=True # Gaussian smoothing
save_output = False # saveするか (saveしないとき図が出力される)

# ファイル名
filename_cfs = '' # D2

# 読み込みラベル名
x_legend_cfs = 'X'
y_legend_cfs = 'Y'

# SG smoothing
sg_order=2
sg_window_length=3 # 奇数で指定
sg_iteration=3

# Gaussian smoothing
FWHM=0.2
background=0

# plotパラメータ
# 生データ、スムージングデータの範囲
y_min = 0
y_max = 400
x_min = 1.5
x_max = 4.5
# 2次微分範囲
y_min_dif_dif = -3000
y_max_dif_dif = 3000
x_min_dif_dif = 1.5
x_max_dif_dif = 4.5

########################################################################
if save_output:
    import matplotlib.pyplot
    matplotlib.use('Agg')  # 描画はファイル保存に限る（GUIウィンドウ表示なし）
#######################################################################
# --- ファイル読み込み ---
# ファイル選択ダイアログを表示して、ファイルを選択
cfsys=Spectrum()
cfsys.read_labels_from_file_auto()
print(cfsys.label_list)
cfsys.load_xy_data_from_file_auto(x_legend=cfsys.label_list[0], y_legend=cfsys.label_list[1], plot_spectrum=False)

################################################################
# --- PYS -> DPYS, 2DPYS ---
# --- BG処理なし PYS ---
# SG smoothing
if smooth_SG:
    cfsys.smooth_spectra_by_SG(cfsys.y, sg_order, sg_window_length, sg_iteration) # 生
    cfsys.y_smooth = copy.deepcopy(cfsys.y_sg_lst[-1])
# gaussainスムージング
elif smooth_gauss:
    cfsys.generate_spread_function_for_deconvolution(cfsys.x, 'Gaussian', FWHM)
    print(cfsys.s)
    cfsys.y_smooth = rpa.conv(cfsys.y, cfsys.s, step=cfsys.x_step)
else:
    cfsys.y_smooth = cfsys.y
# 微分
cfsys.y_sg_dif=np.gradient(cfsys.y_smooth, cfsys.x, edge_order=1)
# 二階微分
cfsys.y_sg_dif_dif=np.gradient(cfsys.y_sg_dif, cfsys.x, edge_order=1)
# plot

fig, ax = plt.subplots(2, 1, figsize=(3, 8))
# 生データとスムージングデータ
ax[0].scatter(cfsys.x, cfsys.y, alpha=0.3,label="Y", color="tab:gray", s=10)
ax[0].plot(cfsys.x, cfsys.y_smooth, label="Y_smooth", color="tab:gray")
# その他設定
ax[0].plot([min(cfsys.x), max(cfsys.x)], [0,0], color="black", linewidth=1, zorder=0)
ax[0].set_ylabel("Y")
ax[0].set_xlabel("X") # labelがあれば追加。
ax[0].set_title('')
ax[0].legend(loc='best')
ax[0].invert_xaxis()
ax[0].set_ylim(y_min, y_max)
ax[0].set_xlim(x_min, x_max)

# 二階微分
ax[1].plot(cfsys.x, cfsys.y_sg_dif_dif, label="Y_dif_dif", color="tab:blue")
# その他設定
ax[1].set_ylim(y_min_dif_dif, y_max_dif_dif)
ax[1].set_xlim(x_min_dif_dif, x_max_dif_dif)
ax[1].set_ylabel("Y")
ax[1].set_xlabel("X") # labelがあれば追加。
ax[1].set_title('')
ax[1].legend(loc='best')
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
    # from pathlib import Path
    base_path = str(Path(cfsys.path).expanduser().resolve().parent) # 例: "C:\\work\\data" や "/Users/you/work/data" # pathのうち、ファイル名 data を除いた部分を取得
    
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

        for i in range(len(cfsys.x)):
            data.append(f'{cfsys.x[i]}\t{cfsys.y[i]}\t{cfsys.y_sg_dif[i]}\t{cfsys.y_sg_dif_dif[i]}')
                    
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
