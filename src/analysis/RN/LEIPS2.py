import numpy as np
import pandas as pd
import scipy
import scipy.signal as signal
import matplotlib.pyplot as plt
from pathlib import Path
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog
import os
from pathlib import Path
import customtkinter as ctk

# 自作モジュールのインポート（srcを基準にした絶対import）
from RyoPy import defs_for_analysis as rpa

##########################################################################################################################################
# input parameters ########################################################################################################################
##########################################################################################################################################

# 入力するファイルのパスを指定 #################
# ""の中にファイルの絶対pathをコピペする 
# ex) filepath = Path("/Users/name/Documents/...(略).../解析するcsvfile.csv")
# filepath = "Pupup window" # GUI
# filepath = Path("ここにコピペ")

filepath = Path("/Users/ryotaro/Documents/実験データ/SpecTaroscoPy/examples_for_RN/LEIPS2/testLEIPS2.txt")

# パラメータ #############################


##########################################################################################################################################
# def ####################################################################################################################################
########################################################################################################################################## 

def ask_filepath():
    # appearance（任意）
    ctk.set_appearance_mode("System")   # "Light" / "Dark"
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("File path input")
    app.attributes("-topmost", True)

    result = {"path": None}

    def submit():
        result["path"] = entry.get()
        app.destroy()

    def cancel():
        app.destroy()

    # --- widgets ---
    label = ctk.CTkLabel(
        app,
        text=(
            "解析するCSVファイルのフルパスをここにコピペしてください。\n"
            "labelはxとyにしてください。\n"
            "例: /Users/name/Documents/data/example.csv"
        ),
        justify="left"
    )
    label.pack(padx=20, pady=(20, 10), anchor="w")

    entry = ctk.CTkEntry(app, width=300)
    entry.pack(padx=10, pady=(0, 10))
    entry.focus_set()

    button_frame = ctk.CTkFrame(app)
    button_frame.pack(pady=(0, 10))

    ok_btn = ctk.CTkButton(button_frame, text="OK", width=120, command=submit)
    ok_btn.pack(side="left", padx=10)

    cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=120, command=cancel)
    cancel_btn.pack(side="left", padx=10)

    # EnterキーでOK
    app.bind("<Return>", lambda event: submit())
    app.bind("<Escape>", lambda event: cancel())

    app.mainloop()
    
    if result["path"] is None or result["path"].strip() == "":
        raise SystemExit("Canceled")

    return Path(result["path"].strip())

def get_rmse(y, y0):
    return np.sqrt(1/len(y)*np.sum((y-y0)**2))

def Detect_peak_of_SGspectrum_by_SecondDerevetive(x, ysg_lst, sg_point_lst, order):
    # 二次微分ピークの情報
    ddy_peak_lst=[] #ddyの値
    ite_ddy_peak_lst_1D=[] #iteration
    o_ddy_peak_lst=[] #deconvの値
    x_ddy_peak_lst=[] #エネルギー

    #二次微分のピーク検出
    
    dy=np.gradient(ysg_lst)
    dy=dy[1]
    ddy=np.gradient(dy)
    ddy_lst=ddy[1]
    minid_ddy = signal.argrelmin(ddy_lst, order=order,axis=1) #最小値のindexの取得
    
    ite_ddy_peak_lst_1D=minid_ddy[0] #iterationのリスト
    
    for j in range(len(minid_ddy[1])):
        x_ddy_peak_lst.append(x[minid_ddy[1][j]].tolist()) #energyのリスト
    for j in range(len(minid_ddy[1])):
        ddy_peak_lst.append(ddy_lst[minid_ddy[0][j], minid_ddy[1][j]].tolist()) #ddyのリスト
    for j in range(len(minid_ddy[1])):
        o_ddy_peak_lst.append(ysg_lst[minid_ddy[0][j], minid_ddy[1][j]].tolist()) #oのリスト
    
    # iterationで区切られた多次元配列にする
    ite_ddy_peak_lst, x_ddy_peak_lst=Rearrange_lsts(ite_ddy_peak_lst_1D, x_ddy_peak_lst)
    ite_ddy_peak_lst, o_ddy_peak_lst=Rearrange_lsts(ite_ddy_peak_lst_1D, o_ddy_peak_lst)
    ite_ddy_peak_lst, ddy_peak_lst  =Rearrange_lsts(ite_ddy_peak_lst_1D, ddy_peak_lst)
    
    # ite_ddy_peak_lstはSGスムージングのパラメータのpointsのことです。よって、sg_point_lstを使って変更する。
    for i in range(len(sg_point_lst)):
        ite_ddy_peak_lst[i] = [sg_point_lst[i]] * len(ite_ddy_peak_lst[i])
    
    #ite_ddy_peak_lst = [[x_[0] + 1, x_[1] + 1] for x_ in ite_ddy_peak_lst] # plotのためiterationを1から始める
    
    return ddy_lst, ite_ddy_peak_lst, x_ddy_peak_lst, o_ddy_peak_lst, ddy_peak_lst

