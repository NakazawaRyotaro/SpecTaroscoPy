import numpy as np
import math
import matplotlib.pyplot as plt
import mpmath as mp
import pandas as pd
import tkinter
from tkinter import filedialog
import csv
from tkinter import messagebox
from scipy.optimize import curve_fit
import os
from math import log10, floor
from decimal import Decimal, ROUND_HALF_UP
import scipy.signal
import copy
from math import comb
import re
from scipy.special import comb


def append_to_elements(input_string, append_str):
    # タブで分割
    elements = input_string.split('\t')
    # 各要素に文字列を追加
    updated_elements = [element + append_str for element in elements]
    # タブ区切りで再結合
    return '\t'.join(updated_elements)

def check_numeric_in_tab_separated_string(input_string):
    # タブで分割
    elements = input_string.split('\t')
    # 各要素が数字かどうかをチェック
    for element in elements:
        if not element.isdigit():  # 数字以外の文字が含まれる場合
            return True
    return False

def get_idx_of_the_nearest(data, value, bind_value=None):
    data = np.array(data)   
    
    # bind_valueが指定されている場合、その値を無効化（非常に大きな値に置き換える）
    if bind_value is not None:
        mask = data == bind_value
        data[mask] = np.inf  # 非常に大きな値に置き換える
    
    idx = np.argmin(np.abs(data - value))
    # print(idx)
    return idx

def write_name(file_path, key, value):
    try:
        lines = []
        found_key = False

        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                if not found_key:
                    parts = line.rstrip('\n').split('\t', 1)
                    if parts and parts[0] == key:
                        new_line = f"{key}\t{value}\n"
                        lines.append(new_line)
                        found_key = True
                    else:
                        lines.append(line)
                else:
                    lines.append(line)

        if not found_key:
            # keyが見つからなかった場合、末尾に追加
            lines.append(f"{key}\t{value}\n")

        with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
            file.writelines(lines)

        print("saved")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")


# setting_defaultから読みこむdef文
def open_file_and_get_words_next_to_search_term(file_path, search_words, mark='\t', words_for_failure="", type="float"):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            return get_words_next_to_search_term(file, search_words, mark=mark, words_for_failure=words_for_failure, type=type)
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
        return words_for_failure, False


# setting_defaultから読みこむdef文
def open_file_and_get_list_next_to_tab(file_path, search_words, mark='\t', inner_mark=' ', words_for_failure="", type="float"):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            return get_list_next_to_search_term(file, search_words, mark=mark, inner_mark=inner_mark, words_for_failure=words_for_failure, type=type)
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
        return words_for_failure, False


def get_words_next_to_search_term(file, search_words, mark="\t", words_for_failure="", type="float"):
    # mark: defaultは\t (タブ)
    has_words = True
    for line in file:
        words_temp = line.split(mark)
        if search_words == words_temp[0]:  # 完全一致を確認
            words = line.split(mark)[-1].strip()  # タブ文字で分割して、最後の要素を取得
            # print(words)
            if words != "":
                if type == "float":
                    return float(words), has_words
                elif type == "str":
                    return str(words), has_words
            else:
                return words_for_failure, has_words  # 空文字の時はwords_for_failureを返す
    has_words = False
    return words_for_failure, has_words  # ファイル内でxxが見つからない場合

def get_list_next_to_search_term(file, search_words, mark="\t", inner_mark=" ", words_for_failure=[], type="float"):
    """
    ファイルから指定された search_words を探し、その後のデータを特定の形式で返す。

    Args:
        file (iterable): 読み取るファイルまたは文字列のリスト。
        search_words (str): 検索する単語。
        mark (str): search_words とデータを区切る文字。デフォルトはタブ。
        inner_mark (str): データ部分の内部の区切り文字。デフォルトはスペース。
        words_for_failure (any): データが見つからない場合や不正な形式の場合に返す値。
        type (str): "float" か "str" を指定。データの型を決定。

    Returns:
        tuple: (データのリスト, has_words)
            データ部分が成功すれば型変換後のリスト、失敗すれば words_for_failure。
            has_words は成功なら True、失敗なら False。
    """
    has_words = True
    for line in file:
        words_temp = line.split(mark)
        if search_words == words_temp[0]:  # 完全一致を確認
            try:
                # 内部区切り文字で分割してリスト化
                words_list = words_temp[1].strip().split(inner_mark)
                if type == "float":
                    # すべての要素を float に変換
                    words_list = [float(w) for w in words_list]
                elif type == "str":
                    # 要素をそのまま文字列として返す
                    words_list = [str(w) for w in words_list]
                return words_list, has_words
            except ValueError:
                # 型変換エラーの場合
                return words_for_failure, has_words
    has_words = False
    return words_for_failure, has_words  # ファイル内で search_words が見つからない場合

