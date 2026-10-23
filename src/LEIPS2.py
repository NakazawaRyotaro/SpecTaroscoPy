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

# srcのディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent

# print(CURRENT_PATH)
# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")

# ファイル選択するときの初期値
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
USER, has_USER = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type='str')
VERSION_NUMBER, hoge=rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "version", type="str")

##########################################################################################################################################
# input parameters ########################################################################################################################
##########################################################################################################################################

# 入力するファイルのパスを指定 #################
# ""の中にファイルの絶対pathをコピペする 
# ex) filepath = Path("/Users/name/Documents/...(略).../解析するcsvfile.csv")
filepath = "Pupup window" # GUI
# filepath = Path("/Users/ryotaro/Documents/実験データ/20260809_PBFDO_pristine/rawdata/N3/20260812-36-pristine_N3_FineScan_257nm.txt")

# パラメータ #############################
X_EF_ref=2.20
WAVELENGTH_BPF_ref=257

WAVELENGTH_BPF="Pupup window" # GUI
# WAVELENGTH_BPF=232

# leetの微分を使ってシフトさせるときの基準scan番号 (index表記: 0スタート)
idx_ref_scan = 0 # ref_scan

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
            "解析するtxtファイルのフルパスをここにコピペしてください。\n"
            "例) /Users/name/Documents/data/example.txt"
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

    return (result["path"])

