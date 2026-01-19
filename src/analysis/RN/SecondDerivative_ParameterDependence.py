import numpy as np
import pandas as pd
import scipy
import scipy.signal as signal
import matplotlib.pyplot as plt
from pathlib import Path
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog

from pathlib import Path
import customtkinter as ctk


##########################################################################################################################################
# input parameters ########################################################################################################################
##########################################################################################################################################

# 入力するファイルのパスを指定 #################
# ""の中にファイルの絶対pathをコピペする 
# ex) filepath = Path("/Users/name/Documents/...(略).../解析するcsvfile.csv")
# filepath = "Pupup window"
# filepath = Path("ここにコピペ")
filepath = Path("/Users/ryotaro/Documents/実験データ/20241217_organic_conductors/A1rawdata/beta7_9/STPy_6_5_5_PESImage/Example_SecondDerivative.csv")

# SGパラメータ #############################
sg_iteration = 4 # SGの繰り返し数
sg_poly = 2 # 次数
order = 2 # ピーク検出の感度

sg_point_min=sg_poly+1 # SGスムージングの最小の点数 (このまま使う)
sg_point_max=141 # SGスムージングの最大の点数

# RMSE計算範囲 #############################
# autoの場合、importしたXの最小値、最大値を使用
x_rms_min_eV = "Auto" # RMSE計算のxの下限
x_rms_max_eV = "Auto" # RMSE計算のxの上限
# 手動の場合はこちらをコメントアウトして使用
# x_rms_min_eV = 0 
# x_rms_max_eV = 1.2

# peak plotの表示範囲 (エネルギー) ###########
x_min_show = "Auto" # Peak plotのxの最小値
x_max_show = "Auto" # Peak plotのxの最大値
# 手動の場合はこちらをコメントアウトして使用
# x_min_show = 0 
# x_max_show = 1.2

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

def load_data(file_pass, x_leg, y_leg): 
    # ---------
    # 入力 すべて" *" にすること
    # filepass: ファイルのパス(.csvのみ) 
    # x_leg: xの読み込みの凡例。
    # y_leg: yの読み込みの凡例。
    # 出力
    #読み込んだx_legとy_legをx, yとして出力する。
    # ---------
    df = pd.read_csv(file_pass,encoding="utf-8") #..\\戻る　　\\ディレクトリの結合(進む)
    #print(df)
    x = df[x_leg].values
    y = df[y_leg].values
    #nanを全て消す
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    return x, y

def idx_of_the_nearest(data, value):
    idx = np.argmin(np.abs(np.array(data) - value))
    return idx
    
def sg_fil(C, window_size, polynomial_order, repeat_sg):
    Csg=np.copy(C)
    
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.sig_nal.savgol_filter.html#scipy.signal.savgol_filter
    for i in range(repeat_sg):
        Csg = scipy.signal.savgol_filter(Csg, window_size, polynomial_order, mode='nearest')
    return Csg

def get_rmse(y, y0):
    return np.sqrt(1/len(y)*np.sum((y-y0)**2))

def Rearrange_lsts(x, y):
    X = []  # 結果を格納するための入れ子リスト
    Y = []  # 対応するYの値を格納するためのリスト

    judge_x = 0
    current_x = []  # 現在のxの値を初期化
    current_y = []  # 現在のxに対応するyの値を格納するためのリストを初期化

    for j in range(len(x)):
        if x[j] == judge_x:
            current_x.append(x[j])
            current_y.append(y[j])  # 同じxに属するyの値を格納

        else:
            X.append(current_x)  # 現在のxに対応するyの値をXに追加
            Y.append(current_y)  # 現在のxの値をYに追加

            current_x = [x[j]]
            current_y = [y[j]]

            judge_x = x[j]  # 新しいxの値を設定         

    # ループ終了後、最後のxに対応するyの値を追加
    X.append(current_x)
    Y.append(current_y)

    # XとYに整理されたデータが格納されています
#     print(X)
#     print(Y)

    return X, Y

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

if ".csv" in input_file: #自作csvファイルの時。spline補完する
    # スペクトルデータの読み込み
    x_input, y_input = load_data(path, 
                             "x", "y")
    step= np.round(abs(x_input[0]-x_input[1]),5)
    
    print("step幅      :",step,"eV")
    x_input = np.round(x_input,5)

    # 入力データプロット
    plt.figure(figsize=(4, 3))
    plt.plot(x_input, y_input,label="Imported spectrum", color='black')
    plt.title(input_file)
    plt.legend()
    plt.xlabel('Energy (eV)')
    plt.ylabel('Intensity (arb. units)')
    plt.show(block=False)
    plt.pause(0.001)
else:
    print("csv fileの読み込みに失敗しました。パスを変数filepathに文字列としてコピペしてください。csv fileの1行目はラベルです。2列に分けて、それぞれxとyとしてください。2行目以降にx, yの数値データを縦に並べてください。")

# xを小さい順に並び替え、対応するyも同じ順序で並び替える
sort_indices = np.argsort(x_input)
x_input = x_input[sort_indices]
y_input = y_input[sort_indices]

# plotするかどうか
plot_sg_spectra=True 

print("SG order    :", sg_poly)
print("SG repeat   :", sg_iteration)
print("SG point min:", sg_point_min)
print("SG point max:", sg_point_max)

# peak dependence plot範囲設定
if x_rms_min_eV == "Auto":
    x_rms_min_eV = np.amin(x_input)
if x_rms_max_eV == "Auto":
    x_rms_max_eV = np.amax(x_input)

print("RMSE範囲    :", x_rms_min_eV, "to", x_rms_max_eV)