def Make_savitzky_goley_lst(x, # x
                            y, # y
                            sg_point_min, # pointsのmin
                            sg_point_max, # pointsのmax
                            sg_poly, # 時数
                            sg_times, # repeat
                            x_rms_min_eV, # 残差を計算するときのxの下限
                            x_rms_max_eV): 
    
    # SG法のpoint数の配列
    sg_point_lst = np.round(np.arange(sg_point_min, sg_point_max+0.2, 2)) # 奇数にすること
    #print(sg_point_lst)
    
    # 初期化
    y_sg_lst = np.zeros( (len(sg_point_lst), len(y)) )
    rms_sg = np.zeros(len(sg_point_lst))

    #差分を取る領域をindexに変換
    x_rms_min=idx_of_the_nearest(x, x_rms_min_eV) #indexに変換
    x_rms_max=idx_of_the_nearest(x, x_rms_max_eV) #indexに変換
    
    for j in range(len(sg_point_lst)):
        y_sg_lst[j] = sg_fil(y, sg_point_lst[j], sg_poly, sg_times)
        
         # 残差 model data
        rms_sg[j]=np.sqrt(np.average((y[x_rms_min:x_rms_max]-y_sg_lst[j][x_rms_min:x_rms_max])**2)) #2乗平均平方根誤差     

    rms_sg=np.array(rms_sg)
    
    return y_sg_lst, rms_sg, sg_point_lst

def read_leips_data(path):

    def get_value(target):
        for line in lines:
            items = line.strip("\n").split("\t")

            if target in items:
                i = items.index(target)
                return items[i + 1]

        raise ValueError(f"{target} was not found.")

    # fileを開く
    with open(path, 'r', encoding='utf-8', errors='replace') as file:
        lines = file.readlines()

    # ==========================================
    # 測定条件の取得
    # ==========================================
    start = float(get_value("start / eV"))
    stop = float(get_value("stop / eV"))
    step = float(get_value("step / eV"))
    cathode_potential = float(get_value("cathode potential/V"))

    dwell = float(get_value("Dwell / s"))
    scans = int(get_value("Number of Scans"))

    # ==========================================
    # データ開始位置を探す
    # ==========================================
    header_index = next(
        i for i, line in enumerate(lines)
        if "energy/eV\tcurrent/uA\tintensity/count" in line
    )

    data_start_index = header_index + 1

    # ==========================================
    # データ読み込み
    # ==========================================
    current = []
    intensity = []

    for line in lines[data_start_index:]:

        # 空行になったらデータ終了
        if not line.strip():
            break

        items = line.strip().split("\t")

        # 数値化
        values = [float(x) for x in items if x != ""]

        # 3 × scans 個なければデータ行ではない
        if len(values) < 3 * scans:
            break

        # energy は読み捨てる
        current.append(values[scans:2 * scans])
        intensity.append(values[2 * scans:3 * scans])

    current = np.array(current).T
    intensity = np.array(intensity).T
    intensity = intensity / dwell  # count/s に変換


    # ==========================================
    # X軸を生成
    # X = cathode - start + step * i
    # ==========================================
    n_points = len(current[0])

    X = cathode_potential - start + step * np.arange(n_points)

    return {
        "X": X,
        "current": current,
        "intensity": intensity,
        "start": start,
        "stop": stop,
        "step": step,
        "cathode_potential": cathode_potential,
        "dwell": dwell,
        "scans": scans,
    }