def ask_wavelength():
    # appearance（任意）
    ctk.set_appearance_mode("System")   # "Light" / "Dark"
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Wavelength input")
    app.attributes("-topmost", True)

    result = {"wavelength": None}

    def submit():
        result["wavelength"] = entry.get()
        app.destroy()

    def cancel():
        app.destroy()

    # --- widgets ---
    label = ctk.CTkLabel(
        app,
        text=(
            "検出波長を入力してください。\n"
            "例) 257 nm -> 257 と入力。"
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
    
    if result["wavelength"] is None or result["wavelength"].strip() == "":
        raise SystemExit("Canceled")

    return float(result["wavelength"].strip())

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
    try:
        coordinate = get_value("(x, y, z)")
    except ValueError:
        try:
            coordinate = get_value(str("(x, y, z)"))
        except ValueError:
            coordinate = "N/A"
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
        "coordinate": coordinate,
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

def make_savefile_folder(path, foldername="STPy_LEIPS2"):
    directory_path = os.path.dirname(path) # ディレクトリパスを取得

    rpa.create_folder_at_current_path(path, foldername)

def save_data(
    savefile_path,
    base_legendname,
    x_step,
    shifted_point, 
    x,
    Eb_EF,
    y_leips_shifted_avg,
    y_leips_shifted,
    y_leet_shifted,
    y_leet_dif_shifted
):
    """
    保存するデータ:

    x                     : shape (n,)
    Eb_EF                 : shape (n,)
    y_leips_shifted_avg   : shape (n,)
    y_leips_shifted       : shape (n, m)
    y_leet_shifted        : shape (n, m)
    y_leet_dif_shifted    : shape (n, m)

    出力:
        n行 × (3 + 3m)列

    columns:
        X_bl
        EF_bl
        Y_LEIPS_bl
        Y_LEIPS_sft_bl_1 ... Y_LEIPS_sft_bl_m
        Y_LEET_sft_bl_1  ... Y_LEET_sft_bl_m
        Y_LEET_dif_sft_bl_1 ... Y_LEET_dif_sft_bl_m
    """

    bl = base_legendname

    def save(savefile_path):

        # ------------------------------------------------------------------
        # header
        # ------------------------------------------------------------------
        added_header = []

        added_header.append("[SpecTaroscoPy - LEIPS2]")
        added_header.append('Author\tR Nakazawa')
        added_header.append('Contact\tnakazawa@chiba-u.jp')
        added_header.append(f"Version\t{VERSION_NUMBER}")
        added_header.append("--- info ---")
        added_header.append(f"User\t{USER}")
        added_header.append(f"Input file\t{filepath}")
        added_header.append(f"scan number\t{scans}")
        added_header.append(f"dwell time\t{dwell} s")
        added_header.append(f"coordinate\t{coordinate}")
        added_header.append(f"X Step\t{x_step}")
        added_header.append("Offset Energy\t" + "\t".join(map(str, shifted_point * x_step)))

        added_header.append("")
        added_header.append("DATA:")

        # ------------------------------------------------------------------
        # array size check
        # ------------------------------------------------------------------
        n = len(x)

        m = y_leips_shifted.shape[0]

        if not (
            y_leet_shifted.shape[0] == m
            and y_leet_dif_shifted.shape[0] == m
        ):
            raise ValueError("The number of scans m is inconsistent.")

        # ------------------------------------------------------------------
        # legend
        # ------------------------------------------------------------------
        labels = [
            f"X_{bl}",
            f"EF_{bl}",
            f"Y_LEIPS_sft_{bl}",
        ]

        # scan number: 1, 2, ..., m
        labels += [
            f"Y_LEIPS_sft_{bl}_{j + 1}"
            for j in range(m)
        ]

        labels += [
            f"Y_LEET_sft_{bl}_{j + 1}"
            for j in range(m)
        ]

        labels += [
            f"Y_LEET_dif_sft_{bl}_{j + 1}"
            for j in range(m)
        ]

        label = "\t".join(labels)

        # ------------------------------------------------------------------
        # numerical data
        # ------------------------------------------------------------------
        save_array = np.column_stack([
            x,
            Eb_EF,
            y_leips_shifted_avg,
            y_leips_shifted.T,
            y_leet_shifted.T,
            y_leet_dif_shifted.T,
        ])

        data = []

        for row in save_array:
            data.append("\t".join(map(str, row)))

        # ------------------------------------------------------------------
        # output
        # ------------------------------------------------------------------
        output_lines = (
            added_header
            + [label]
            + data
        )

        with open(
            savefile_path,
            'w',
            errors='replace',
            encoding='utf-8'
        ) as f:
            for line in output_lines:
                f.write(line + '\n')

    # ----------------------------------------------------------------------
    # save
    # ----------------------------------------------------------------------
    if not os.path.isfile(savefile_path):
        save(savefile_path)
        print("Data was saved.")

    else:
        overwrite = rpa.ask_me(
            "Confirmation of save",
            "Do you want to overwrite existing file? (y/n)"
        )

        if overwrite == 'y':
            save(savefile_path)
            print("Data was saved.")
        else:
            print("Aborted.")

def convert_Ek_to_Eb(x, X_EF_ref, WAVELENGTH_BPF_ref, WAVELENGTH_BPF):
    """
    EkをEbに変換する。
    """
    
    PE_BPF_ref = np.round(1239.84193 / WAVELENGTH_BPF_ref, 4)
    PE_BPF = np.round(1239.84193 / WAVELENGTH_BPF, 4)
    X_EF = np.round(X_EF_ref + (PE_BPF - PE_BPF_ref), 4)

    print(f"PE@EF ({WAVELENGTH_BPF_ref} nm): {PE_BPF_ref} eV")
    print(f"PE@EF ({WAVELENGTH_BPF} nm): {PE_BPF} eV")
    print(f"Ek@EF ({WAVELENGTH_BPF_ref} nm) w.r.t. cathode vol: {X_EF_ref} eV")
    print(f"Ek@EF ({WAVELENGTH_BPF} nm) w.r.t. cathode vol: {X_EF} eV")

    return - (x - X_EF), X_EF


##########################################################################################################################################
# 実行部 ##################################################################################################################################
##########################################################################################################################################

if filepath == "Pupup window":
    filepath = ask_filepath()
    print("filepath  :", filepath)

path = Path(filepath)
folder = path.parent.name
input_file = path.name
base_legendname = path.stem

print("path        :", path)
print("folder      :", folder)
print("input_file  :", input_file)

if WAVELENGTH_BPF == "Pupup window":
    WAVELENGTH_BPF = ask_wavelength()
    print("wavelength  :", WAVELENGTH_BPF)

leips2 = read_leips_data(path)

x = leips2["X"]
scans = leips2["scans"]
dwell = leips2["dwell"]
coordinate = leips2["coordinate"]
y_leet = leips2["current"]
y_leips = leips2["intensity"]
x_step = leips2["step"]

print("X number:", len(x))
print("Scan number:", len(y_leet))

# LEIPSの平均を計算してプロット
y_leips_avg = calculate_average_intensity(y_leips)

# LEETの微分
y_leet_dif = differential_leet(x, y_leet)

# LEETの微分をつかってスペクトルをシフトさせる。
y_leet_shifted, y_leips_shifted, shifted_point, y_leet_dif, y_leet_dif_shifted = align_leet_leips(x, 
                                                                                y_leet, 
                                                                                y_leips, 
                                                                                ref_scan=idx_ref_scan)

# LEETを基準にシフトさせたLEIPSの平均を計算してプロット
y_leips_shifted_avg = calculate_average_intensity(y_leips_shifted, end=3)

Eb_EF, X_EF = convert_Ek_to_Eb(x, X_EF_ref, WAVELENGTH_BPF_ref, WAVELENGTH_BPF)

# 出力ファイルを格納するフォルダを作成
make_savefile_folder(path, foldername="STPy_LEIPS2")

# # save file 
save_data(
    path.parent / f"STPy_LEIPS2" / f"out_{base_legendname}.txt",
    base_legendname,
    x_step,
    shifted_point,
    x,
    Eb_EF,
    y_leips_shifted_avg,
    y_leips_shifted,
    y_leet_shifted,
    y_leet_dif_shifted)


fig_leet, ax_leet = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
for i in range(len(y_leet)):
    ax_leet[0].plot(x, y_leet[i])
ax_leet[0].set_title("Raw LEET:\n" + input_file)
ax_leet[1].set_title("Aligned LEET")
ax_leet[0].set_ylabel("Current (uA)")
ax_leet[1].set_ylabel("Current (uA)")
ax_leet[1].set_xlabel("Energy w.r.t. cathode voltage (eV)")
plt.tight_layout()

fig_leet_dif, ax_leet_dif = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
for i in range(len(y_leet)):
    ax_leet_dif[0].plot(x, y_leet_dif[i]) #, label=f"{i}")
ax_leet_dif[0].set_title("Raw LEET_DIF:\n" + input_file)
ax_leet_dif[1].set_title("Aligned LEET")
ax_leet_dif[0].set_ylabel("Current (μA)")
ax_leet_dif[1].set_ylabel("Current (μA)")
ax_leet_dif[1].set_xlabel("Energy w.r.t. cathode voltage (eV)")
plt.tight_layout()

fig_leips, ax_leips = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
for i in range(len(y_leips)):
    ax_leips[0].plot(x, y_leips[i]) #, label=f"{i}")
ax_leips[0].plot(x, y_leips_avg, color="black", linewidth=2, label="Average")
ax_leips[0].set_title("Raw LEIPS:\n" + input_file)
ax_leips[1].set_title("Aligned LEIPS")
ax_leips[0].set_ylabel("Intensity (cps)")
ax_leips[1].set_ylabel("Intensity (cps)")
ax_leips[1].set_xlabel("Energy w.r.t. cathode voltage (eV)")
ax_leips[0].legend()
plt.tight_layout()

print("Shifted point:", shifted_point*x_step, "eV")

# shifted dataをプロット
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
plt.tight_layout()

# shift量をプロット
fig_shifted_point, ax_shifted_point = plt.subplots(figsize=(4, 4))
for i in range(len(shifted_point)):
    ax_shifted_point.plot(i + 1, shifted_point[i] * x_step, "o", color="tab:blue")
ax_shifted_point.set_title("Offset Energy:\n" + input_file)
ax_shifted_point.set_ylabel("Energy (eV)")
ax_shifted_point.set_xlabel("Scan number")
plt.tight_layout()

# summary
fig_summary, ax_summary = plt.subplots(2, 1, figsize=(4, 8), sharex=True)
ax_summary[0].plot(x, y_leips_avg, color="black", linewidth=2, label="Average")
ax_summary[1].plot(x, y_leips_shifted_avg, color="black", linewidth=2, label="Average")
if X_EF is not None:
    ax_summary[0].axvline(X_EF, color="black", linestyle="--", label="Fermi level", zorder=1000)
    ax_summary[1].axvline(X_EF, color="black", linestyle="--", label="Fermi level", zorder=1000)
ax_summary[0].set_title("Raw LEIPS:\n" + input_file)
ax_summary[1].set_title("Aligned LEIPS")
ax_summary[0].set_ylabel("Intensity (cps)")
ax_summary[1].set_ylabel("Intensity (cps)")
ax_summary[1].set_xlabel("Energy w.r.t. cathode voltage (eV)")

# LEETの微分を右軸として追加
ax_summary_r0 = ax_summary[0].twinx()
ax_summary_r1 = ax_summary[1].twinx()

# LEET differential（基準スペクトルのみ）
ax_summary_r0.plot(
    x,
    y_leet_dif[idx_ref_scan],
    color="tab:blue",
    linewidth=2,
    label=f"LEET_DIF#{idx_ref_scan+1}",
    zorder=0
)

ax_summary_r1.plot(
    x,
    y_leet_dif_shifted[idx_ref_scan],
    color="tab:blue",
    linewidth=2,
    label=f"LEET_DIF#{idx_ref_scan+1}",
    zorder=0
)
# 右軸ラベル
ax_summary_r0.set_ylabel("LEET diff. (μA/eV)", color="tab:blue")
ax_summary_r1.set_ylabel("LEET diff. (μA/eV)", color="tab:blue")
# 右軸の色
ax_summary_r0.tick_params(axis="y", colors="tab:blue")
ax_summary_r1.tick_params(axis="y", colors="tab:blue")

ax_summary[0].legend(loc="lower right")
ax_summary[1].legend(loc="lower right")
plt.tight_layout()
plt.show()

