import copy
import numpy as np
import re
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scipy.interpolate import griddata
from pathlib import Path
from scipy.signal import argrelmax, argrelmin
from RyoPy.PlotControl import ImagePlotControl, PlotControl
from RyoPy.MBS_A1 import MBS_A1
import RyoPy.defs_for_analysis as rpa
import matplotlib.pyplot as plt


# SpectrumAnalyzer用にデータを読み込む
try:
    # 現在のスクリプトの親ディレクトリを取得
    SRC_PATH = Path(__file__).resolve().parent.parent
    print('src_path:', SRC_PATH)
    # ファイルパスを統一的に管理
    default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
    # txtを開き、入力値を取得
    VERSION_NUMBER, hoge=rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "version", type="str")
    user, hoge=rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")
except:
    pass

ORDER_Y=10
ORDER_X=10  

def main():
    main_image_analysis()
    # main_second_derivative()

def main_second_derivative():
    # インスタンス作製
    peim=IgorPro_Image()
    peim_plot = PlotControl(title="imported data")
    peim_image_plot = ImagePlotControl(peim.x, peim.y, peim.z)
    peim_image_plot.show_figures()
    z_sg=peim.smooth_image_SG(peim.z, 2, 25, 10)
    z_ddx=peim.second_derivative(peim.x, z_sg, 0)
    peim_image_ddx_plot=ImagePlotControl(peim.x, peim.y, z_ddx)
    # for i in range(len(peim.z)):
    #     peim_pltctrl.add_spectrum(peim.x, peim.z[i], label=None, linewidth=1, scatter=False, color="tab:blue")
    #     peim_pltctrl.add_spectrum(peim.x, peim.z_sg[i], label=None, linewidth=1, scatter=False, color="tab:blue")
    peim_plot.show_figures()
    peim_image_ddx_plot.show_figures()

def main_image_analysis():   
    # data読み込み
    peim=IgorPro_Image(plt_show=True) #photoemission intensity map

    print(len(peim.x), len(peim.y), len(peim.z), len(peim.z[0]))
    
    peim_pltcntrl=ImagePlotControl(peim.x, peim.y, peim.z, 
                            title="Photoemission Intensity Map", 
                            x_label=peim.x_label, 
                            y_label=peim.y_label, 
                            z_label=peim.z_label, 
                            plt_interaction=True)
    peim_pltcntrl.show_figures()
    
    """
    # Ek -> EB
    hn=21.22
    x_EF=16.99
    Vsample=0
    peim.convert_axis_in_one_photon_process(hn, Vsample, x_EF, SECO=None, VL_conversion=False, kh_conversion=False)
    
    # generate an EDC
    y_slice_min=peim.y_min
    y_slice_max=peim.y_max
    peim.generate_an_edc(peim.z, peim.y, y_slice_min, y_slice_max)
    plt.plot(peim.x, peim.z_edc)
    plt.show()

    # edc stack
    # y_step_edcs=2 # n (degree) or n (mm) 刻み
    # z_offset_edcs=500 # EDCs stackの強度offset
    # peim.generate_edcs_stack(y_step_edcs, z_offset_edcs)
    # for i in range(len(peim.z_edcs)):
    #     plt.plot(peim.x, peim.z_edcs[i]+z_offset_edcs*i)
    # plt.show()
    """