def calculate_average_intensity(intensity, start=0, end=None):
    """
    指定したscan範囲のLEIPSを平均する。

    intensity.shape = (n_scans, n_points)
    """
    return np.mean(intensity[start:end, :], axis=0)

def differential_leet(X, current):

    n_scans, n_points = current.shape

    # =========================================
    # LEETを一次微分
    # current.shape = (scan, X)
    # なので X方向は axis=1
    # =========================================

    return np.gradient(current, X, axis=1)

def shift_array(y, shift):
    """
    1次元配列を整数点だけシフトする。
    空いた部分は NaN にする。

    shift > 0 : 右へシフト
    shift < 0 : 左へシフト
    """

    result = np.full(len(y), np.nan, dtype=float)

    if shift > 0:
        result[shift:] = y[:-shift]

    elif shift < 0:
        result[:shift] = y[-shift:]

    else:
        result[:] = y

    return result

def align_leet_leips(X, current, intensity,
                     ref_scan=0,
                     xmin=None,
                     xmax=None):

    """
    LEETの一次微分のcross-correlationから横ずれを求め、
    LEET(current)とLEIPS(intensity)の両方を補正する。

    Parameters
    ----------
    X : ndarray
        エネルギー軸
        shape = (n_points,)

    current : ndarray
        LEET
        shape = (n_scans, n_points)

    intensity : ndarray
        LEIPS
        shape = (n_scans, n_points)

    ref_scan : int
        基準にするscan番号。
        Pythonなので
        ref_scan=0 → scan 1
        ref_scan=1 → scan 2

    xmin, xmax : float
        cross-correlationに使用するLEET領域。
        Noneなら全領域。

    Returns
    -------
    current_aligned : ndarray
        シフト補正後のLEET
        shape = (n_scans, n_points)

    intensity_aligned : ndarray
        シフト補正後のLEIPS
        shape = (n_scans, n_points)

    shifts_point : ndarray
        各scanを実際に何点動かしたか

    shifts_eV : ndarray
        各scanを実際に何eV動かしたか
    """

    n_scans, n_points = current.shape

    # =========================================
    # LEETを一次微分
    # current.shape = (scan, X)
    # なので X方向は axis=1
    # =========================================

    dcurrent = np.gradient(current, X, axis=1)

    # =========================================
    # cross-correlationを計算するX領域
    # =========================================

    mask = np.ones(len(X), dtype=bool)

    if xmin is not None:
        mask &= X >= xmin

    if xmax is not None:
        mask &= X <= xmax

    # =========================================
    # 基準LEETの一次微分
    # =========================================

    reference = dcurrent[ref_scan, mask]

    # DC成分を除去
    reference = reference - np.mean(reference)

    # =========================================
    # 出力配列
    # =========================================

    current_aligned = np.full_like(
        current,
        np.nan,
        dtype=float
    )

    intensity_aligned = np.full_like(
        intensity,
        np.nan,
        dtype=float
    )

    dcurrent_aligned = np.full_like(
        dcurrent,
        np.nan,
        dtype=float
    )

    shifts_point = np.zeros(n_scans, dtype=int)
    shifts_eV = np.zeros(n_scans)

    step = X[1] - X[0]

    # =========================================
    # 各scanをreferenceに合わせる
    # =========================================

    for j in range(n_scans):

        target = dcurrent[j, mask]

        # DC成分を除去
        target = target - np.mean(target)

        # cross-correlation
        corr = np.correlate(
            target,
            reference,
            mode="full"
        )

        # targetがreferenceに対して何点ずれているか
        lag = np.argmax(corr) - (len(reference) - 1)

        # 補正方向
        correction = -lag

        shifts_point[j] = correction
        shifts_eV[j] = correction * step

        # LEETとLEIPSに同じシフトを適用
        current_aligned[j, :] = shift_array(
            current[j, :],
            correction
        )

        intensity_aligned[j, :] = shift_array(
            intensity[j, :],
            correction
        )

        dcurrent_aligned[j, :] = shift_array(
            dcurrent[j, :],
            correction
        )

    return (
        current_aligned,
        intensity_aligned,
        shifts_point,
        dcurrent,
        dcurrent_aligned
    )