# SGスムージング実施
ysg_lst, rms_sg, sg_point_lst =  Make_savitzky_goley_lst(x_input, # x
                                                        y_input, # y
                                                        sg_point_min, # SG pointsのmin
                                                        sg_point_max, # SG pointsのmax
                                                        sg_poly,      # SG 次数
                                                        sg_iteration, # SG iteration number
                                                        x_rms_min_eV, # 残差を計算するときのxの下限
                                                        x_rms_max_eV) # 残差を計算するときのxの上限

# SGスペクトルの二次微分とピーク検出
ddysg_lst, point_ddysg_peak_lst, x_ddysg_peak_lst, ysg_ddysg_peak_lst, ddysg_peak_lst = Detect_peak_of_SGspectrum_by_SecondDerevetive(x_input, ysg_lst, sg_point_lst, order)


# plotting ###############################
legendsize=6
labelsize=10

facecolors_peak="white"
edgecolors_peak="tab:blue"
linewidth_peak=2
s_peak= 40

linewidth_raw=2

linewidth_smooth=2

# peak dependence plot範囲設定
if x_min_show == "Auto":
    x_min_show = np.amin(x_input)
if x_max_show == "Auto":
    x_max_show = np.amax(x_input) 


# スムージングの詳細プロット
for j in range(len(sg_point_lst)):

    fig_sg, (ax_ysg, ax_ddysg) = plt.subplots(
                                                1, 2, # 1行 2列
                                                figsize=(7, 3), # 図全体のサイズ
                                                constrained_layout=True # レイアウトの自動調整
                                            )
    
    # 二次微分スペクトル
    # peak
    ax_ddysg.scatter(x_ddysg_peak_lst[j], ddysg_peak_lst[j], 
                     label="Peaks",
                    facecolors=facecolors_peak,
                    edgecolors=edgecolors_peak,
                    linewidths=linewidth_peak,
                    s=s_peak)  
    
    # ddysg
    ax_ddysg.plot(x_input, ddysg_lst[j],
                  color="tab:blue", 
                  label="2nd Derivative\n"+str(sg_point_lst[j])+" points",
                  linewidth=2, 
                  zorder=0)
    
    # スムージングスぺクトル
    # raw data
    ax_ysg.plot(x_input, y_input,
                label="Imported spectrum", 
                color="black", zorder=0, linewidth=linewidth_raw)
    
    # smoothing
    ax_ysg.plot(x_input, ysg_lst[j],
                label="Smoothed spectrum\n" + str(sg_point_lst[j]) + " points", 
                linewidth=linewidth_smooth,
                color="tab:blue", zorder=0)
    
    # peak
    ax_ysg.scatter(x_ddysg_peak_lst[j], ysg_ddysg_peak_lst[j],
                   label="2nd Derivative Peak",
                    facecolors=facecolors_peak,
                    edgecolors=edgecolors_peak,
                    linewidths=linewidth_peak,
                    s=s_peak)
    
    # detail
    ax_ysg.set_xlabel("Energy (eV)", fontsize=labelsize)
    ax_ysg.set_ylabel("Intensity (arb. units)", fontsize=labelsize)
    ax_ysg.legend(fontsize=legendsize)
    
    # タイトルを設定し、改行位置を指定
    ax_ysg_title= f"Peak energies: {x_ddysg_peak_lst[j]}"
    max_line_length = 70  # 70文字ごとに改行
    wrapped_title = "\n".join([ax_ysg_title[i:i+max_line_length] for i in range(0, len(ax_ysg_title), max_line_length)])
    ax_ysg.set_title(wrapped_title, fontsize=labelsize)
    
    ax_ysg.tick_params(axis='both', which='both', labelsize=labelsize)  # labelsizeを適宜変更
    
    ax_ddysg.set_xlabel("Energy (eV)", fontsize=labelsize)
    ax_ddysg.set_ylabel("Intensity (arb. units)", fontsize=labelsize)
    # ax_ddysg.legend(fontsize=legendsize)
    ax_ddysg.set_title("Second derivative", fontsize=labelsize)
    ax_ddysg.tick_params(axis='both', which='both', labelsize=labelsize)  # labelsizeを適宜変更


# まとめプロット ###############################
fig1 = plt.figure(figsize=(4, 3))
ax1 = fig1.add_subplot(1, 1, 1) #Δpeak posi
fig2 = plt.figure(figsize=(4, 3))
ax2 = fig2.add_subplot(1, 1, 1) #ΔRMS smoothing

# ピーク
for j in range(len(point_ddysg_peak_lst)):
    ax1.scatter(point_ddysg_peak_lst[j], x_ddysg_peak_lst[j], 
                facecolors=facecolors_peak,
                edgecolors=edgecolors_peak,
                linewidths=linewidth_peak/2,
                s=s_peak/3)

# RMSE
ax2.scatter(sg_point_lst, rms_sg, edgecolors="tab:orange", facecolors="white", s=s_peak/2)

# まとめ RMSE と ピーク位置
ax1.set_ylabel("Energy (eV)", fontsize=labelsize)
ax1.set_xlabel("Point Number", fontsize=labelsize)
ax1.set_ylim(x_min_show, x_max_show)
ax1.set_title("Second derivetive peaks", fontsize=labelsize)
ax1.tick_params(axis='both', which='both', labelsize=labelsize)  # labelsizeを適宜変更
fig1.tight_layout()

#ax2.legend()
ax2.set_ylabel("RMSE", fontsize=labelsize)
ax2.set_xlabel("Point Number", fontsize=labelsize)
ax2.set_title("RMSE between the imported and smoothed spectra", fontsize=labelsize)
ax2.tick_params(axis='both', which='both', labelsize=labelsize)  # labelsizeを適宜変更
fig2.tight_layout()

plt.show()