def get_path(idir=''):
    path_lst=[]
    filename_lst=[]
    get_paths = tkinter.filedialog.askopenfilename(initialdir = idir, multiple=True) #選択する
    
    for i in get_paths:
        filename = i.split("/")[-1] #取得した絶対パスからファイル名を得る
        # print("load path:",i)
        # print("load filename:",filename)
        path_lst.append(i)
        filename_lst.append(filename)
    # print(path_lst)
    return path_lst, filename_lst

# csvファイルを開いてlabelをリストに格納する。
def read_labels_from_csv(path_to_csv):
    labels = []  # ラベルを格納するリストを初期化します
    with open(path_to_csv, 'r', newline='', encoding='utf-8', errors='replace') as csvfile:
        csv_reader = csv.reader(csvfile)
        # CSVファイルの最初の行を読み込んで、それをラベルとしてリストに追加します
        labels = next(csv_reader)
    return labels

def get_2Ddata_from_csv(path, x_leg, y_leg, plot_spectrum=False): 
    """
    Import experimental 2D data.
    いまとなっては非推奨。

    Args:
    file_pass (str): 入力ファイルの絶対pass
    x_leg (str): x dataの凡例
    y_leg (str): y dataの凡例
    
    Returns:
    x (ndarray): x data
    y (ndarray): y data
    """

    # 入力ファイルの取得
    df = pd.read_csv(path, encoding="utf-8")
    x = df[x_leg].values # x取得
    y = df[y_leg].values # y取得
    #nanを全て消す
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]

    # xが小さい順にソートします
    sorted_indices = np.argsort(x)
    sorted_x = x[sorted_indices]
    sorted_y = y[sorted_indices]

    # plotting
    if plot_spectrum:
        fig, axs = plt.subplots(2, 1, figsize=(4, 9))
        axs[0].scatter(sorted_x, sorted_y, label="Imported spectrum", color="tab:gray", s=10)
        axs[0].legend()
        axs[1].scatter(sorted_x, sorted_y, label="Imported spectrum", color="tab:gray", s=10)
        axs[1].set_yscale("log")
        axs[1].legend()
        plt.show()
        # print("plot終了")
    return sorted_x, sorted_y

def get_2Ddata_from_text_file_auto(path, x_leg, y_leg, plot_spectrum=False):
    """
    こっちが推奨。
    """
    with open(path, encoding="utf-8", errors='replace') as f:
        lines = f.readlines()

    # nanやinfを許容する数値行判定
    def is_numeric_line(line):
        parts = re.split(r'[\t,]', line.strip())
        try:
            [float(val.strip()) for val in parts if val.strip()]
            return True
        except ValueError:
            return False

    # 数値が続くヘッダーを探す（連続2行で確認）
    for i in range(len(lines) - 2):
        if not is_numeric_line(lines[i]) and is_numeric_line(lines[i + 1]) and is_numeric_line(lines[i + 2]):
            header_line = lines[i].strip()
            data_lines = []
            for j in range(i + 1, len(lines)):
                if is_numeric_line(lines[j]):
                    data_lines.append(lines[j])
                else:
                    break
            break
    else:
        raise ValueError("データ行の検出に失敗しました。")

    # 区切り文字推定
    if '\t' in header_line:
        delimiter = '\t'
    elif ',' in header_line:
        delimiter = ','
    # else:
    #     delimiter = r'\s+'

    # ラベル読み込み（空白を除去）
    label_list = [label.strip() for label in re.split(delimiter, header_line)]
    
    # データ読み込み
    data = np.genfromtxt(data_lines, delimiter=delimiter)
    if data.ndim == 1:
        data = data.reshape(-1, len(label_list))
    # nan を 0 に置換
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    # print(data)
    df = pd.DataFrame(data, columns=label_list)

    # ラベル存在チェック
    if x_leg not in df.columns or y_leg not in df.columns:
        raise KeyError(f"'{x_leg}' または '{y_leg}' がラベルに存在しません。\n存在するラベル: {df.columns.tolist()}")

    # x, y抽出
    x = df[x_leg]
    y = df[y_leg]

    # ソート
    sorted_idx = np.argsort(x)
    sorted_x = x.iloc[sorted_idx].to_numpy()
    sorted_y = y.iloc[sorted_idx].to_numpy()

    # プロット
    if plot_spectrum:
        fig, axs = plt.subplots(2, 1, figsize=(4, 9))
        axs[0].scatter(sorted_x, sorted_y, label="Spectrum", color="tab:gray", s=10)
        axs[0].legend()
        axs[1].scatter(sorted_x, sorted_y, label="Spectrum (log)", color="tab:gray", s=10)
        axs[1].set_yscale("log")
        axs[1].legend()
        plt.tight_layout()
        plt.show()

    return sorted_x, sorted_y