def make_savefile_folder(path, name="STPy_LEIPS2"):
    directory_path = os.path.dirname(path) # ディレクトリパスを取得
    
    foldername=name
    foldername=foldername.replace('.','_')
    rpa.create_folder_at_current_path(path, foldername)
    
    # filepath 作成
    savefile_path = os.path.join(directory_path, foldername, self.savefile_entry.get())


    def save_data(self, savefile_path, base_legendname, mode, save_peaks=False):
        # txt fileの中身
        filename=base_legendname.replace(".txt","")

        def save(savefile_path, filename=filename):
            # DATA: 以降の行を取得
            data_index = self.image[0].l.index('DATA:') + 1
            # print(data_index)
            data_lines = self.image[0].l[data_index:]

            # ヘッダー作成
            added_header=[] #テキストファイルに出力する実験条件などを格納する変数

            added_header.append('')
            # title
            if mode=='2der':
                added_header.append("[SpecTaroscoPy — Second Derivative]")
            elif mode=='curX' or mode=='curXY':
                added_header.append("[SpecTaroscoPy — Curvature]")
            # info
            added_header.append('Author\tR Nakazawa')
            added_header.append('Contact\tnakazawa@ims.ac.jp')
            added_header.append(f"Version\t{VERSION_NUMBER}")
            added_header.append("--- info ---")
            added_header.append(f"User\t{USER}")
            added_header.append(f'File\t{self.image[0].filename}')     
            added_header.append(f"Smoothing Method\t{self.smoothing_method}")
            added_header.append("Smoothing Params\t" + ' '.join(map(str, self.smoothing_param_values)))
            added_header.append("Intensity Offset\t" + ' '.join(map(str, self.y_2der_offset)))
            # curvature
            if mode=='curX' or mode=='curXY':
                added_header.append(f'Curvature Method\t{self.curvature_method}')
                added_header.append('Curvature Parameters\t' + ' '.join(map(str, self.curvature_param_values)))

            # paek detectした時
            if save_peaks:
                added_header.append(f"Detect Peak\t{self.detect_peak_checkbox.get()}")
                added_header.append(f"Order (Detect Peak)\t{self.order_detect_peak}")
                added_header.append(f"X Min Detect Peak\t{self.x_min_entry.get()}")
                added_header.append(f"X Max Detect Peak\t{self.x_max_entry.get()}")
            
            added_header.append("")
            added_header.append("DATA:")

            # saveする数値データ作成
            data = [] # テキストファイルに出力する数値データを格納するリスト

            # ラベル追加
            # 数値データにラベルがあるか確認。ラベル付きの場合はラベルの末尾に2Der追記する。
            # label=[]
            # # DATA: の次の1行を取得
            # next_DATA_line = self.image[0].l[data_index].strip().split()
            # if not all(element.replace('.', '', 1).isdigit() for element in next_DATA_line):
            #     label_ = []
            #     label_.append(next_DATA_line)
            #     # 各要素の末尾に文字列を追記
            #     if mode=='2der' and save_peaks==False: #二次微分解析の場合
            #         label_ = [[f"{element}2Der" for element in label] for label in label_]
            #     # print("Labels:", label_)
            #     elif mode=='curX' and save_peaks==False: #Curvature解析の場合
            #         label_ = [[f"{element}CurX" for element in label] for label in label_]
            #     label="\t".join(label_[0]) if label_ else ""
            # else:
            #     pass

            # ---- helper functions (class内でも外でもOK) ----
            def _is_numeric_row(row: list[str]) -> bool:
                """rowの全要素が float に変換できるなら True（-1.2, 1e-3, NaN もOK）"""
                try:
                    for x in row:
                        float(x)
                    return True
                except ValueError:
                    return False
            def _decorate_labels(labels: list[str], mode: str, save_peaks: bool) -> list[str]:
                """mode と save_peaks に応じてサフィックスを付ける（必要なときだけ）"""
                if save_peaks:
                    return labels
                suffix_map = {
                    "2der": "2Der",
                    "curX": "CurX",
                }
                suffix = suffix_map.get(mode, "")
                if not suffix:
                    return labels
                return [f"{x}{suffix}" for x in labels]

            # ---- main logic (あなたの元コードの置き換え部分) ----
            label = ""  # 最終的に出す「タブ区切りラベル文字列」。無ければ空文字。

            # DATA: の次の1行を取得（想定）
            row = self.image[0].l[data_index].strip().split()

            # ラベル行かどうか判定：全要素が数値ならデータ行→ラベル無し
            if not _is_numeric_row(row):
                labels = row[:]  # 1次元のまま
                labels = _decorate_labels(labels, mode, save_peaks)
                label = "\t".join(labels) # この後、必要なら label を使う
                print(label)
            
            
            
            # データ追加
            # peak detect dataのsave
            if save_peaks:
                data.append(f'yc_{filename}_Peak\tx_{filename}_Peak\t{filename}_Peak\t{filename}_PeakOffset')
                for i in range(len(self.peak_energy_lst)):
                    for j in range(len(self.peak_energy_lst[i])):
                        y_slice_center=1
                        if self.image[0].y_slice_center_edcs!=[]:
                            y_slice_center=self.image[0].y_slice_center_edcs[i]
                        data.append(f'{y_slice_center}\t{self.peak_energy_lst[i][j]}\t{self.edcs_peak_intensity_lst[i][j]}\t{self.edcs_peak_intensity_lst[i][j]+self.y_edc_offset[i]}')
            
            else:
                # 二次微分解析の場合
                if mode=='2der':
                    z=self.z_second_derivative
                elif mode=='curX':
                    z=self.z_curvature
                
                # save
                if label != "":
                    data.append(label) # ラベル追加
                for i in range(len(z[0])):
                    data_lst = [f"{self.x[i]}"]
                    for j in range(len(z)):
                        data_lst.append(f"{z[j][i]}")
                    # data_lstを適切にフォーマットして文字列に変換
                    data.append("\t".join(data_lst))
            
            # output file全体
            output_lines= self.image[0].l[:data_index-2] + added_header + data

            with open(savefile_path, 'w', errors='replace', encoding='utf-8') as f:
                for line in output_lines:
                    # print(line)
                    f.write(line + '\n')

        # save
        if not os.path.isfile(savefile_path): # saveファイルが重複しない場合はsave
            save(savefile_path)
            print("Data was saved.")
        else: # saveファイルが存在する場合、上書きするか確認する
            overwrite = rpa.ask_me("Confirmation of save", "Do you want to overwrite existing file? (y/n)") # popup
            if overwrite == 'y': # yesを選択すればsave
                save(savefile_path)
                print("Data was saved.")
            else: # noを選択すれば保存しない
                print('Aborted.')    