class IgorPro_Image(MBS_A1):

    def load_data(self):
        self._initialize_variables()
        
        x_max_old = None
        x_min_old = None

        for k, path in enumerate(self.path_lst):
            # file読み込み、および、測定条件抽出
            print(f'Load File: {path}')
            self._read_file(path)
            self._extract_measurement_conditions()
            # 強度データを抽出
            data_ = self._extract_intensity_data()

            data = np.array(data_)

            self.z_paths.append(data)
            self.x_paths.append(self.x)

            # z_ = self._normalize_raw_z_data(data)
            self._append_data(data)

            if k == 0:
                x_min_old = copy.deepcopy(self.x_min)
                x_max_old = copy.deepcopy(self.x_max)
            else:
                # エネルギー範囲が異なる場合は積算不可 (point数が等しくても範囲が異なると意味がない)
                if x_min_old != self.x_min or x_max_old != self.x_max:
                    self.z_sekisan_flag = False
                    print(f"{self.filename_lst[k]}のエネルギー範囲が異なるため平均化処理できませんでした。")
                x_min_old = copy.deepcopy(self.x_min)
                x_max_old = copy.deepcopy(self.x_max)
        
        # 積算可能化どうかでファイル名が決定される
        if self.z_sekisan_flag is False:
            self.filename=self.filename_lst[-1]
        else:
            self.filename = self._create_filename(self.filename_lst)

        # 強度の規格化
        # 今回は積算平均化は行わない。複数のpathを読み込んだときにpath数で平均化する
        self._finalize_z_image()

        self.x_offseted = copy.deepcopy(self.x)
        self.y_offseted = copy.deepcopy(self.y)


    def _read_file(self, path):
        with open(path, encoding='utf-8', errors='replace') as f:
            # 改行だけ削る（タブは絶対に消さない）
            self.l = [s.rstrip('\n').rstrip('\r') for s in f.readlines()]
        # print("1行目", repr(self.l[3]))
        # print("99行目", repr(self.l[100]))
        # print("3行目", self.l[2])
        # print("4行目", self.l[3])
    
    def _extract_measurement_conditions(self):
        
        self.Epass = None
        self.x_label = 'Kinetic Energy (eV)'
        self.y_label = r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$"
        self.y_label_initial = r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$"
        self.z_label = 'Intensity (counts)'


        self.x = np.array(self.l[1].split('\t')[1:], dtype=float)
        # print('x:', self.x)
        self.x_min = np.amin(self.x)
        self.x_max = np.amax(self.x)
        self.x_step = abs(np.round(float(self.x[0])-float(self.x[1]), ORDER_X))

    def _extract_intensity_data(self, data_index='DATA:'):
        data = []
        self.y = []
        self.labels = []
        index=2
            
        for i in range(index + 1, len(self.l) - index):
            # タブ区切り（空要素を保持）
            row = self.l[i].rstrip('\n').split('\t')

            # 空要素 → 0、数値化
            for j, v in enumerate(row):
                if v == '' or v.isspace():
                    row[j] = 0.0
                else:
                    try:
                        row[j] = float(v)
                    except ValueError:
                        row[j] = 0.0

            # 1列目 → y
            nx = len(self.x)
            if row[1:]==[]:
                # --- ケース1: row が空（完全に空行） ---
                data.append([0.0] * nx)
            else:
                # 2列目以降 → intensity（行ごと）
                data.append(row[1:])
            
            self.y.append(row[0])

            # print('line:', len(data[-1]))
        
        self.y = np.array(self.y, dtype=float)
        # print("y:", self.y)
        self.y_min = np.amin(self.y)
        self.y_max = np.amax(self.y)
        self.y_step = abs(np.round(float(self.y[0])-float(self.y[1]), ORDER_Y))
        
        # print(data[0][:10])
        # print(data[50][:10])
        return data


    def _append_data(self, z_):
        if self.x_label == "Binding Energy (eV)":
            self.EF_paths.append(self.EF)
        else:
            self.x_paths.append(self.x)

        if self.z is None:
            self.z = copy.deepcopy(z_)
        else:
            try:
                self.z += z_
            except:
                self.z_sekisan_flag = False
                print("積算失敗：データ点数が一致していません")

    def _finalize_z_image(self):
        if self.z_sekisan_flag:
            self.z /= len(self.path_lst)
            
        else: # 積算できないときは最後に読み込んだデータを表示させる
            self.z = self.z_paths[-1]
    
if __name__ == "__main__":
    main()