def make_gaussian(x, x0, fwhm, peak_intensity=1, bg=0): 
    """
    gaussianを作ります。ピーク強度はデフォルトでは1です。このとき面積が1になります。
    Args:
        x (ndarray): x asis. エネルギー
        x0 (float): gaussianのピークエネルギー
        fwhm (float): gaussianの半値全幅
        peak_intensity (float): gaussianのピーク強度。デフォルトは1です。
    #xデータ、中心、FWHM, ピーク強度
    """
    if peak_intensity==1:
        return peak_intensity/((fwhm/2.354820)*np.sqrt(2*math.pi)) * np.exp(-(x-x0)**2 /(2*((fwhm/2.354820)**2))) + bg
    else:
        return peak_intensity * np.exp(-(x-x0)**2 /(2*((fwhm/2.354820)**2))) + bg
    
def make_two_gaussian(x, x1, fwhm1, y_peak1, x2, fwhm2, y_peak2, bg=0):
    g1 = make_gaussian(x, x1, fwhm1, y_peak1)
    g2 = make_gaussian(x, x2, fwhm2, y_peak2)
    return g1+g2+bg

def make_three_gaussian(x, x1, fwhm1, y_peak1, x2, fwhm2, y_peak2, x3, fwhm3, y_peak3, bg=0):
    g1 = make_gaussian(x, x1, fwhm1, y_peak1)
    g2 = make_gaussian(x, x2, fwhm2, y_peak2)
    g3 = make_gaussian(x, x3, fwhm3, y_peak3)
    return g1+g2+g3+bg

def make_exponential_tail_states(x, A, x0, xt, bg=0):
    return A*np.exp((x - x0)/xt) + bg

def make_Menzel2021_fitting_function(x, x_vbm_polylog, inverse_slope_of_tail_states_polylog, a0_polylog, bg=0, A=-1):
    """
    Calculate the fitting function of equation (3) in Dorothee et al., ACS Appl. Mater. Interfaces 2021, 13, 43540−43553 (2022)
    
    Args:
        x (ndarray): x axis。エネルギー
        x_vbm_polylog (float): VBMエネルギー
        inverse_slope_of_tail_states_polylog (float): テール準位の傾きの逆数
        a0_polylog (float): y強度の定数項
        bg (float): background強度 (定数)
        A (float): 指数関数の乗数の時の強度。 **default** A=-1

    Returns:
        y_fdi (ndarray): Menzel 2021のfitting関数
    """
    y_fdi=np.zeros(len(x))
    z = make_exponential_tail_states(x, A, x_vbm_polylog, inverse_slope_of_tail_states_polylog)
    # 多重対数関数Li_3/2の生成
    for i in range(len(x)):
        y_fdi[i]= -a0_polylog/2*np.sqrt(inverse_slope_of_tail_states_polylog*math.pi)*mp.re(mp.polylog(0.5, z[i])) # mp.reでreal partを取得できるらしい
    # y_fdi*= a0_polylog
    return y_fdi+bg

def make_lincom_of_polylog_and_gauss(x, x_vbm_polylog, inverse_slope_of_tail_states_polylog, a0_polylog, 
                                     x_center_gauss, x_fwhm_gauss, peak_int_gauss, bg=0, A=-1):
    """
    Calculate the fitting function of linearcombination of Gaussians and polylogarithm [equation (3) in Dorothee et al., ACS Appl. Mater. Interfaces 2021, 13, 43540−43553 (2022)].
    
    Args:
        x (ndarray): x axis。エネルギー
        
        x_vbm_polylog (float): VBMエネルギー
        inverse_slope_of_tail_states_polylog (float): テール準位の傾きの逆数
        a0_polylog (float): y強度の定数項
        A (float): 指数関数の乗数の時の強度。 **default** A=-1

        x_center_of_gauss (float): Gaussianの中心のエネルギー
        x_fwhm_gauss (float): Gaussianの半値全幅
        peak_int_of_gauss (float): Gaussianのピーク強度
        
        bg (float): background
    Returns:
        y_fdi (ndarray): Menzel 2021のfitting関数
    """

    y_fdi=np.zeros(len(x))
    z = make_exponential_tail_states(x, A, x_vbm_polylog, inverse_slope_of_tail_states_polylog)
    # 多重対数関数Li_3/2の生成
    for i in range(len(x)):
        y_fdi[i]= -a0_polylog/2*np.sqrt(inverse_slope_of_tail_states_polylog*math.pi)*mp.re(mp.polylog(0.5, z[i])) # mp.reでreal partを取得できるらしい
    # y_fdi*= a0_polylog
    
    # gaussianの生成
    y_gauss = make_gaussian(x, x_center_gauss, x_fwhm_gauss, peak_int_gauss)

    # polylogとgaussianの線形結合を取る
    return y_fdi + y_gauss + bg