##########################################################################################################################################
# 実行部 ##################################################################################################################################
##########################################################################################################################################

if filepath == "Pupup window":
    filepath = ask_filepath()
    print("filepath  :", filepath)

path = Path(filepath)
folder = path.parent.name
input_file = path.name

print("path        :", path)
print("folder      :", folder)
print("input_file  :", input_file)

leips2 = read_leips_data(path)

x = leips2["X"]
y_leet = leips2["current"]
y_leips = leips2["intensity"]

print("X:", len(x))
print("y_leet:", len(y_leet))

idx_ref_scan = 0  # ref_scan (1スタート)

# LEIPSの平均を計算してプロット
y_leips_avg = calculate_average_intensity(y_leips)

# LEETの微分
y_leet_dif = differential_leet(x, y_leet)

fig_leet, ax_leet = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
for i in range(len(y_leet)):
    ax_leet[0].plot(x, y_leet[i])
ax_leet[0].set_title("Raw LEET: " + input_file)
ax_leet[1].set_title("Aligned LEET")
ax_leet[0].set_ylabel("Current (uA)")
ax_leet[1].set_ylabel("Current (uA)")
ax_leet[1].set_xlabel("Energy (eV)")
plt.tight_layout()

fig_leet_dif, ax_leet_dif = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
for i in range(len(y_leet)):
    ax_leet_dif[0].plot(x, y_leet_dif[i]) #, label=f"{i}")
