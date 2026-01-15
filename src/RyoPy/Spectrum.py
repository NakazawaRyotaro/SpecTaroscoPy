import numpy as np
import matplotlib.pyplot as plt
import csv
import datetime
import copy
import scipy.signal
import tkinter.messagebox as messagebox

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
import RyoPy.defs_for_analysis as rpa
from scipy.optimize import curve_fit
from pathlib import Path

try:
    # 現在のスクリプトの祖父母ディレクトリ (srcフォルダ) を取得
    SRC_PATH = Path(__file__).resolve().parent.parent
    # ファイルパスを統一的に管理
    default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
    VERSION_NUMBER, hoge=rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "version", type="str")
except:
    pass

# """
def main(): # fitting解析のmain関数
    USER="NAKAZAWA"
    # print(USER)
    # instance化
    
    #"""
    # spectrum = Spectrum(USER, filename="ARLEIPS_cryPEN_RT_GX_GY_GM_sato_finaldata.csv") 
    # csvファイル読み込み
    # spectrum.open_csv_file(fixs_a_path=True, path=r"G:\マイドライブ\実験データ\spectrumanalyzer_testdata\deconv\ARLEIPS_cryPEN_RT_GX_GY_GM_sato_finaldata.csv")
    # spectrum.load_data_from_csv_file("EF_0deg_GY", "Y_0deg_GY", plot_spectrum=False)
    

    # csvファイル読み込み
    PATH=r"g:\マイドライブ\実験データ\spectrumanalyzer_testdata\fitting\Doro2021fitting\Cu2O_H17_CFSYS.csv"
    FILENAME="Cu2O_H17_CFSYS.csv"

    spectrum = Spectrum(USER)
    spectrum.open_csv_file(path=PATH, filename=FILENAME)
    spectrum.load_data_from_csv_file("EF_Cu2O111_CFSYS_1216.1", "rNhPm1_Cu2O111_CFSYS_1216.1", plot_spectrum=False)
    #"""

    """
    ############################################################
    # deconvolution 解析 #######################################
    ############################################################
    # background処理
    x_bg_min = 1
    x_bg_max = 2
    spectrum.subtract_background("None", x_bg_min, x_bg_max)

    # spread function
    spectrum.generate_spread_function_for_deconvolution(spectrum.x_bg, "Gaussian", 0.35)
    
    # smoothing
    spectrum.smooth_spectrum_with_auto_cross_colleration(spectrum.y_bg, spectrum.s)

    # deconvolution
    # RMSEを計算する範囲を指定
    # x_RMSE_min = 
    # x_RMSE_max = 
    # deconvolutionのアルゴリズム選択
    # deconvolution_method="Jansson's"
    deconvolution_method="Gold"
    # deconvolution_method="Van citter with positive constrained"
    # parameters
    # jannson法の場合
    a=0
    b=10
    r0=spectrum.i_ac*10
    iteration_number=10

    # deconvoluion 実行部
    spectrum.deconvolute_spectrum(spectrum.x_bg, spectrum.i_ac, spectrum.s_cc, 
                                   iteration_number, 
                                   np.amin(spectrum.x_bg), np.amax(spectrum.x_bg), 
                                   deconvolution_method, 
                                   a, b, r0)

    # data saveを同じファイルで行うため、pathなどをインスタンスspectrumと共通にする。
    deconvoluted_spectrum = Spectrum(USER, x=spectrum.x_deconv, y_lst=spectrum.o_deconv_lst,
                                         path=spectrum.path, 
                                         x_legend=spectrum.x_legend, y_legend=spectrum.y_legend,
                                         filename=spectrum.filename)
    # data save
    spectrum.save_results("deconvolution")


    # peak検出
    deconvoluted_spectrum.detect_peak_spectrum_lst(deconvoluted_spectrum.x, deconvoluted_spectrum.y_lst)
    # pltctrl_peak_plots_of_deconvoluted_spectra = PlotControl("The peak plot of deconvoluted spectra", figsize_h=9, figsize_v=4)
    # pltctrl_peak_plots_of_deconvoluted_spectra.plot_rainbow_peak_plot(deconvoluted_spectrum.idx_y_peak_lst, 
    #                                                                   deconvoluted_spectrum.x_y_peak_lst,
    #                                                                   z=deconvoluted_spectrum.y_peak_lst)
    
    # data save
    deconvoluted_spectrum.save_results("detecting_peaks", is_GUI=True)
    spectrum.save_results("deconvolution")
    deconvoluted_spectrum.save_results("peak_detection", is_GUI=True)
    """
    
    #"""
    ############################################################
    # fitting 解析 #############################################
    ############################################################
    # set fitting parameters
    # polylogarithm
    x_fitting_min = 0. # energy at the minimum in fitting range (eV)
    x_fitting_max = 0.65 # energy at maximum in fitting range (eV)
    
    fitting_func = "polylogarithm" # fitting function
    x_vbm_polylog = 0.8 # VBM energy (eV)
    inverse_slope_of_tail_states_polylog = 0.09 # 傾きの逆数 (eV-1)
    a0_polylog = 64400  # y intensity (arb. units)
    
    # gaussianと線形結合を取る場合
    # fitting_func = "lincom_of_polylog_and_gauss"
    # fitting_func = "PES_of_lincom_of_polylog"
    x_center_gauss=0.3
    x_fwhm_gauss=0.3
    peak_int_gauss=300


    # Fermi-edge
    # fitting_func = "Fermi-edge"
    # x_fitting_min = 12.9
    # x_fitting_max = 13.6
    T = 300
    E_F = 13.3
    a_0 = 55
    fermi_fwhm = 0.1
    bg=0


    if fitting_func == "polylogarithm":
        p0 = [x_vbm_polylog, inverse_slope_of_tail_states_polylog, a0_polylog, bg]
        # 拘束条件
        bounds = [[-np.inf, -np.inf, -np.inf, 0], # x_vbm_polylog, inverse_slope_of_tail_states_polylog, intensity
                [np.inf, np.inf, np.inf, 1e-10]]

    if fitting_func == "lincom_of_polylog_and_gauss":
        p0 = [x_vbm_polylog, inverse_slope_of_tail_states_polylog, a0_polylog, x_center_gauss, x_fwhm_gauss, peak_int_gauss, bg]
        # 拘束条件
        bounds = [[-np.inf, 0, -np.inf, -np.inf, 0, 0, 0], # x_vbm_polylog, inverse_slope_of_tail_states_polylog, intensity
                [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf, 1e-10]]

    elif fitting_func == "Fermi-edge":
        p0 = [T, E_F, fermi_fwhm, a_0, bg]
        bounds = [[-np.inf,-np.inf,-np.inf,-np.inf, 0],
                  [np.inf,np.inf,np.inf,np.inf, 1e-10]]

    # 手動fitting (条件の探索)
    spectrum.fit_spectrum_manually(fitting_func, x_fitting_min, x_fitting_max, p0)
    # fitting analysis
    spectrum.fit_spectrum(fitting_func, x_fitting_min, x_fitting_max, p0, bounds)
    # save results
    spectrum.save_results("fitting")
    #"""