def make_lincom_of_polylog_and_three_gauss(x, x_vbm_polylog, inverse_slope_of_tail_states_polylog, a0_polylog, 
                                        x_center_gauss1, x_fwhm_gauss1, peak_int_gauss1, 
                                        x_center_gauss2, x_fwhm_gauss2, peak_int_gauss2, 
                                        x_center_gauss3, x_fwhm_gauss3, peak_int_gauss3, 
                                        bg=0, A=-1):
    """
    Calculate the fitting function of linearcombination of Gaussians and polylogarithm [equation (3) in Dorothee et al., ACS Appl. Mater. Interfaces 2021, 13, 43540−43553 (2022)].
    
    Args:
        x (ndarray): x axis。エネルギー
        
        x_vbm_polylog (float): VBMエネルギー
        inverse_slope_of_tail_states_polylog (float): テール準位の傾きの逆数
        a0_polylog (float): y強度の定数項
        A (float): 指数関数の乗数の時の強度。 **default** A=-1

        x_center_of_gauss (float): Gaussianの中心のエネルギー
        x_fwhm_gauss (float): Gaussianの半値全幅
        peak_int_of_gauss (float): Gaussianのピーク強度
        
        bg (float): background
    Returns:
        y_fdi (ndarray): Menzel 2021のfitting関数
    """

    y_fdi=np.zeros(len(x))
    z = make_exponential_tail_states(x, A, x_vbm_polylog, inverse_slope_of_tail_states_polylog)
    # 多重対数関数Li_3/2の生成
    for i in range(len(x)):
        y_fdi[i]= -a0_polylog/2*np.sqrt(inverse_slope_of_tail_states_polylog*math.pi)*mp.re(mp.polylog(0.5, z[i])) # mp.reでreal partを取得できるらしい
    # y_fdi*= a0_polylog
    
    # gaussianの生成
    y_gauss1 = make_gaussian(x, x_center_gauss1, x_fwhm_gauss1, peak_int_gauss1)
    y_gauss2 = make_gaussian(x, x_center_gauss2, x_fwhm_gauss2, peak_int_gauss2)
    y_gauss3 = make_gaussian(x, x_center_gauss3, x_fwhm_gauss3, peak_int_gauss3)
    # polylogとgaussianの線形結合を取る
    return y_fdi + y_gauss1 + y_gauss2 + y_gauss3 + bg

# def make_fermi_edge_function(x, T, E_F, fwhm, a_0, bg=0, k_B=8.617333262e-5):
#     """ 
#     fermi edgeのPESスペクトルをシミュレーション
#     convolutionするときに端の強度が低くなるのを抑えるため、
#     一度範囲(配列の長さ)を拡張してフェルミディラック分布・装置関数を生成、PESスペクトルを作成する。
#     そのあとシミュレーションPESスペクトルの配列の長さを元に戻して出力する。
#     """
#     print(x)
#     x_min = np.around(x[0],6)
#     x_max = np.around(x[-1],6)
    
#     step = np.around((x[1]-x[0]), 6)
#     additional_idx = int(1/step)
#     start = np.around(x_min - additional_idx*step, 6)
#     end = np.around(x_max + additional_idx*step, 6)
#     x_ = np.round(np.arange(start, end+step/10, step), 6)
#     dif_len_x = len(x)-len(x_)
#     # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
#     if dif_len_x % 2 != 1:
#         x_ = np.append(x_, x_[-1] + np.around(x_, 6))

#     FD =  a_0 / ( 1 + np.exp((x_-E_F)/(k_B*T)) )
#     x_s = np.round(np.arange(-(len(x_)-1)*step/2, (len(x_)-1)*step/2 + step/10, step), 6)
#     s = make_gaussian(x_s, 0, fwhm)
#     y_ = np.convolve(s, FD, mode="same") * step
#     # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
#     y = y_[get_idx_of_the_nearest(x_, x_min) : get_idx_of_the_nearest(x_, x_max)+1] + bg
#     # print(len(y))
#     # print(len(x))
#     # plt.plot(x_, FD)
#     # plt.plot(x, s)
#     # plt.plot(x_, y_)
#     # plt.plot(x, y)
#     # plt.show()
#     # print(x_)
#     return y