ax_leet_dif[0].set_title("Raw LEET_DIF: " + input_file)
ax_leet_dif[1].set_title("Aligned LEET")
ax_leet_dif[0].set_ylabel("Current (uA)")
ax_leet_dif[1].set_ylabel("Current (uA)")
ax_leet_dif[1].set_xlabel("Energy (eV)")
plt.tight_layout()

fig_leips, ax_leips = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
for i in range(len(y_leips)):
    ax_leips[0].plot(x, y_leips[i]) #, label=f"{i}")
ax_leips[0].plot(x, y_leips_avg, color="black", linewidth=2, label="Average")
ax_leips[0].set_title("Raw LEIPS: " + input_file)
ax_leips[1].set_title("Aligned LEIPS")
ax_leips[0].set_ylabel("Intensity (cps)")
ax_leips[1].set_ylabel("Intensity (cps)")
ax_leips[1].set_xlabel("Energy (eV)")
ax_leips[0].legend()
plt.tight_layout()


idx_ref_scan = 0  # ref_scan (1スタート)
# LEETの微分をつかってスペクトルをシフトさせる。
y_leet_shifted, y_leips_shifted, shifts_point, y_leet_dif, y_leet_dif_shifted = align_leet_leips(x, 
                                                                                y_leet, 
                                                                                y_leips, 
                                                                                ref_scan=idx_ref_scan)

# LEIPSの平均を計算してプロット
y_leips_shifted_avg = calculate_average_intensity(y_leips_shifted)

for i in range(len(y_leips)):
    ax_leet[1].plot(x, y_leet_shifted[i])
    ax_leet_dif[1].plot(x, y_leet_dif_shifted[i])
    ax_leips[1].plot(x, y_leips_shifted[i])
ax_leet[0].plot(x, y_leet[idx_ref_scan], label=f"{idx_ref_scan+1}", color="Black", linewidth=2)
ax_leet[1].plot(x, y_leet_shifted[idx_ref_scan], label=f"{idx_ref_scan+1}", color="Black", linewidth=2)
ax_leet_dif[0].plot(x, y_leet_dif[idx_ref_scan], label=f"{idx_ref_scan+1}", color="Black", linewidth=2)
ax_leet_dif[1].plot(x, y_leet_dif_shifted[idx_ref_scan], label=f"{idx_ref_scan+1}", color="Black", linewidth=2)
ax_leips[1].plot(x, y_leips_shifted_avg, color="black", linewidth=2, label="Average")

ax_leips[1].legend()
ax_leet[0].legend()
ax_leet[1].legend()
ax_leet_dif[0].legend()
ax_leet_dif[1].legend()

plt.show()