class Spectrum:
    def __init__(self=None, user=None, x=[], y=[], y_lst=[], path=None, x_legend=None, y_legend=None, filename=None, plt_interaction=False): 
        # 初期化
        self.user = user
        self.path = path
        self.y_legend = y_legend
        self.x_legend = x_legend
        self.filename = filename
        self.x=x
        self.y=y
        self.y_lst=y_lst
        # fitting
        self.x_fitting_min = None 
        self.x_fitting_max = None 
        self.p0 = [] 
        self.x_vbm_polylog = None 
        self.inverse_slope_of_tail_states_polylog = None 
        self.a0_polylog = None 
        self.popt = None 
        self.x_fitting = None 
        self.y_fitting = None 
        self.y_fitting_full = None 
        # deconvolution
        self.bg_method = None
        self.x_bg_min = None
        self.x_bg_max = None
        self.x_bg = None
        self.y_bg = None
        self.BG = None
        self.x_s = None
        self.s = None
        self.s_function = []
        self.s_fwhm = None
        self.smoothing_method = None
        self.x_deconv = []
        self.s_deconv = []
        self.i_deconv = []
        self.deconv_method = None
        self.iteration_number = None # iteration number of deconvolution
        self.o_deconv_lst = [] # decovoluted spectra
        self.d_o_deconv_lst = [] # deconvoluted spectraの差
        self.i_reconv_lst = [] # reconvoluted observed spectra
        self.d_i_and_reconv_lst = [] # reconvoluted observed spectraとobserved spectraの差
        self.rmse_i_deconv = [] # reconvoluted observed spectraとobserved spectraで計算したrmse
        self.d_rmse_i_deconv = []
        
        self.polynomial_order_SG=None
        self.window_size_SG=None
        self.iteration_number_SG=None
        self.y_sg_lst=[]
        
        if plt_interaction:
            plt.ion()
    

    def read_labels_from_file_auto(self, idir=None, path=None, filename=None):
        """
        テキスト/CSVファイルから、ラベル行を自動検出して列ラベルをリストで返す関数。
        条件：
        - n行目にラベルがあり、
        - その下に2行以上の数値データが続く（長方形）

        Returns:
            list[str]: 自動検出された列ラベル

        Raises:
            ValueError: ラベル行を自動検出できなかった場合
        """

        import re

        # def is_numeric_line(line):
        #     parts = re.split(r'[\t,]', line.strip())
        #     return all(re.match(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$', val.strip()) for val in parts if val.strip())

        # nanやinfを許容する数値行判定
        def is_numeric_line(line):
            parts = re.split(r'[\t,]', line.strip())
            try:
                [float(val.strip()) for val in parts if val.strip()]
                return True
            except ValueError:
                return False

        if path is not None:
            self.path = path
            self.filename = filename
        else:
            path_lst, filename_lst = rpa.get_path(idir=str(idir))
            self.path=path_lst[0]
            self.filename=filename_lst[0]

        with open(self.path, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        for i in range(len(lines) - 3):  # 最低2行の数値をチェック
            line = lines[i].strip()
            next1 = lines[i + 1].strip()
            next2 = lines[i + 2].strip()

            if not is_numeric_line(line) and is_numeric_line(next1) and is_numeric_line(next2):
                if '\t' in line:
                    labels = line.split('\t')
                elif ',' in line:
                    labels = line.split(',')
                else:
                    labels = line.split()

                self.label_list = [label.strip() for label in labels]
                return self.label_list

        raise ValueError("ラベル行を自動検出できませんでした。")


    # 非推奨だがデータのnanに対応している
    # def load_xy_data_from_file_auto_old(self, x_legend, y_legend, path=None, plot_spectrum=False):
    #     """
    #     .csv や .txt ファイルから、指定ラベルの x, y データを読み込み、解析に必要な属性を初期化する。

    #     Args:
    #         x_legend (str): x軸データのラベル
    #         y_legend (str): y軸データのラベル
    #         plot_spectrum (bool): スペクトルを表示するかどうか
    #     """
    #     import re
    #     import numpy as np
    #     import pandas as pd
    #     import matplotlib.pyplot as plt

    #     # ===== 初期化 =====
    #     if path is not None:
    #         self.path=path
    #     self.x = None
    #     self.y = None
    #     self.y_lst = []
    #     self.x_fitting_min = None 
    #     self.x_fitting_max = None 
    #     self.p0 = [] 
    #     self.x_vbm_polylog = None 
    #     self.inverse_slope_of_tail_states_polylog = None 
    #     self.a0_polylog = None 
    #     self.popt = None 
    #     self.x_fitting = None 
    #     self.y_fitting = None 
    #     self.y_fitting_full = None 
    #     self.bg_method = None
    #     self.x_bg_min = None
    #     self.x_bg_max = None
    #     self.x_bg = None
    #     self.y_bg = None
    #     self.BG = None
    #     self.x_s = None
    #     self.s = None
    #     self.s_function = None
    #     self.s_fwhm = None
    #     self.smoothing_method = None
    #     self.x_deconv = None
    #     self.s_deconv = []
    #     self.i_deconv = []
    #     self.deconv_method = None
    #     self.iteration_number = None
    #     self.o_deconv_lst = []
    #     self.d_o_deconv_lst = []
    #     self.i_reconv_lst = []
    #     self.d_i_and_reconv_lst = []
    #     self.rmse_i_deconv = []
    #     self.d_rmse_i_deconv = []

    #     self.x_legend = x_legend
    #     self.y_legend = y_legend

    #     # ===== 数値データの読み込み =====
    #     def is_numeric_line(line):  # nan, infに対応
    #         parts = re.split(r'[\t,]', line.strip())
    #         try:
    #             [float(val.strip()) for val in parts if val.strip()]
    #             return True
    #         except ValueError:
    #             return False

    #     with open(self.path, encoding='utf-8', mode='r', errors='replace') as f:
    #         lines = f.readlines()
        
    #     for i in range(len(lines) - 3):
    #         if not is_numeric_line(lines[i]) and is_numeric_line(lines[i + 1]) and is_numeric_line(lines[i + 2]):
    #             header_line = lines[i].strip()
    #             data_lines = []
    #             for j in range(i + 1, len(lines)):
    #                 if is_numeric_line(lines[j]):
    #                     data_lines.append(lines[j])
    #                 else:
    #                     break
    #             break
    #     else:
    #         raise ValueError("データ行の検出に失敗しました。")

    #     # 区切り文字
    #     if '\t' in header_line:
    #         delimiter = '\t'
    #     elif ',' in header_line:
    #         delimiter = ','
    #     else:
    #         delimiter = r'\s+'

    #     # ラベルとデータ読み込み
    #     label_list = re.split(delimiter, header_line.strip())
    #     self.label_list = [label.strip() for label in label_list]

    #     data_array = np.genfromtxt(data_lines, delimiter=delimiter)
    #     if data_array.ndim == 1:
    #         data_array = data_array.reshape(-1, len(self.label_list))
    #     df = pd.DataFrame(data_array, columns=self.label_list)

    #     # ===== x, y データ取得 =====
    #     self.x = df[x_legend]
    #     self.y = df[y_legend]
    #     # DataFrame（複数列）になったときは、1列目だけを使う
    #     if isinstance(self.x, pd.DataFrame):
    #         self.x = self.x.iloc[:, 0]
    #     if isinstance(self.y, pd.DataFrame):
    #         self.y = self.y.iloc[:, 0]
    #     valid = ~np.isnan(self.x) & ~np.isnan(self.y)
        
    #     self.x = self.x[valid]
    #     self.y = self.y[valid]
    #     sorted_idx = np.argsort(self.x)
    #     self.x = self.x[sorted_idx].to_numpy()
    #     self.y = self.y[sorted_idx].to_numpy()

    #     self.x_step = np.round(abs(self.x[0] - self.x[1]), 8)
    
    #     # ===== プロット =====
    #     if plot_spectrum:
    #         fig, axs = plt.subplots(2, 1, figsize=(5, 7))
    #         axs[0].scatter(self.x, self.y, label="Imported spectrum", color="tab:gray", s=10)
    #         axs[0].legend()
    #         axs[1].scatter(self.x, self.y, label="Imported spectrum", color="tab:gray", s=10)
    #         axs[1].set_yscale("log")
    #         axs[1].legend()
    #         plt.tight_layout()
    #         plt.show()


    def load_y2_data_from_info_of_file(self, filepath, key_y2=None, key_y2_label=None):
        """
        y2 データやラベルをファイルから読み込む。
        どちらか一方または両方を指定可能。

        Parameters:
            filepath : str
                読み込むファイルのパス
            key_y2 : str or None
                y2 の値を探すためのキー
            key_y2_label : str or None
                y2 のラベルを探すためのキー

        Returns:
            tuple (y2, y2_label)
        """

        # 初期値
        y2 = None
        y2_label = None

        if key_y2 is not None or key_y2_label is not None:
            with open(filepath, encoding='utf-8', errors='replace', mode='r') as f:
                lines_header = [s.strip() for s in f.readlines()]

            if key_y2 is not None:
                y2, _ = rpa.get_list_next_to_search_term(lines_header, key_y2)

            if key_y2_label is not None:
                y2_label, _ = rpa.get_words_next_to_search_term(
                    lines_header, key_y2_label, type='str'
                )

        print("Spectrum data is obtained.")
        return y2, y2_label

    # csv fileからlabelを抽出する。(非推奨)
    def open_csv_file(self,
                    idir=r'G:\マイドライブ\test_spectrum.csv', 
                    path=None, filename=None  # 手打ちするときのpathとfileの名前 (拡張子あり)
                    ): # 入力スぺクトルを表示するときTrue
        
        if path is not None: # 手打ちする場合
            self.path=path
            self.filename=filename
        else: # file explolerで選択する場合
            self.path, self.filename = rpa.get_path(idir=str(idir)) # csvファイルを探す
        try:
            self.label_list = rpa.read_labels_from_csv(self.path)
        except TypeError:
            pass


    # csv fileを開く。nan対応
    def load_xy_data_from_file_auto(self, x_legend, y_legend, plot_spectrum=False):
        # 初期化
        self.x=None
        self.y=None
        self.y_lst=[]
        self.x_fitting_min = None 
        self.x_fitting_max = None 
        self.p0 = [] 
        self.x_vbm_polylog = None 
        self.inverse_slope_of_tail_states_polylog = None 
        self.a0_polylog = None 
        self.popt = None 
        self.x_fitting = None 
        self.y_fitting = None 
        self.y_fitting_full = None 
        # deconvolution
        self.bg_method = None
        self.x_bg_min = None
        self.x_bg_max = None
        self.x_bg = None
        self.y_bg = None
        self.BG = None
        self.x_s = None
        self.s = None
        self.s_function = None
        self.s_fwhm = None
        self.smoothing_method = None
        self.x_deconv = None
        self.s_deconv = []
        self.i_deconv = []
        self.deconv_method = None
        self.iteration_number = None # iteration number of deconvolution
        self.o_deconv_lst = [] # decovoluted spectra
        self.d_o_deconv_lst = [] # deconvoluted spectraの差
        self.i_reconv_lst = [] # reconvoluted observed spectra
        self.d_i_and_reconv_lst = [] # reconvoluted observed spectraとobserved spectraの差
        self.rmse_i_deconv = [] # reconvoluted observed spectraとobserved spectraで計算したrmse
        self.d_rmse_i_deconv = []

        # path内のx, y dataを取得
        self.x_legend = x_legend
        self.y_legend = y_legend
        self.x, self.y = rpa.get_2Ddata_from_text_file_auto(self.path, self.x_legend, self.y_legend)
        self.x_step=np.round(abs(self.x[0]-self.x[1]),8) # なんとなく8桁で丸める。誤差対策。

        print("Spectrum data is obtained.")

        if plot_spectrum:
            fig, axs = plt.subplots(2, 1, figsize=(5, 7))
            axs[0].scatter(self.x, self.y, label="Imported spectrum", color="tab:gray", s=10)
            axs[0].legend()
            axs[1].scatter(self.x, self.y, label="Imported spectrum", color="tab:gray", s=10)
            axs[1].set_yscale("log")
            axs[1].legend()
            plt.show()

        # print(self.x)

    def fit_spectrum_manually(self, fitting_func, x_fitting_min, x_fitting_max, p0):
        """
        手動で調整 (fittingの初期条件の探索)
        """

        # define the energy range これは練習なので self.にしない
        x_fitting = self.x[rpa.get_idx_of_the_nearest(self.x, x_fitting_min): rpa.get_idx_of_the_nearest(self.x, x_fitting_max)]

        # plotting
        fig, axs = plt.subplots(2, 1, figsize=(5, 7))
        # linear scale
        axs[0].scatter(self.x, self.y, label="Observed spectrum", color="tab:gray", s=10)

        # fitting functionを作製
        if fitting_func == "Polylogarithm": 
            y_fitting_full_temp = rpa.make_Menzel2021_fitting_function(self.x, *p0)

        elif fitting_func == "Polylog + Gauss":
            y_fitting_full_temp = rpa.make_lincom_of_polylog_and_gauss(self.x, *p0)

        elif fitting_func == "Polylog + Triple Gauss":
            y_fitting_full_temp = rpa.make_lincom_of_polylog_and_three_gauss(self.x, *p0)

        elif fitting_func == "Fermi–edge of metal (conv. Gauss)":
            y_fitting_full_temp = rpa.make_fermi_edge_metal_conv_gaussian(self.x, *p0)

        elif fitting_func == "Fermi–edge of degenerate semicon. (conv. Gauss)":
            y_fitting_full_temp = rpa.make_fermi_edge_degenerate_semicon_conv_gauss(self.x, *p0)
        
        elif fitting_func == "Fermi–edge of degenerate semicon. (conv. Lorentz and Gauss)":
            y_fitting_full_temp = rpa.make_fermi_edge_degenerate_semicon_conv_lorentz_gauss(self.x, *p0)
        
        elif fitting_func == "Exponential tail":
            y_fitting_full_temp = rpa.make_exponential_tail_states(self.x, *p0)

        elif fitting_func == "Single Gaussian":
            y_fitting_full_temp = rpa.make_gaussian(self.x, *p0)

        elif fitting_func == "Double Gaussian":
            y_fitting_full_temp = rpa.make_two_gaussian(self.x, *p0)

        elif fitting_func == "Triple Gaussian":
            y_fitting_full_temp = rpa.make_three_gaussian(self.x, *p0)
 
        print(y_fitting_full_temp)

        # fitting領域だけ
        y_fitting_temp = y_fitting_full_temp[rpa.get_idx_of_the_nearest(self.x, x_fitting_min): rpa.get_idx_of_the_nearest(self.x, x_fitting_max)]

        # 全エネルギー領域
        axs[0].plot(self.x, y_fitting_full_temp, 
                    label="Extended manual fitting", color="tab:blue", linewidth=1, linestyle="--") 
        axs[1].plot(self.x, y_fitting_full_temp, 
                    label="Extended manual fitting", color="tab:blue", linewidth=1, linestyle="--")
        
        # fitting領域
        axs[0].plot(x_fitting, y_fitting_temp, 
                    label="Manual fitting", color="tab:orange", linewidth=2)
        axs[1].plot(x_fitting, y_fitting_temp, 
                    label="Manual fitting", color="tab:orange", linewidth=2)
        
        # その他設定
        axs[0].invert_xaxis()
        axs[0].set_xlabel("X")
        axs[0].set_ylabel("Y")
        axs[0].set_title("Manual Fitting")
        axs[0].legend()
        
        # log scale
        axs[1].set_yscale("log")
        axs[1].scatter(self.x, self.y, label="Observed spectrum", color="tab:gray", s=10)
        axs[1].invert_xaxis()
        # axs[1].set_ylim(min(y)-max(y)/20, max(y)+max(y)/20)
        # axs[1].set_ylim(0.1, 1000000)
        axs[1].set_xlabel("X")
        axs[1].set_ylabel("Y")
        # axs[1].set_title(f"VBM energy: {np.round(p0[0], 4)} eV, \nInverse slope of tail states: {np.round(p0[1], 4)} eV-1, \nIntensity: {np.round(p0[2], 4)}")
        axs[1].legend()
        plt.show()

    def fit_spectrum_core(self, x_data, y_data, func, initial_params, bounds=None, fixed_params_mask=None, instrum_func_type=None, instrumental_params=[]):
        """
        カスタムフィッティング関数

        Parameters:
        -----------
        x_data: array-like
            独立変数のデータ。
        y_data: array-like
            従属変数のデータ。
        func_choice: str
            キーを指定。'gauss'など。
                    {'Polylogarithm': rpa.make_Menzel2021_fitting_function, 
                    'polylog + gauss': rpa.make_lincom_of_polylog_and_gauss, 
                    'Fermi-edge': rpa.make_fermi_edge_function_with_convoluted_gaussian,
                    'gauss': rpa.make_gaussian}
        initial_params: list
            パラメータの初期値リスト。
        bounds: list of two lists, optional
            パラメータの下限リストと上限リスト（入れ子のリスト）。デフォルトは無限大の範囲。
        fixed_params_mask: list of bool, optional
            パラメータが固定されているかどうかを示すTrue/Falseのリスト。デフォルトはすべてFalse（フィット）。

        Returns:
        --------
        popt: array
            フィットされたパラメータの最適値。
        pcov: 2D array
            パラメータの共分散行列。
        """
        
        # バウンドのデフォルト設定: -∞から+∞まで
        if bounds is None:
            bounds = ([-np.inf] * len(initial_params), [np.inf] * len(initial_params))

        # 固定するかどうかを示すマスクのデフォルト設定: すべてFalse（フィット）
        if fixed_params_mask is None:
            fixed_params_mask = [False] * len(initial_params)

        # 固定されていないパラメータのインデックスを取得
        free_param_indices = [i for i, fixed in enumerate(fixed_params_mask) if not fixed]

        # 固定されていないパラメータのみフィッティングに使用
        free_initial_params = [initial_params[i] for i in free_param_indices]
        free_bounds = ([bounds[0][i] for i in free_param_indices], 
                    [bounds[1][i] for i in free_param_indices])

        # フィッティング関数をラップする
        def wrapped_func(x, *free_params):
            # 固定パラメータとフィットパラメータを結合
            full_params = initial_params.copy()
            for idx, free_val in zip(free_param_indices, free_params):
                full_params[idx] = free_val
            return func(x, *full_params)

        # curve_fitを使用してフィッティング実行
        popt, pcov = curve_fit(wrapped_func, x_data, y_data, p0=free_initial_params, bounds=free_bounds)

        # フィットされたパラメータを全てのパラメータに反映
        full_popt = initial_params.copy()
        for idx, val in zip(free_param_indices, popt):
            full_popt[idx] = val

        return full_popt, pcov

    def fit_spectrum(self,
                    x_fitting_min, x_fitting_max,
                    fitting_func_name,
                    initial_params,
                    bounds,
                    fixed_params_mask,
                    is_broadened_by_instrum_func=False,
                    instrum_func_type=None,
                    instrum_params=[],
                    plots_a_result=True):

        # fitting region
        self.x_fitting_min = x_fitting_min
        self.x_fitting_max = x_fitting_max
        self.x_fitting = self.x[rpa.get_idx_of_the_nearest(self.x, x_fitting_min): 
                                         rpa.get_idx_of_the_nearest(self.x, x_fitting_max)]
        y_fitting = self.y[rpa.get_idx_of_the_nearest(self.x, x_fitting_min): 
                                         rpa.get_idx_of_the_nearest(self.x, x_fitting_max)]
        
        # fitting実行
        self.p0=initial_params
        self.bound=bounds
        self.fixed_params_mask=fixed_params_mask

        self.fitting_func=fitting_func_name

        # ==== fitting関数を決定 ====
        # 通常とconvolution付きの両方をdictで対応
        func_dict = {
            'Polylogarithm': rpa.make_Menzel2021_fitting_function,
            'Polylog + Gauss': rpa.make_lincom_of_polylog_and_gauss,
            'Polylog + Triple Gauss': rpa.make_lincom_of_polylog_and_three_gauss,
            'Fermi–edge of metal (conv. Gauss)': rpa.make_fermi_edge_metal_conv_gaussian,
            'Exponential tail': rpa.make_exponential_tail_states,
            'Single Gaussian': rpa.make_gaussian,
            'Double Gaussian': rpa.make_two_gaussian,
            'Triple Gaussian': rpa.make_three_gaussian,
            'Fermi–edge of degenerate semicon. (conv. Gauss)': rpa.make_fermi_edge_degenerate_semicon_conv_gauss,
            'Fermi–edge of degenerate semicon. (conv. Lorentz and Gauss)': rpa.make_fermi_edge_degenerate_semicon_conv_lorentz_gauss,
        }

        base_func = func_dict[fitting_func_name]

        # convolution処理をラップする
        if is_broadened_by_instrum_func:
            if instrum_func_type is 'Gaussian':
                def convoluted_fit_func(x, instrum_params, *params):
                    y = base_func(x, *params)
                    if instrum_func_type == 'Gaussian':
                        instrum_func = rpa.make_gaussian(x, 0, instrum_params[0], 1, 0)  # 正規化されたガウス関数
                    return rpa.convolve(y, instrum_func, self.x_step)
                fit_func = convoluted_fit_func
            else:
                fit_func = base_func
        else:
            fit_func = base_func
        
        # fitting実行
        try:
            # self.popt, self.pcov = self.fit_spectrum_core(self.x_fitting, y_fitting, func_dict[self.fitting_func], 
            #                                 self.p0, self.bound, self.fixed_params_mask)
            self.popt, self.pcov = self.fit_spectrum_core(self.x_fitting, y_fitting, fit_func, 
                                            self.p0, self.bound, self.fixed_params_mask)
        except RuntimeError:
            messagebox.showwarning('RuntimeError!','RuntimeError.\tPlease reset fitting parameters.')

        print("Fitting complete!")
        print("Results:", self.popt)

        # fitting spectrum作製
        self.y_fitting_full=func_dict[self.fitting_func](self.x, *self.popt)
        self.y_fitting=self.y_fitting_full[
                                        rpa.get_idx_of_the_nearest(self.x, x_fitting_min): 
                                        rpa.get_idx_of_the_nearest(self.x, x_fitting_max)
                                        ]

        # plotting 
        if plots_a_result:
            # サブプロットを作成
            
            fig, axs = plt.subplots(2, 1, figsize=(5, 7))
            # linear scale
            axs[0].scatter(self.x, self.y, label="Observed spectrum", color="tab:gray", s=10) # scatter表示
            # axs[0].plot(self.x, self.y, label="Observed spectrum", color="tab:gray", linewidth=1.5) # line表示
            axs[0].plot(self.x, self.y_fitting_full, label="Extended fitting func.",linewidth=1, linestyle="--", color='tab:blue') # full range
            axs[0].plot(self.x_fitting, self.y_fitting, label="Fitting func.", linewidth=3, color='black')
            axs[0].set_xlabel("X")
            axs[0].set_ylabel("Y")
            # axs[0].set_title("Fitting result")
            
            # log scale
            axs[1].set_yscale("log")
            axs[1].scatter(self.x, self.y, label="Observed spectrum", color="tab:gray", s=10)
            axs[1].plot(self.x, self.y_fitting_full, label="Extended fitting func.",linewidth=1, linestyle="--", color='tab:blue') # full range
            axs[1].plot(self.x_fitting, self.y_fitting, label="Fitting func.", linewidth=3, color='black')
            
            # 線形結合の各項をplot
            if self.fitting_func=="Polylog + Gauss":
                y1 = rpa.make_Menzel2021_fitting_function(self.x, self.popt[0], self.popt[1], self.popt[2], self.popt[-1])
                y2 = rpa.make_gaussian(self.x, self.popt[3], self.popt[4], self.popt[5], self.popt[-1])

                axs[1].fill_between(self.x, self.popt[-1], y1, label="olylogarithm", linewidth=0, alpha=0.3, color="tab:blue")
                axs[1].fill_between(self.x, self.popt[-1], y2, label="gaussian", linewidth=0, alpha=0.3, color="tab:red")
            
            elif self.fitting_func == "Fermi–edge of degenerate semicon. (conv. Gauss)":
                y_gapstate = self.popt[0] * np.exp((self.x - self.popt[1])/self.popt[2]) + self.popt[-1]
                y_CB = self.popt[4] * np.sqrt(np.clip(- self.x + self.popt[3], 0, None)) + self.popt[-1]

                axs[0].fill_between(self.x, self.popt[-1], y_gapstate, label="in-gap states", linewidth=0, alpha=0.3, color="tab:blue")
                axs[0].fill_between(self.x, self.popt[-1], y_CB, label="CB", linewidth=0, color="tab:orange", alpha=0.3)
                axs[1].fill_between(self.x, self.popt[-1], y_gapstate, label="in-gap states", linewidth=0, alpha=0.3, color="tab:blue") 
                axs[1].fill_between(self.x, self.popt[-1], y_CB, label="CB", linewidth=0, color="tab:orange", alpha=0.3)

            elif self.fitting_func == "Fermi–edge of degenerate semicon. (conv. Lorentz and Gauss)":
                def _lifetime_broadening(x):
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
                    x_gauss = np.round(np.arange(-(len(x_)-1)*step/2, (len(x_)-1)*step/2 + step/10, step), 6) # 装置関数用のx軸
                    y_lifetime = rpa.make_gaussian(x_gauss, 0, self.popt[5], peak_intensity=1, bg=0)

                    # 元のDOS関数
                    y_gapstate = self.popt[0] * np.exp((x_ - self.popt[1])/self.popt[2])

                    # y_CB = self.popt[4] * np.sqrt(np.clip(- x_ + self.popt[3], 0, None)) # parabolic band
                    y_CB = self.popt[4] * np.sqrt(np.clip(-(x_ - self.popt[3])*(1+0.2*(x_ - self.popt[3])), 0, None))*(1 + 2 * 0.2 * (x_ - self.popt[3])) # InNの非放物線バンドに対応
                    y_gapstate = np.convolve(y_gapstate, y_lifetime, mode='same') * step + self.popt[-1]
                    y_CB = np.convolve(y_CB, y_lifetime, mode='same') * step + self.popt[-1]
                    # 元のx軸に合わせて切り取る 
                    y_gapstate = y_gapstate[rpa.get_idx_of_the_nearest(x_, x_min) : rpa.get_idx_of_the_nearest(x_, x_max)+1]
                    y_CB = y_CB[rpa.get_idx_of_the_nearest(x_, x_min) : rpa.get_idx_of_the_nearest(x_, x_max)+1]
                    return y_gapstate, y_CB

                # lifetime broadening
                y_gapstate, y_CB = _lifetime_broadening(self.x)
                # broadning後のDOSプロット
                axs[0].fill_between(self.x, self.popt[-1], y_gapstate, label="in-gap states", linewidth=0, alpha=0.3, color="tab:blue")
                axs[0].fill_between(self.x, self.popt[-1], y_CB, label="CB", linewidth=0, color="tab:orange", alpha=0.3)
                axs[1].fill_between(self.x, self.popt[-1], y_gapstate, label="in-gap states", linewidth=0, alpha=0.3, color="tab:blue") 
                axs[1].fill_between(self.x, self.popt[-1], y_CB, label="CB", linewidth=0, color="tab:orange", alpha=0.3)


            elif self.fitting_func == 'Double Gaussian':
                y1 = rpa.make_gaussian(self.x, self.popt[0], self.popt[1], self.popt[2], self.popt[-1])
                y2 = rpa.make_gaussian(self.x, self.popt[3], self.popt[4], self.popt[5], self.popt[-1])
                
                axs[0].fill_between(self.x, self.popt[-1], y1, label="gaussian1", alpha=0.3, color="tab:blue", linewidth=0) # x・下限・上限
                axs[0].fill_between(self.x, self.popt[-1], y2, label="gaussian2", alpha=0.3, color="tab:red", linewidth=0) # x・下限・上限

                # peak positions
                peak1=rpa.get_idx_of_the_nearest(self.x, self.popt[0])
                peak2=rpa.get_idx_of_the_nearest(self.x, self.popt[3])
                axs[0].scatter(self.x[peak1], self.y_fitting_full[peak1]*1.1, color='tab:red', linewidth=4, s=140, marker='|')
                axs[0].scatter(self.x[peak2], self.y_fitting_full[peak2]*1.1, color='tab:red', linewidth=4, s=140, marker='|')

            elif self.fitting_func == 'Triple Gaussian':
                y1 = rpa.make_gaussian(self.x, self.popt[0], self.popt[1], self.popt[2], self.popt[-1])
                y2 = rpa.make_gaussian(self.x, self.popt[3], self.popt[4], self.popt[5], self.popt[-1])
                y3 = rpa.make_gaussian(self.x, self.popt[6], self.popt[7], self.popt[8], self.popt[-1])

                axs[0].fill_between(self.x, self.popt[-1], y1, label="gaussian1", alpha=0.3, color="tab:blue", linewidth=0) # x・下限・上限
                axs[0].fill_between(self.x, self.popt[-1], y2, label="gaussian2", alpha=0.3, color="tab:red", linewidth=0) # x・下限・上限
                axs[0].fill_between(self.x, self.popt[-1], y3, label="gaussian3", alpha=0.3, color="tab:orange", linewidth=0) # x・下限・上限

                # peak positions
                peak1=rpa.get_idx_of_the_nearest(self.x, self.popt[0])
                peak2=rpa.get_idx_of_the_nearest(self.x, self.popt[3])
                peak3=rpa.get_idx_of_the_nearest(self.x, self.popt[6])
                axs[0].scatter(self.x[peak1], self.y_fitting_full[peak1]*1.1, color='tab:red', linewidth=4, s=140, marker='|')
                axs[0].scatter(self.x[peak2], self.y_fitting_full[peak2]*1.1, color='tab:red', linewidth=4, s=140, marker='|')
                axs[0].scatter(self.x[peak3], self.y_fitting_full[peak3]*1.1, color='tab:red', linewidth=4, s=140, marker='|')

            axs[1].set_xlabel("X")
            axs[1].set_ylabel("Y")

            # title
            axs[0].set_title(f"Y Label: {self.y_legend}\nFilename: {self.filename}")
            axs[0].legend()
            axs[1].legend()

            plt.tight_layout()
            plt.show()


    def save_results(self, analysis, is_GUI=False, info_note=None, path_note=None, legend_note=None):
        ###################################################
        # saveを行う中身
        def save(analysis):

            # ピーク検出をしたときは結果を末尾に追記
            if analysis=="peak_detection":
                with open(self.savefile_path, mode='a', newline='', errors='replace') as f:
                    writer = csv.writer(f)
                    ITERATION_PEAK = f"ITE_{self.y_legend}_deconvpeak{legend_note}"
                    X_DECONV_PEAK = f"{self.x_legend}_deconvpeak{legend_note}"
                    Y_DECONV_PEAK = f"{self.y_legend}_deconvpeak{legend_note}"
                    writer.writerow([""])
                    writer.writerow([ITERATION_PEAK, X_DECONV_PEAK, Y_DECONV_PEAK])
                    for i in range(len(self.x_y_peak_lst)):
                        for j in range(len(self.x_y_peak_lst[i])):
                            writer.writerow([self.idx_y_peak_lst[i][j], self.x_y_peak_lst[i][j], self.y_peak_lst[i][j]])
            
            # 普通のとき
            else:
                with open(self.savefile_path, mode='w', newline='', errors='replace') as f:
                    writer = csv.writer(f)

                    # title
                    if analysis=="fitting":
                        writer.writerow(['[SpecTaroscoPy 0 Fitting]'])
                    elif analysis=="deconvolution":
                        writer.writerow(['[SpecTaroscoPy — Deconvolution]'])

                    writer.writerow(['Author\tR Nakazawa'])
                    writer.writerow(['Contact\tnakazawa@ims.ac.jp'])
                    writer.writerow([f"Version\t{VERSION_NUMBER}"])
                    writer.writerow(["--- Info ---"])
                    writer.writerow([f"User\t{self.user}"])

                    date = datetime.datetime.now()  # 現在時刻
                    writer.writerow([f"Date\t{date}"])

                    writer.writerow([f"Load File Path\t{self.path}"])
                    writer.writerow([f"{self.x_legend}\t{' '.join(map(str, self.x))}"])
                    writer.writerow([f"{self.y_legend}\t{' '.join(map(str, self.y))}"])
                    writer.writerow([f'Save File Path\t{self.savefile_path}'])
                    writer.writerow([f"Comment\t{info_note}"])
                    
                    # fitting解析の時の処理
                    if analysis == "fitting":
                        # label作成
                        X_INPUT =   f"Xinput{legend_note}"
                        Y_INPUT  = f"Yinput{legend_note}"
                        Y_FIT_FULL = f"Yfit_full{legend_note}"
                        X_FIT = f"Xfit{legend_note}"
                        Y_FIT = f"Yfit{legend_note}"
                        # data save
                        writer.writerow(["--- Fitting initial parameters ---"])
                        writer.writerow([f"Function\t{self.fitting_func}"])
                        if self.fitting_func == "polylogarithm":
                            writer.writerow(["Reference: D. Menzel, et al., ACS Appl. Mater. and Interfaces 13, 43540 (2021)"])
                        elif self.fitting_func == "lincom_of_polylog_and_gauss":
                            writer.writerow(["Reference: D. Menzel, et al., ACS Appl. Mater. and Interfaces 13, 43540 (2021)"])
                        elif self.fitting_func == "lincom_of_polylog_and_three_gauss":
                            writer.writerow(["Reference: D. Menzel, et al., ACS Appl. Mater. and Interfaces 13, 43540 (2021)"])
                        writer.writerow([f"Initial Params\t{' '.join(map(str, self.p0))}"])
                        writer.writerow([f"Fixed Paramrs\t{' '.join(map(str, self.fixed_params_mask))}"])
                        writer.writerow([f"Lower Limit\t{' '.join(map(str, self.bound[0]))}"])
                        writer.writerow([f"Upper Limit\t{' '.join(map(str, self.bound[1]))}"])
                        writer.writerow([f"X Min FitRegion\t{self.x_fitting_min}"])
                        writer.writerow([f"X Max FitRegion\t{self.x_fitting_max}"])
                        writer.writerow(["--- Fitting Result ---"])
                        writer.writerow([f"Parameters\t{' '.join(map(str, self.popt))}"])

                        writer.writerow([]) #空行
                        #deconvolution スペクトルデータ
                        writer.writerow(["DATA:"])
                        writer.writerow(["\t".join([X_INPUT, Y_INPUT, Y_FIT_FULL])])  # 全体

                        for i in range(len(self.x)):
                            writer.writerow([f"{self.x[i]}\t{self.y[i]}\t{self.y_fitting_full[i]}"])
                        writer.writerow([])  # 空行
                        
                        writer.writerow(["\t".join([X_FIT, Y_FIT])]) # fitting範囲だけ
                        for i in range(len(self.x_fitting)):
                            writer.writerow([f"{self.x_fitting[i]}\t{self.y_fitting[i]}"])
                    
                    # deconvolution解析の時の処理
                    elif analysis == "deconvolution":
                        # label生成
                        X_INPUT  = f"{self.x_legend}{legend_note}"
                        Y_INPUT  = f"{self.y_legend}{legend_note}"
                        Y_SPREAD  = f"{self.y_legend}_deconv_s{legend_note}"
                        X_BG = f"{self.x_legend}_deconv_i{legend_note}"
                        Y_BG = f"{self.y_legend}_deconv_i{legend_note}"
                        Y_DECONV_lst=[]
                        Y_RECONV_lst=[]
                        Y_RESIDUAL_lst=[]
                        for i in range(int(self.iteration_number)):
                            Y_DECONV_lst.append(f"{self.y_legend}_deconv_o{i+1}{legend_note}")
                            Y_RECONV_lst.append(f"{self.y_legend}_reconv_i{i+1}{legend_note}")
                            Y_RESIDUAL_lst.append(f"{self.y_legend}_residual_i{i+1}{legend_note}")
                        RMSE=f"RMSE_{self.y_legend}{legend_note}"
                        DRMSE=f"dRMSE_{self.y_legend}{legend_note}"

                        writer.writerow(["--- Background procedure ---"])
                        writer.writerow([f"Method\t{self.bg_method}"])
                        if self.bg_method == "Constant":
                            writer.writerow([f"X Min BGRegion\t{self.x_bg_min}"])
                            writer.writerow([f"X Max BGRegion\t{self.x_bg_max}"])
                            writer.writerow([f"BG Intensity\t{self.BG}"])
                        if self.bg_method == "Constant BG + Gaussian":
                            writer.writerow([f"X Min BGRegion\t{self.x_bg_min}"])
                            writer.writerow([f"X Max BGRegion\t{self.x_bg_max}"])
                            writer.writerow([f"BG Intensity\t{self.BG}"])
                            writer.writerow([f"X Min FitRegion\t{self.x_fitting_min}"])
                            writer.writerow([f"X Max FitRegion\t{self.x_fitting_max}"])
                            writer.writerow([f"Gaussian Parameters\t{' '.join(map(str, self.popt))}"])
                            
                        writer.writerow(["--- Spread function ---"])
                        writer.writerow([f"Function\t{self.s_function}"])
                        if self.s_function == "Gaussian":
                            writer.writerow([f"FWHM\t{self.s_fwhm}"])

                        writer.writerow(["--- Smoothing ---"])
                        writer.writerow([f"Method\t{self.smoothing_method}"])

                        writer.writerow(["--- Deconvolution ---"])
                        writer.writerow([f"Method\t{self.deconv_method}"])
                        if self.deconv_method == "Jansson's method":
                            writer.writerow([f"a\t{self.a_jansson}"])
                            writer.writerow([f"b\t{self.b_jansson}"])
                            writer.writerow([f"r_0\t{self.r0_jansson}"])

                        writer.writerow([f"Iteration Number\t{self.iteration_number}"])
                        writer.writerow([f"X Min RMSERegion\t{self.x_rmse_min}"])
                        writer.writerow([f"X Max RMSERegion\t{self.x_rmse_max}"])
                        writer.writerow([])
                        writer.writerow(["DATA:"])
                        writer.writerow(["\t".join([X_BG, Y_SPREAD, Y_BG] + Y_DECONV_lst + Y_RECONV_lst + Y_RESIDUAL_lst)]) # legend

                        # x data
                        if self.x_bg is None:
                            x = copy.deepcopy(self.x)
                        else:
                            x = copy.deepcopy(self.x_bg)
                        # y data
                        if self.y_bg is None:
                            y = copy.deepcopy(self.y)
                        else:
                            y = copy.deepcopy(self.y_bg)

                        # 数値データ連結して書き込み
                        for x_, s_, y_, ydeconv_, yreconv_, yresidual_ in zip(
                                x, self.s, y, self.o_deconv_lst.T, self.i_reconv_lst.T, self.d_i_and_reconv_lst.T):
                            writer.writerow([f"{x_}\t{s_}\t{y_}\t" + "\t".join(map(str, list(ydeconv_) + list(yreconv_) + list(yresidual_)))])
                        writer.writerow([""])

                        # RMSE
                        writer.writerow(["\t".join([RMSE, DRMSE])])
                        for i in range(len(self.rmse_i_deconv)):
                            writer.writerow([f"{self.rmse_i_deconv[i]}\t{self.d_rmse_i_deconv[i]}"])

            print('Data was successfully saved.')
            print(f'path: {self.savefile_path}')
            
        ####################################################

        #GUIの時の処理
        if not is_GUI:
            # 但し書き
            info_note=input(f'[Info] に入れる但し書き。') # [info]に入れるメモ
            # 但し書き
            path_note=input(f'ファイル名に入れる但し書き。') #savefileに入れるメモ
            if path_note is not None:
                path_note=f'_{path_note}'
            # 但し書き
            legend_note=input(f'凡例に入れる但し書き。') #ラベルに入れるメモ
            if legend_note is not None:
                legend_note=f'_{legend_note}'

        # resultsというフォルダを作る
        if analysis=='deconvolution':
            foldername=f'STPy_Deconvolution'
            foldername = foldername.replace('.', '_')
        elif analysis=='fitting':
            foldername=f'STPy_Fitting'
            foldername = foldername.replace('.', '_')
        rpa.create_folder_at_current_path(self.path, foldername)

        # fileのパスを作成
        if analysis=='deconvolution':
            self.savefile_path = self.path.replace(self.filename, f"{foldername}/deconv_{self.filename}") 
        elif analysis=='fitting':
            self.savefile_path = self.path.replace(self.filename, f"{foldername}/fit_{self.filename}") 
        
        if path_note is not None:
            self.savefile_path = self.savefile_path.replace(".csv", f"{path_note}.csv") # path_noteを付け足す
            self.savefile_path = self.savefile_path.replace(".txt", f"{path_note}.txt") # path_noteを付け足す

        # 以下でsaveを行う
        # detect peakをしたときは追記する。
        if analysis=="peak_detection":
            save("peak_detection")
        # それ以外の時
        elif not os.path.isfile(self.savefile_path): # saveファイルが重複しない場合はsave
            save(analysis)
        else: # saveファイルが存在する場合、上書きするか確認する
            overwrite = rpa.ask_me("Confirmation of save", "Do you want to overwrite existing file? (y/n)") # popup
            if overwrite == 'y': # yesを選択すればsave
                save(analysis)
            else: # noを選択すれば保存しない
                print('Aborted.')

    def subtract_const_gauss_background(self, x_bg_min, x_bg_max,
                                        x_fit_min, x_fit_max,
                                        p0=[0,0,0,0], bounds=None, fixed_params_mask=None, 
                                        gauss_x_side='High X Side'):
        """
        input dataのバックグラウンド処理をします。定数を引くのとスペクトル端をgaussianに置換します。
        x_bg_min: background領域の最小値
        x_bg_max: background領域の最大値
        x_fit_min: fitting領域の最小値
        x_fit_max: fitting領域の最大値
        p0: リスト。fittingの初期値. paramはピーク強度（定数バックグラウンド引く前）、ピークエネルギー、FWHM、バックグラウンド強度
        bounds: リスト。fittingの制限. ([bound_min: パラメータの数だけ], [bound_max: paramの数だけ])
        fixed_params_mask: リスト。paramを固定するかどうか。Trueのとき固定
        gauss_x_side: fittingで置換される方。'High X Side' or 'Low X Side'と記入
        -----
        x_input, y_inputともにdefaultならself.x_bg, self.y_bgを作成。
        どちらかでもdefaultでない場合、x_bgとy_bgをreturnするので、お好きに定義して下さい。

        """

        self.bg_method="Constant BG + Gaussian"
        self.x_bg_min = x_bg_min
        self.x_bg_max = x_bg_max
        self.BG = np.average(self.y[rpa.get_idx_of_the_nearest(self.x,x_bg_min):
                                    rpa.get_idx_of_the_nearest(self.x,x_bg_max)])
        p0[-1]=self.BG
        # print(p0)
        fixed_params_mask=[False,False,False,True] # backgroundはfitting paramから外す。
        #######
        self.fit_spectrum(
                    x_fit_min, x_fit_max,
                    'Single Gaussian',
                    initial_params=p0,
                    bounds=bounds,
                    fixed_params_mask=fixed_params_mask,
                    plots_a_result=False)
        
        print(self.popt)
        # フィッティングされた関数を元のデータに足し合わせる
        if gauss_x_side=='high':
            x_fit_func = np.arange(np.amin(self.x), self.popt[0]+self.popt[1]*2,self.x_step)
            fit_func = rpa.make_gaussian(x_fit_func, *self.popt)
            i_smooth = np.concatenate([self.y[:rpa.get_idx_of_the_nearest(self.x, x_fit_min)], 
                                    fit_func[rpa.get_idx_of_the_nearest(x_fit_func, x_fit_min):]])
            x_smooth = np.concatenate([self.x[:rpa.get_idx_of_the_nearest(self.x, x_fit_min)], 
                                    x_fit_func[rpa.get_idx_of_the_nearest(x_fit_func, x_fit_min):]])
        else:
            x_fit_func = np.arange(self.popt[0]-self.popt[1]*2,np.amax(self.x),self.x_step)
            fit_func = rpa.make_gaussian(x_fit_func, *self.popt)
            i_smooth = np.concatenate([fit_func[:rpa.get_idx_of_the_nearest(x_fit_func, x_fit_max)],
                                    self.y[rpa.get_idx_of_the_nearest(self.x, x_fit_max):]])
            x_smooth = np.concatenate([x_fit_func[:rpa.get_idx_of_the_nearest(x_fit_func, x_fit_max)],
                                    self.x[rpa.get_idx_of_the_nearest(self.x, x_fit_max):]])
        self.x_bg=copy.deepcopy(x_smooth)
        i_smooth-=self.popt[-1] # backgroundを減算
        self.y_bg=copy.deepcopy(i_smooth)   
            
    def subtract_constant_background(self, x_bg_min=None, x_bg_max=None):
        self.bg_method='Constant'
        self.x_bg_max = x_bg_min
        self.x_bg_min = x_bg_max
        self.BG = np.average(self.y[rpa.get_idx_of_the_nearest(self.x,x_bg_min):
                                    rpa.get_idx_of_the_nearest(self.x,x_bg_max)])
        self.y_bg = self.y-self.BG
        self.x_bg = copy.deepcopy(self.x)

    def generate_spread_function_for_deconvolution(self, x, func="Gaussian", *params):
        """
        x: np.array() 1D形式
        func: 'Gaussian' or 'Import'
        params: 'Gaussian'のときFWHMを。'Import'のときimportしたデータをそのまま入れる. 多分1Dのndarray
        """
        # ここから装置関数生成
        step = abs(x[0] - x[1])
        self.x_s = np.round(np.arange(-(len(x)-1)/2*step,(len(x)-1)*step/2+step/10,step),6) #装置関数の定義域 Cが要素nの時、0を中心に2n+1個生成する。# */m*step,(len(Csg)-1)*step/m+step/2, step にして、いい感じに切る(mでそろえること)
        
        self.s_function=func
        if self.s_function=="Gaussian":
            self.s_fwhm= params[0]
            self.s = rpa.make_gaussian(self.x_s, 0, self.s_fwhm)
        elif self.s_function=="Import":
            self.s = params[0] # 関数を入力する
            self.s = self.s/np.sum(self.s*abs(x[0]-x[1])) #面積1に規格化->Jansson法でうまくいく

    def smooth_spectrum_with_auto_cross_colleration(self, i, s):       
        self.smoothing_method="Auto-/cross-correlation"
        self.i_ac = rpa.conv(i, np.flip(s), self.x_step)
        self.s_cc = rpa.conv(s, np.flip(s), self.x_step)

    def deconvolute_spectrum(self, x_deconv, i0, i_deconv, s_deconv,
                             iteration_number, 
                             x_rmse_min, x_rmse_max, 
                             method, *params):
        # i0は測定生スペクトルの強度データ。
        # x_deconv, i_deconv, s_deconvを使用してdeconvolutionが行われる。(スムージング後)
        # Auto-/cross-correlationを使用したときは、Auto-/cross-correlated spectraを。
        # paramsはパラメータを打ち込む必要があるmethodを使用時に入れる。
        # x_deconvは等間隔のデータであること。間隔は、下でself.x_stepで計算する。

        # 初期化
        self.x_deconv = x_deconv # energy
        self.x_step = abs(x_deconv[0]-self.x_deconv[1])
        self.i_deconv = i_deconv # observed spectra
        self.s_deconv = s_deconv # spread func
        self.iteration_number = iteration_number # iteration number of deconvolution
        self.o_deconv_lst = np.zeros((int(self.iteration_number), len(self.x_deconv))) # decovoluted spectra
        self.d_o_deconv_lst = np.zeros((int(self.iteration_number), len(self.x_deconv))) # deconvoluted spectraの差
        self.i_reconv_lst = np.zeros((int(self.iteration_number), len(self.x_deconv))) # reconvoluted observed spectra
        self.d_i_and_reconv_lst = np.zeros((int(self.iteration_number), len(self.x_deconv))) # reconvoluted observed spectraとobserved spectraの差

        self.deconv_method = method

        self.x_rmse_min = x_rmse_min # rmseを計算するエネルギーの最小値
        self.x_rmse_max = x_rmse_max # rmseを計算するエネルギーの最大値

        idx_x_rmse_min = rpa.get_idx_of_the_nearest(self.x_deconv, self.x_rmse_min) # idexに変換
        idx_x_rmse_max = rpa.get_idx_of_the_nearest(self.x_deconv, self.x_rmse_max) # idexに変換

        self.rmse_i_deconv = np.zeros(self.iteration_number) # reconvoluted observed spectraとobserved spectraで計算したrmse
        self.d_rmse_i_deconv = np.zeros(self.iteration_number) # rmseの差

        # Jansson's parameters
        if self.deconv_method=="Jansson's method":
            # print(params)
            self.a_jansson = params[0]
            self.b_jansson = params[1]*np.amax(self.i_deconv)
            self.r0_jansson = params[2]*params[1]

        # deconvolution 実行部
        # iteration (k), k=1
        o_deconv = self.i_deconv 
        # k>=2
        for i in range(self.iteration_number):
            if self.deconv_method == "Jansson's method":
                self.o_deconv_lst[i] = rpa.deconvolute_spectrum_by_jannson(o_deconv, self.s_deconv, self.i_deconv, self.x_step, self.a_jansson, self.b_jansson, self.r0_jansson)
            if self.deconv_method == "Gold's ratio method":
                self.o_deconv_lst[i] = rpa.deconvolute_spectrum_by_gold(o_deconv, self.s_deconv, self.i_deconv, self.x_step)
            
            # 残差の計算
            self.i_reconv_lst[i] = rpa.conv(self.o_deconv_lst[i], self.s, self.x_step) # reconvoluted observed spectrum
            self.d_i_and_reconv_lst[i] = self.i_reconv_lst[i] - i0 # reconvoluted observed spectrumとobserved spectrumの残差

            # 指定した範囲でrmseの計算
            self.rmse_i_deconv[i] = np.sqrt(np.sum(self.d_i_and_reconv_lst[i][idx_x_rmse_min: idx_x_rmse_max]**2) /len(self.d_i_and_reconv_lst[i][idx_x_rmse_min: idx_x_rmse_max]))
            # kとk-1番目のrmseの差をとる
            if i==0: # k=1のときだけ例外処理
                self.d_rmse_i_deconv[i] = None
            else:
                self.d_rmse_i_deconv[i] = self.rmse_i_deconv[i-1] -self.rmse_i_deconv[i]

            # 次のitearationに向けてo_deconvを更新する
            o_deconv = self.o_deconv_lst[i]

    def detect_peak_of_spectrum_lst(self, x, y_lst, order=5):
        # 初期化
        self.idx_y_peak_lst = [] # idx number (deconvolutionの場合、iteration number-1 に相当する)
        self.y_peak_lst=[] # ピーク強度
        self.x_y_peak_lst=[] # ピークエネルギー

        maxid_y = scipy.signal.argrelmax(y_lst, order=order,axis=1) #最小値のindexの取得
        idx_y_peak_lst = maxid_y[0] # idx number リスト
   
        for j in range(len(maxid_y[1])):
            self.x_y_peak_lst.append(x[maxid_y[1][j]].tolist()) #energyのリスト

        for j in range(len(maxid_y[1])):
            self.y_peak_lst.append(y_lst[maxid_y[0][j], maxid_y[1][j]].tolist()) #yのリスト

        # iterationで区切られた多次元配列にする
        self.idx_y_peak_lst, self.x_y_peak_lst = rpa.rearrange_nd_lst_to_1d_lst(idx_y_peak_lst, self.x_y_peak_lst)
        _, self.y_peak_lst = rpa.rearrange_nd_lst_to_1d_lst(idx_y_peak_lst, self.y_peak_lst)
        
        # iteration numberが1から始まるように調整
        for i in range(len(self.idx_y_peak_lst)):
            for j in range(len(self.idx_y_peak_lst[i])):
                self.idx_y_peak_lst[i][j] += 1

    def smooth_spectra_by_SG(self, y, order, window, iteration):       
        if window % 2 != 0:
            self.polynomial_order_SG=order
            self.window_size_SG=window
            self.iteration_number_SG=iteration
            self.y_sg_lst=[]
            iteration=0

            y_sg=np.copy(y)

            while iteration < self.iteration_number_SG:
                # https://docs.scipy.org/doc/scipy/reference/generated/scipy.sig_nal.savgol_filter.html#scipy.signal.savgol_filter
                y_sg = scipy.signal.savgol_filter(y_sg, self.window_size_SG, self.polynomial_order_SG, mode='nearest')
                self.y_sg_lst.append(y_sg)
                iteration+=1

        else: # windowが偶数のときは警告文を出して終わり。
            messagebox.showwarning('Invalid Window Length', f"Error!\nWindow length must be an odd number.")

    # def second_derivative_spectrum(self, y):
    #     """
    #     y: 1D array
    #     """
    #     self.y_second_derivative = np.gradient(np.gradient(y, self.x_step), self.x_step)
    #     return self.y_second_derivative

if __name__ == "__main__":
    # pass
    main()