def make_fermi_edge_metal_conv_gaussian(x, T, E_F, fwhm, a=0, b=1, bg=0, k_B=8.617333262e-5):
    """ 
    fermi edgeのPESスペクトルをシミュレーション
    convolutionするときに端の強度が低くなるのを抑えるため、
    一度範囲(配列の長さ)を拡張してフェルミディラック分布・装置関数を生成、PESスペクトルを作成する。
    そのあとシミュレーションPESスペクトルの配列の長さを元に戻して出力する。
    """
    # print(x)
    x_min = np.around(x[0],6)
    x_max = np.around(x[-1],6)

    step = abs(np.around((x[1]-x[0]), 6))
    additional_idx = int(1/step)
    start = np.around(x_min - additional_idx*step, 6)
    end = np.around(x_max + additional_idx*step, 6)
    x_ = np.round(np.arange(start, end+step/10, step), 6)
    dif_len_x = len(x)-len(x_)
    # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
    if dif_len_x % 2 != 1:
        x_ = np.append(x_, x_[-1] + np.around(x_, 6))

    FD =  (a * x_ + b) / ( 1 + np.exp((x_-E_F)/(k_B*T)) )
    x_s = np.round(np.arange(-(len(x_)-1)*step/2, (len(x_)-1)*step/2 + step/10, step), 6)
    s = make_gaussian(x_s, 0, fwhm)
    y_ = np.convolve(s, FD, mode="same") * step
    # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
    y = y_[get_idx_of_the_nearest(x_, x_min) : get_idx_of_the_nearest(x_, x_max)+1] + bg
    # print(len(y))
    # print(len(x))
    # plt.plot(x_, FD)
    # plt.plot(x, s)
    # plt.plot(x_, y_)
    # plt.plot(x, y)
    # plt.show()
    # print(x_)
    return y

def make_lorentzian(x, x0, fwhm, peak_intensity=1, bg=0):
    """
    lorentzianを作ります。ピーク強度はデフォルトでは1です。このとき面積が1になります。
    Args:
        x (ndarray): x asis. エネルギー
        x0 (float): lorentzianのピークエネルギー
        fwhm (float): lorentzianの半値全幅
        peak_intensity (float): lorentzianのピーク強度。デフォルトは1です。
    #xデータ、中心、FWHM, ピーク強度
    """
    return peak_intensity/math.pi*(fwhm/2) / ((x - x0)**2 + (fwhm/2)**2) + bg


def make_fermi_edge_degenerate_semicon_conv_gauss(x, 
                                                  at, Ev, Et, # exponential tail states
                                                  Ec, ac, # CB DOS
                                                #   x0_lorentz, gamma_lorentz, # lorentzian
                                                  fwhm_instrum, # gaussian
                                                  T, x_EF, a_FDD=0, b_FDD=1, # FDD 
                                                  bg=0, # background
                                                  intensity_lorentz=1, k_B=8.617333262e-5):
    ## convolution計算で端を落とさないための拡張
    x_min = np.around(x[0],6)
    x_max = np.around(x[-1],6)

    step = abs(np.around((x[1]-x[0]), 6))
    additional_idx = int(1/step)
    start = np.around(x_min - additional_idx*step, 6)
    end = np.around(x_max + additional_idx*step, 6)
    x_ = np.round(np.arange(start, end+step/10, step), 6)
    dif_len_x = len(x)-len(x_)
    # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
    if dif_len_x % 2 != 1:
        x_ = np.append(x_, x_[-1] + np.around(x_, 6))
    ## ここまで拡張

    # フェルミディラック分布
    y_FDD =  (a_FDD * x_ + b_FDD) / ( 1 + np.exp((x_-x_EF)/(k_B*T)) )
    # print('y_FDD:', y_FDD)

    # 装置関数用のgaussian作成
    x_gauss = np.round(np.arange(-(len(x_)-1)*step/2, (len(x_)-1)*step/2 + step/10, step), 6) # 装置関数用のx軸
    y_gauss = make_gaussian(x_gauss, 0, fwhm_instrum, peak_intensity=1, bg=0)
    # print('y_gauss:', y_gauss)

    # DOS作成 
    y_CB = np.zeros(len(x_)) # 初期化
    y_gap = np.zeros(len(x_)) # 初期化
    # DOS作成
    y_CB = ac * np.sqrt(np.clip(-(x_ - Ec), 0, None)) 
    y_gap = at * np.exp((x_ - Ev)/Et)
    y_DOS = y_CB + y_gap # 和を取る
    # print('y_CB_DOS:', y_DOS)

    # y = conv(y, y_lorenz, step=step)
    y_electron = y_DOS * y_FDD

    # 装置関数でconvolution
    y_PES = conv(y_electron, y_gauss, step=step)
    y_PES += bg # backgroundを足す
    # print('y:', y)
    return y_PES[get_idx_of_the_nearest(x_, x_min) : get_idx_of_the_nearest(x_, x_max)+1] # 元の長さに戻す


def make_fermi_edge_degenerate_semicon_conv_two_gauss(x, 
                                                  at, Ev, Et, # exponential tail states
                                                  Ec, ac, # CB DOS
                                                  fwhm_lifetime, # gaussian lifetime
                                                  fwhm_instrum, # gaussian instrumental function
                                                  T, x_EF, a_FDD=0, b_FDD=1, # FDD 
                                                  bg=0, # background
                                                  intensity_lorentz=1, k_B=8.617333262e-5):
    
    ## convolution計算で端を落とさないための拡張
    x_min = np.around(x[0],6)
    x_max = np.around(x[-1],6)

    step = abs(np.around((x[1]-x[0]), 6))
    additional_idx = int(1/step)
    start = np.around(x_min - additional_idx*step, 6)
    end = np.around(x_max + additional_idx*step, 6)
    x_ = np.round(np.arange(start, end+step/10, step), 6)
    dif_len_x = len(x)-len(x_)
    # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
    if dif_len_x % 2 != 1:
        x_ = np.append(x_, x_[-1] + np.around(x_, 6))
    ## ここまで拡張

    # フェルミディラック分布
    y_FDD =  (a_FDD * x_ + b_FDD) / ( 1 + np.exp((x_-x_EF)/(k_B*T)) )
    # print('y_FDD:', y_FDD)

    # 装置関数用のgaussian作成
    x_gauss = np.round(np.arange(-(len(x_)-1)*step/2, (len(x_)-1)*step/2 + step/10, step), 6) # 装置関数用のx軸
    # y_lifetime = make_gaussian(x_gauss, 0, fwhm_lifetime, peak_intensity=1, bg=0)
    y_lifetime = make_lorentzian(x_gauss, 0, fwhm_lifetime, peak_intensity=1, bg=0)
    y_instrum = make_gaussian(x_gauss, 0, fwhm_instrum, peak_intensity=1, bg=0)
    # print('y_gauss:', y_gauss)

    # DOS作成 
    y_CB = np.zeros(len(x_)) # 初期化
    y_gap = np.zeros(len(x_)) # 初期化
    # DOS作成
    # y_CB = ac * np.sqrt(np.clip(-(x_ - Ec), 0, None)) # parabolic band
    y_CB = ac * np.sqrt(np.clip(-(x_ - Ec)*(1+0.2*(x_-Ec)), 0, None))*(1 + 2*0.2*(x_-Ec)) # InNの非放物線バンドに対応
    y_gap = at * np.exp((x_ - Ev)/Et)
    y_DOS = y_CB + y_gap # 和を取る
    y_DOS = conv(y_DOS, y_lifetime, step=step) # 電子のライフタイムぼかし
    # print('y_CB_DOS:', y_DOS)

    y_electron = y_DOS * y_FDD

    # 装置関数でconvolution
    y_PES = conv(y_electron, y_instrum, step=step)
    y_PES += bg # backgroundを足す
    # print('y:', y)
    return y_PES[get_idx_of_the_nearest(x_, x_min) : get_idx_of_the_nearest(x_, x_max)+1] # 元の長さに戻す


def make_fermi_edge_degenerate_semicon_conv_lorentz_gauss( x, 
                                        at, Ev, Et, # exponential tail states
                                        Ec, ac, # CB DOS
                                        fwhm_lifetime, # gaussian lifetime
                                        fwhm_instrum, # gaussian instrumental function
                                        T, x_EF, a_FDD=0, b_FDD=1, # FDD 
                                        bg=0, # background
                                        intensity_lorentz=1, k_B=8.617333262e-5):
    
    ## convolution計算で端を落とさないための拡張
    x_min = np.around(x[0],6)
    x_max = np.around(x[-1],6)

    step = abs(np.around((x[1]-x[0]), 6))
    additional_idx = int(1/step)
    start = np.around(x_min - additional_idx*step, 6)
    end = np.around(x_max + additional_idx*step, 6)
    x_ = np.round(np.arange(start, end+step/10, step), 6)
    dif_len_x = len(x)-len(x_)
    # x_の作成がうまくいかず、1要素ずれることがあるので調整する。
    if dif_len_x % 2 != 1:
        x_ = np.append(x_, x_[-1] + np.around(x_, 6))
    ## ここまで拡張

    # フェルミディラック分布
    y_FDD =  (a_FDD * x_ + b_FDD) / ( 1 + np.exp((x_-x_EF)/(k_B*T)) )
    # print('y_FDD:', y_FDD)

    # 装置関数用のgaussian作成
    x_gauss = np.round(np.arange(-(len(x_)-1)*step/2, (len(x_)-1)*step/2 + step/10, step), 6) # 装置関数用のx軸
    # y_lifetime = make_gaussian(x_gauss, 0, fwhm_lifetime, peak_intensity=1, bg=0)
    y_lifetime = make_lorentzian(x_gauss, 0, fwhm_lifetime, peak_intensity=1, bg=0) 
    y_instrum = make_gaussian(x_gauss, 0, fwhm_instrum, peak_intensity=1, bg=0)
    # print('y_gauss:', y_gauss)

    # DOS作成 
    y_CB = np.zeros(len(x_)) # 初期化
    y_gap = np.zeros(len(x_)) # 初期化
    # DOS作成
    y_CB = ac * np.sqrt(np.clip(-(x_ - Ec)*(1+0.2*(x_-Ec)), 0, None))*(1 + 2*0.2*(x_-Ec)) # InNの非放物線バンドに対応
    y_gap = at * np.exp((x_ - Ev)/Et)
    y_DOS = y_CB + y_gap # 和を取る
    y_DOS = conv(y_DOS, y_lifetime, step=step) # 電子のライフタイムぼかし
    # print('y_CB_DOS:', y_DOS)

    y_electron = y_DOS * y_FDD

    # 装置関数でconvolution
    y_PES = conv(y_electron, y_instrum, step=step)
    y_PES += bg # backgroundを足す
    # print('y:', y)
    return y_PES[get_idx_of_the_nearest(x_, x_min) : get_idx_of_the_nearest(x_, x_max)+1] # 元の長さに戻す


def fit_experimental_data(x_observed, y_observed, 
                          fitting_function, 
                          x_fit_min, x_fit_max, 
                          p0, 
                          bounds,
                          maxfev=1000):
    
    idx_x_fitting_min = get_idx_of_the_nearest(x_observed, x_fit_min)
    idx_x_fitting_max = get_idx_of_the_nearest(x_observed, x_fit_max)

    # fitting
    popt, pcov = curve_fit(fitting_function, 
                           x_observed[idx_x_fitting_min:idx_x_fitting_max], 
                           y_observed[idx_x_fitting_min:idx_x_fitting_max], 
                           p0=p0,
                           bounds=bounds,
                           maxfev=maxfev
                           )
    return popt, pcov

def create_folder_at_current_path(current_path, folder_name):
    parent_directory = os.path.dirname(current_path)  # 親ディレクトリのパスを取得
    new_folder_path = os.path.join(parent_directory, folder_name)  # 新しいフォルダのパスを作成
    try:
        os.mkdir(new_folder_path)
    except FileExistsError: #すでにフォルダがある場合に何もしない
        pass

# 有効数字をsigにしてざっくり表示
def decimalRound(num, sig=3):
    a=Decimal(str(num))
    dig="1E"+str((sig-int(floor(log10(abs(num))))-1)*-1)
    b = a.quantize(Decimal(dig), rounding=ROUND_HALF_UP)
    if "E" in str(b):#E~で表示されるのの回避
        return str(int(b))
    else:
        return str(b)

# convolution  
def conv(y1, y2, step, mode="same"):
    return np.convolve(y1, y2, mode=mode) * step

# jannson's method
def deconvolute_spectrum_by_jannson(o, s, i, step, a, b, r0): 
    # relaxation function
    def r(a, b, r0):
        return r0 * (1-2/(b-a)*abs(o-(a+b)/2))
    # deconvolution
    o=o+r(a, b, r0)*(i-conv(o, s, step)) #deconv処理oがj-1番目からj番目に更新される
    return o

#Gold's ratio method
def deconvolute_spectrum_by_gold(o, s, i, step):
    o=o*i/conv(s, o, step) #deconv処理oがj-1番目からj番目に更新される
    return o

# idx(iteration)で区切られた多次元配列にする
def rearrange_nd_lst_to_1d_lst(x, y):
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


def split_around_zero(x, n):
    if n % 2 == 0:
        raise ValueError("n must be an odd number.")
    
    # xをソートして、0を中心に分割するためのインデックスを取得
    sorted_indices = np.argsort(x)
    sorted_x = x[sorted_indices]
    zero_index = get_idx_of_the_nearest(sorted_x, 0)
    
    half_n = n // 2
    result = []

    # 中心を含む最初のグループ
    start_index = zero_index - half_n
    end_index = zero_index + half_n + 1
    
    if start_index >= 0 and end_index <= len(sorted_x):
        result.append(sorted_indices[start_index:end_index])
    
    # 以降の前後のグループを処理
    for direction in (-1, 1):
        current_start = start_index + direction * n
        current_end = end_index + direction * n
        
        while current_start >= 0 and current_end <= len(sorted_x):
            chunk_indices = sorted_indices[current_start:current_end]
            if len(chunk_indices) == n:
                result.append(chunk_indices)
            current_start += direction * n
            current_end += direction * n
    
    # 一番目の要素が小さい順にソート
    result_sorted = sorted(result, key=lambda indices: x[indices[0]])
    return result_sorted

# popupの返事
def ask_me(title, sentence):
    res = messagebox.askquestion(title, sentence)
    if res == 'yes':
        res = 'y'
    else:  
        res = None
    return res

def smooth_spectrum_by_SG(y, order, point, iteration):
    
    order=int(order)
    point=int(point)
    iteration=int(iteration)
    # 初期化
    # ある条件 (order, point, iteration) におけるスムージングスペクトルの作成
    y_sg=copy.deepcopy(y)
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.sig_nal.savgol_filter.html#scipy.signal.savgol_filter
    for i in range(iteration):
        y_sg = scipy.signal.savgol_filter(y_sg, point, order, mode='nearest') 
    return y_sg

def calculate_RMSE(y1, y2, x=None, x_rmse_min=None, x_rmse_max=None):
    """
    2つのyデータにおける平方根平均事情誤差 RMSE を計算する
    y1, y2: yデータふたつ。 1d ndarray
    x: xデータ一つ。xはなくても良い。1d ndarray。
    x_rmse_min, r_rmse_max: RMSEを計算する範囲。
    """

    if x is not None: # x, x_rmse_min, x_rmse_maxを定義している場合
        if x_rmse_min is None:
            x_rmse_min=min(x)

        if x_rmse_max is None:
            x_rmse_max=max(x)

        #差分を取る領域をindexに変換
        idx_x_rmse_min=get_idx_of_the_nearest(x, x_rmse_min) #indexに変換
        idx_x_rmse_max=get_idx_of_the_nearest(x, x_rmse_max) #indexに変換
        # インデックス範囲を正しい順序に修正
        if idx_x_rmse_min > idx_x_rmse_max:
            idx_x_rmse_min, idx_x_rmse_max = idx_x_rmse_max, idx_x_rmse_min
    else:
        if x_rmse_min is None:
            x_rmse_min=0
        if x_rmse_max is None:
            idx_x_rmse_max = -1

    # RMSE計算
    rmse=np.sqrt(np.average((y1[idx_x_rmse_min:idx_x_rmse_max] - y2[idx_x_rmse_min:idx_x_rmse_max])**2)/len(y1[idx_x_rmse_min:idx_x_rmse_max]))
    
    # (A) を返す。RMSEを計算している場合はそれも。
    return rmse

def calculate_RMSE_image(z1_lst, z2_lst, x=None, x_rmse_min=None, r_rmse_max=None, y=None, y_rmse_min=None, y_rmse_max=None):
    # まずz1_lst, z2_lstをy軸方向に切り出す
    # ...
    

    # y方向に切り出したz1_lst, z2_lstに対して、x軸方向に切り出し、imageのrmseを計算する
    rmse=0
    for i in range(len(z1_lst_y_切り取り)):
        rmse+=calculate_RMSE(z1_lst_y_きりとり[i], z2_lst_y_きりとり[i], x=None, x_rmse_min=None, x_rmse_max=None)
    return rmse


def binomial_function(order, step=1):
    """
    Generate normalized binomial weights for a given order.
    order: The order of Pascal's Triangle (must be an integer).
    step: The step size for integration (default is 1).
    """
    order = int(order)
    pascal_triangle = np.array([comb(order, k) for k in range(order + 1)])  # Generate binomial coefficients

    if step is not None:
        # Perform normalization using trapezoidal integration
        area = trapezoidal_integration(pascal_triangle, step)
        pascal_triangle = pascal_triangle / area  # Normalize to ensure sum = 1
    
    return pascal_triangle

def trapezoidal_integration(y, dx):
    """
    Perform trapezoidal integration over the given array y with step size dx.
    """
    integral = 0
    for i in range(len(y) - 1):
        integral += 0.5 * dx * (y[i] + y[i + 1])  # Calculate trapezoids and sum them up
    return integral
