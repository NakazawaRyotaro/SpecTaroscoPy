import copy
import numpy as np
import re
from scipy.interpolate import griddata
from pathlib import Path
from scipy.signal import argrelmax, argrelmin

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from RyoPy.PlotControl import ImagePlotControl, PlotControl
import RyoPy.defs_for_analysis as rpa

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
    # main_image_analysis()
    main_second_derivative()

def main_second_derivative():
    # インスタンス作製
    peim=MBS_A1(plt_show=False)
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
    peim=MBS_A1(plt_show=False) #photoemission intensity map
    peim_pltcntrl=ImagePlotControl(peim.x, peim.y, peim.z, 
                            title="Photoemission Intensity Map", 
                            x_label=peim.x_label, y_label=peim.y_label, z_label=peim.z_label)

    # Ek -> EB
    hn=21.22
    x_EF=16.99
    Vsample=0
    peim.convert_axis_in_one_photon_process(hn, Vsample, x_EF, SECO=None, VL_conversion=False, kh_conversion=False)
    
    # generate an EDC
    y_slice_min=peim.y_min
    y_slice_max=peim.y_max
    peim.generate_an_edc(peim.z, peim.y, y_slice_min, y_slice_max)
    # plt.plot(peim.x, peim.z_edc)
    # plt.show()
    peim.save_edc_flow(mode="Ek")

    # edc stack
    # y_step_edcs=2 # n (degree) or n (mm) 刻み
    # z_offset_edcs=500 # EDCs stackの強度offset
    # peim.generate_edcs_stack(y_step_edcs, z_offset_edcs)
    # for i in range(len(peim.z_edcs)):
    #     plt.plot(peim.x, peim.z_edcs[i]+z_offset_edcs*i)
    # plt.show()


class MBS_A1:
    def __init__(self, path=None, filename=None, idir=None, plt_show=False):
        # 初期化
        self.z_sekisan_flag=True
        self.path=path # defaultではpath/filenameは入力せず選ぶ
        self.filename=filename
        self.path_lst=None
        self.filename_lst=None
        self.x_offseted=None
        self.x_offset=0
        self.EF=None
        self.EF_offseted=None
        self.x_EF=None
        self.VL=None
        self.VL_offseted=None
        self.hn=None
        self.SECO=None
        self.WF=None
        self.y_offseted=None
        self.y_offset=0
        self.kh=None
        self.kh_offseted=None
        self.Vsample=0
        self.z = None
        self.z_paths = []

        self.z_edc=None
        self.z_edcs=[]
        self.z_ydc=None
        self.y_step_edcs=None
        self.y_slice_center_edcs=[]
        self.y_slice_min=None
        self.y_slice_max=None
        self.y_slice_center=None
        self.z_edc_offseted=None
        self.z_edc_offset=0
        self.z_offset_edcs_lst=[]

        self.x_slice_min=None
        self.x_slice_max=None
        self.x_slice_center=None
        self.z_ydc=None
        self.z_ydc_offseted=None
        self.z_ydc_offset=0
        self.z_ydcs=[]

        self.z_offset_ydcs=None
        self.labels=[]

        self.mcp_function=None
        self.filename_mcp_function=None

        # pathを取得する。
        if self.path==None: # pathとfilenameがNoneのとき、ポップアップからtextを選ぶ (default)
            self.path_lst, self.filename_lst = rpa.get_path(idir=str(idir)) # ポップアップが出てくるのでtextファイルを探す。
        
        # path生成
        self.path=self.path_lst[0]
        # data読み込み
        self.load_data()

    def load_data(self):
        self._initialize_variables()
        
        x_max_old = None
        x_min_old = None

        for k, path in enumerate(self.path_lst):
            print(f'Load File: {path}')
            self._read_file(path)
            self._extract_measurement_conditions()
            self._extract_measurement_conditions_from_spectaro_data()

            data_ = self._parse_data_block()
            # print("data:", data_)

            data = np.array(data_).T # dataの行列を転置する。

            if "[SpecTaroscoPy — PES image]" in self.l:
                z_ = self._handle_spectrum_analyzer_output(data)
            else:
                z_ = self._normalize_raw_z_data(data)

            z_ = np.nan_to_num(z_, nan=0)
            self._append_data(z_)

            if k == 0:
                x_min_old = copy.deepcopy(self.x_min)
                x_max_old = copy.deepcopy(self.x_max)
            else:
                if x_min_old != self.x_min or x_max_old != self.x_max:
                    self.z_sekisan_flag = False
                    print(f"{self.filename_lst[k]}のエネルギー範囲が異なるため平均化処理できませんでした。")
                x_min_old = copy.deepcopy(self.x_min)
                x_max_old = copy.deepcopy(self.x_max)

            print(max(z_[k][:]))
                
        if self.z_sekisan_flag is False:
            self.filename=self.filename_lst[-1]
        else:
            self.filename = self._create_filename(self.filename_lst)

        self._finalize_z_image()
        self._finalize_xy_labels()


    # filenameを作る関数 
    def _create_filename(self, lst):
        # ファイル名のパターンを正規表現で定義
        pattern = re.compile(r'([a-zA-Z0-9]+)(\d{5})_(\d+)\.txt')
        
        prefix = None
        min_measure_num = float('inf')
        max_measure_num = -float('inf')
        min_region = float('inf')
        max_region = -float('inf')

        for filename in lst:
            match = pattern.match(filename)
            if match:
                current_prefix, measure_num, region_num = match.groups()
                measure_num = int(measure_num)
                region_num = int(region_num)
                
                # プレフィックスを取得（ファイル名共通部分）
                if prefix is None:
                    prefix = current_prefix
                
                # 最小の測定番号と対応するregion番号を更新
                if measure_num < min_measure_num:
                    min_measure_num = measure_num
                    min_region = region_num
                elif measure_num == min_measure_num:
                    min_region = min(min_region, region_num)
                
                # 最大の測定番号と対応するregion番号を更新
                if measure_num > max_measure_num:
                    max_measure_num = measure_num
                    max_region = region_num
                elif measure_num == max_measure_num:
                    max_region = max(max_region, region_num)

        # 先頭の0を削除した測定番号
        min_measure_num_str = str(min_measure_num).lstrip('0')
        max_measure_num_str = str(max_measure_num).lstrip('0')
        

        # spectrum Analyzerで解析されたデータを入力した時の特殊処理
        if min_measure_num == float('inf') and max_measure_num == -float('inf'):
            return filename
            
        # 入力ファイルが一つか二つかで異なる出力を行う。
        elif len(lst)==1:
            return f"{prefix}_{min_measure_num_str}_{min_region}.txt"
        elif len(lst)>=2:
            # 結果をフォーマットして返す
            return f"{prefix}_{min_measure_num_str}_{min_region}_{max_measure_num_str}_{max_region}.txt"

    def _initialize_variables(self):
        self.z_sekisan_flag = True
        self.z = self.z_mcp = self.z_kh = self.z_edc = self.z_edc_offseted = self.z_edc_offset = None
        self.z_paths = []
        self.x_paths = self.x_offseted_paths = []
        self.EF_paths = self.EF_offseted_paths = []
        self.VL_paths = self.VL_offseted_paths = []
        self.z_kh_paths = []
        self.EF = self.EF_offseted = self.x_EF = self.VL = self.VL_offseted = None
        self.hn = self.SECO = self.WF = self.kh = self.kh_offseted = None
        self.Vsample = 0
        self.y_slice_min = self.y_slice_max = self.y_slice_center = None
        self.z_edcs = []
        self.y_step_edcs = None
        self.y_slice_center_edcs = []
        self.x_slice_min = self.x_slice_max = self.x_slice_center = None
        self.z_ydc = None
        self.z_ydcs = []
        self.z_offset_ydcs = 0
        self.x_step_edcs = None
        self.x_slice_center_edcs = []
        self.labels = []
        self.x_label = "X"
        self.y_label = "Y"
        self.frame=1000 # frameの初期値は1000に設定しておく。あとでzが1000で割られるため
        self.actscan=1
        self.mcp_function = None
        self.filename_mcp_function = None
        self.z_sg = None
        self.totalactscan = 0
        self.z_offset_edcs_lst=[]
        
    def _read_file(self, path):
        with open(path, encoding='utf-8', errors='replace') as f:
            self.l = [s.strip() for s in f.readlines()]

    def _extract_measurement_conditions(self):
        r = rpa.get_words_next_to_search_term

        self.lines, _ = r(self.l, "Lines")
        self.frame, _ = r(self.l, "Frames Per Step", words_for_failure=self.frame)
        self.frame = float(self.frame)/1000
        self.step_number, _ = r(self.l, "No. Steps")
        self.Epass, _ = r(self.l, "Pass Energy\t", mark="PE")
        self.lens, _ = r(self.l, "Lens Mode", type="str")
        self.region_number, _ = r(self.l, "RegNo")
        self.totsteps, _ = r(self.l, "Totsteps")
        self.add_fms, _ = r(self.l, "AddFMS")
        self.dithsteps, _ = r(self.l, "DithSteps")
        self.x_min, _ = r(self.l, "Start K.E.")
        self.x_step, _ = r(self.l, "Step Size")
        self.x_max, _ = r(self.l, "End K.E.")
        self.spinoffs, _ = r(self.l, "SpinOffs")
        self.x_width, _ = r(self.l, "Width")
        self.x_center, _ = r(self.l, "Center K.E.")
        self.x_first, _ = r(self.l, "FirstEnergy")
        self.deflx, _ = r(self.l, "DeflX")
        self.defly, _ = r(self.l, "DeflY")
        self.dbl10, _ = r(self.l, "Dbl10")
        self.AcqMode, _ = r(self.l, "Swept", type="str")
        self.numbername, _ = r(self.l, "Number Name", type="str")
        self.localdetector, _ = r(self.l, "Local Detector", type="str")
        self.xtab_on, _ = r(self.l, "XTAB ON", type="str")
        self.spin, _ = r(self.l, "Spinn", type="str")
        self.sx, _ = r(self.l, "SX")
        self.ex, _ = r(self.l, "EX")
        self.sy, _ = r(self.l, "SY")
        self.nos, _ = r(self.l, "NoS")
        self.endy, _ = r(self.l, "EndY")
        self.discr, _ = r(self.l, "Discr")
        self.adcmask, _ = r(self.l, "ADCMask")
        self.pcnttype, _ = r(self.l, "PCntType")
        self.softbinx, _ = r(self.l, "SoftBinX")
        self.adcoffset, _ = r(self.l, "ADCOffset")
        self.oradon, _ = r(self.l, "ORadON?")
        self.pcnton, _ = r(self.l, "PCntON?")
        self.region_name, _ = r(self.l, "RegName", type="str")
        self.name_string, _ = r(self.l, "NameString", type="str")
        self.time_start, _ = r(self.l, "Stim")
        self.sxscalemult, _ = r(self.l, "SuScaleMult")
        self.y2_max, _ = r(self.l, "SXScaleMax")
        self.y2_min, _ = r(self.l, "SXScaleMin")
        self.y2_label, _ = r(self.l, "SXScaleName", type="str")
        self.s0scalemult, _ = r(self.l, "S0ScaleMult")
        self.s0scalemax, _ = r(self.l, "S0ScaleMax")
        self.s0scalemin, _ = r(self.l, "S0ScaleMin")
        self.y2_label, _ = r(self.l, "XMapScaleName", type="str")
        self.y_label_for_deflectormap, _ = r(self.l, "YMapScaleName", type="str")
        self.time_end, _ = r(self.l, "TIMESTAMP:", type="str")
        self.x_label, _ = r(self.l, "EScaleName", type="str", words_for_failure=self.x_label)

    def _extract_measurement_conditions_from_spectaro_data(self):
        r = rpa.get_words_next_to_search_term
        if "[SpecTaroscoPy — PES image]" in self.l or "[Spectrum Analyzer]" in self.l:
            self.y_label, _ = r(self.l, "Y Label", type="str", words_for_failure=self.y_label)
            self.x_label, _ = r(self.l, "X Label", type="str", words_for_failure=self.x_label)
            self.y_min, _ = r(self.l, "Y Min")
            self.y_max, _ = r(self.l, "Y Max")
            self.y_step, _ = r(self.l, "Y Step")
            self.actscan, _ = r(self.l, "Total Actual Scans", words_for_failure=self.actscan)
        else:
            self.y_label, _ = r(self.l, "ScaleName", type="str", words_for_failure=self.y_label)
            if self.y_label == "Position(mm)":
                self.y_label = "Position (mm)"
            elif self.y_label in ["Angle(Degrees)", "Y Angle(Degrees)"]:
                self.y_label = "Angle (Degrees)"
            self.y_min, _ = r(self.l, "ScaleMin")
            self.y_max, _ = r(self.l, "ScaleMax")
            self.y_step, _ = r(self.l, "ScaleMult")
            self.actscan, _ = r(self.l, "ActScans", words_for_failure=self.actscan)
        self.totalactscan += int(self.actscan)

    def _parse_data_block(self):
        data = []
        self.labels = []
        try:
            index=self.l.index('DATA:')
        except ValueError:
            index=0
            
        for i in range(1, len(self.l) - index):
            row = self.l[index + i].split()
            label_flag = False
            for j in range(len(row)):
                try:
                    row[j] = float(row[j])
                except ValueError:
                    if i == 1:
                        self.labels.append(row[j])
                        label_flag = True
                    else:
                        row[j] = 0
            if not label_flag:
                data.append(row)
        # print(data)
        return data

    def _handle_spectrum_analyzer_output(self, z_):
        r = rpa.get_words_next_to_search_term
        self.x_label, _ = r(self.l, "X Label", type="str")

        if self.x_label == "Binding Energy (eV)":
            # if '--- EDC ---' in self.l or '--- EDCs Stacking ---' in self.l or '[EDCs Stacking]' in self.l or '[EDC]' in self.l:
            #     self.x = copy.deepcopy(z_[0])
            #     self.EF = copy.deepcopy(z_[1])
            #     z_ = copy.deepcopy(z_[2:])
            # else:
            self.EF = copy.deepcopy(z_[0])
        else:
            self.x = copy.deepcopy(z_[0])
        
        z_ = copy.deepcopy(z_[1:])
        
        if '--- EDCs Stacking ---' in self.l or '[EDCs Stacking]' in self.l:
            self.z_offset_edcs_lst, _=rpa.get_list_next_to_search_term(self.l, 'Z Offset EDCs')
            print(self.z_offset_edcs_lst)
        self.z_paths.append(z_)
        return z_

    def _normalize_raw_z_data(self, z_):
        if self.x_label == "Binding Energy (eV)":
            self.EF = copy.deepcopy(z_[0])
            self.EF_min=np.amin(self.EF)
            self.EF_max=np.amax(self.EF)
            self.EF_step=np.round(abs(self.EF[1]-self.EF[0]), ORDER_X)
        else:
            self.x = copy.deepcopy(z_[0])
            self.x_min=np.amin(self.x)
            self.x_max=np.amax(self.x)
            self.x_step=np.round(abs(self.x[1]-self.x[0]), ORDER_X)
        # print(self.actscan, self.frame)
        z_ = copy.deepcopy(z_[1:]) / self.frame 
        self.z_paths.append(z_/ self.actscan)  # EDC viewer用にact scanで割る
        return z_

    def _append_data(self, z_):
        if self.x_label == "Binding Energy (eV)":
            self.EF_paths.append(self.EF)
        else:
            self.x_paths.append(self.x)

        if self.z is None:
            self.z = copy.deepcopy(z_)
        else:
            if self.z_sekisan_flag:
                try:
                    self.z += z_
                except:
                    self.z_sekisan_flag = False
                    print("積算失敗：データ点数が一致していません")

    def _finalize_z_image(self):
        if "[SpecTaroscoPy — PES image]" not in self.l:
            if self.z_sekisan_flag:
                self.z /= self.totalactscan
            else: # 積算できないときは最後に読み込んだデータを表示させる
                self.z = self.z_paths[-1]
                # self.z /= len(self.path_lst)
        self.z_label = "Intensity (cps)"

    def _finalize_xy_labels(self):
        """
        x, y 軸および関連するオフセット付きデータの最終調整を行う。
        [EDCs stacking] がある場合は、Y座標をスライス中心値で置き換える。
        各軸は小数点8桁で丸め、必要に応じてオフセットも適用。
        """
        # EDCs stacking が有効なら、Y軸データをスライス中心値から取得
        if "--- EDCs Stacking ---" in self.l or '[EDCs Stacking]' in self.l:
            self.y_slice_center_edcs, _ = rpa.get_list_next_to_search_term(
                self.l, "Y Slice Center", type="float", inner_mark=" "
            )
            self.y = list(map(float, self.y_slice_center_edcs))
        else:
            # 通常は y_min, y_max と z 次元数から線形補間で Y 軸を生成
            if self.y_min!='' and self.y_max!='':
                self.y = np.round(np.linspace(self.y_min, self.y_max, len(self.z[:])), ORDER_Y)
            else:
                self.y_min = 0 
                self.y_max = float(len(self.z[:]))
                self.y_step = 1
                self.y = np.round(np.arange(self.y_min, self.y_max-0.1, self.y_step), 1)


        # x 軸と EF を 8桁で丸める（可能な場合）
        try:
            self.x = np.round(self.x, 8)
            self.x_offseted = copy.deepcopy(self.x)
        except Exception:
            pass

        try:
            self.EF = np.round(self.EF, 8)
            self.EF_offseted = copy.deepcopy(self.EF)
        except Exception:
            pass

        # y オフセットの適用
        self.y_offseted = copy.deepcopy(self.y)
        if self.y_offset != 0:
            self.y = self.y_offseted - self.y_offset

        # x オフセットの適用
        self.x_offseted_paths = copy.deepcopy(self.x_paths)
        if self.x_offset != 0:
            self.x_paths = self.x_offseted_paths - self.x_offset

        self.y_label_initial = copy.deepcopy(self.y_label)


    def convert_axis_in_one_photon_process(self, hn, Vsample, x_EF, SECO=None, VL_conversion=False, kh_conversion=False):
        # パラメータ取得
        self.hn=hn
        self.Vsample=Vsample
        self.x_EF=x_EF
        self.SECO=SECO

        # EF基準Eb変換
        self.EF=np.round(-1*(self.x+self.Vsample-self.x_EF),8) # convert Ek to EB_EF
        self.EF_offseted=np.round(self.EF-self.x_offset, 8)
        # 入力データすべてに対しても。
        self.EF_paths=[]
        self.EF_offseted_paths=[]
        for i in range(len(self.x_paths)):
            self.EF_paths.append(np.round(-1*(self.x_paths[i]+self.Vsample-self.x_EF),8))
            self.EF_offseted_paths.append(np.round(self.EF_paths[i]-self.x_offset,8))
        # label名変更
        self.x_label="Binding Energy (eV)"
        
        # 真空準位基準Eb変換
        if VL_conversion:
            self.WF=self.SECO-self.Vsample-(self.x_EF-self.hn) # V印加したときのSECO
            self.VL=np.round(self.EF+self.WF,8) # convert EB_EF to EB_VL
            self.VL_offseted=np.round(self.EF_offseted+self.WF,8) # convert EB_EF to EB_VL
            # 入力データすべてに対しても。
            self.VL_paths=[]
            self.VL_offseted_paths=[]
            for i in range(len(self.x_paths)):
                self.VL_paths.append(np.round(self.EF_paths[i]+self.WF,8))
                self.VL_offseted_paths.append(np.round(self.EF_offseted_paths[i]+self.WF,8))

        # y軸の変換
        if kh_conversion==True and self.y_label!="Position (mm)":
            kh_2d=[]
            kh_2d_offseted=[]
            x_2d=[]
            x_2d_offseted=[]
            # EF_2d=[]
            # VL_2d=[]
            for i in range(len(self.y_offseted)):
                kh_2d.append([0.5123*np.sqrt(self.x[j]+self.Vsample)*np.sin(np.radians(self.y[i])) for j in range(len(self.x))])
                # kh_2d=np.round(np.array(kh_2d),8)
                kh_2d_offseted.append([0.5123*np.sqrt(self.x[j]+self.Vsample)*np.sin(np.radians(self.y_offseted[i])) for j in range(len(self.x))])
                # kh_2d_offseted=np.round(np.array(kh_2d_offseted),8)
                x_2d.append(self.x)
                x_2d_offseted.append(self.x_offseted)
                # EF_2d.append(self.EF)
                # VL_2d.append(self.VL)
            # 等間隔なkhリストを作成
            self.kh=np.round(np.linspace(np.amin(kh_2d), np.amax(kh_2d), len(self.y)), 6)
            self.kh_offseted=np.round(np.linspace(np.amin(kh_2d_offseted), np.amax(kh_2d_offseted), len(self.y_offseted)), 6)
            self.kh_step=np.round(abs(self.kh[0]-self.kh[1]), 6)
            # grid作成
            x_grid, y_grid = np.meshgrid(self.x, self.kh)
            x_grid_offseted, y_grid_offseted = np.meshgrid(self.x_offseted, self.kh_offseted)
            # x_offseted_2d, y_offseted_2d を1次元にフラット化
            points = np.array([(x, y) for x_row, y_row in zip(x_2d, kh_2d) for x, y in zip(x_row, y_row)])
            points_offseted = np.array([(x, y) for x_row, y_row in zip(x_2d_offseted, kh_2d_offseted) for x, y in zip(x_row, y_row)])
            # z画像を補完
            z_values = self.z.flatten()
            self.z_kh=griddata(points, z_values, 
                               (x_grid, y_grid), 
                               method='linear', fill_value=0) #np.nan)
            self.z_kh_offseted=griddata(points_offseted, z_values, 
                                        (x_grid_offseted, y_grid_offseted), 
                                        method='linear', fill_value=0) #np.nan)
            # z_pathsを補完
            self.z_kh_paths=[]
            for i in range(len(self.z_paths)):
                z_paths_values = self.z_paths[i].flatten()
                self.z_kh_paths.append(griddata(points, z_paths_values, (x_grid, y_grid), method='linear', fill_value=0)) #np.nan)
            # z更新
            self.y_label = r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$"
        else:
            self.z_kh = None
            self.kn = None
            self.kh_offseted = None
            self.kh_step = None
            self.z_kh_paths = []
            self.y_label = copy.deepcopy(self.y_label_initial)

    def apply_offset(self, x_offset, y_offset, x_axis=None, y_axis=None):
        # Ek offset
        self.x_offset=x_offset
        self.x_offseted=self.x+self.x_offset
        self.x_offseted_paths=[]
        for i in range(len(self.x_paths)):
            self.x_offseted_paths.append(self.x_paths[i]+self.x_offset)
        
        if x_axis=="EB_EF":
            self.EF_offseted=self.EF-self.x_offset
            self.EF_offseted_paths=[]
            for i in range(len(self.x_offseted_paths)):
                self.EF_offseted_paths.append(self.EF_paths[i]-self.x_offset)
        
        elif x_axis=="EB_VL":
            self.EF_offseted=self.EF-self.x_offset # EFも一応
            self.VL_offseted=self.VL-self.x_offset
            self.EF_offseted_paths=[]
            self.VL_offseted_paths=[]
            for i in range(len(self.x_offseted_paths)):
                self.EF_offseted_paths.append(self.EF_paths[i]-self.x_offset)
                self.VL_offseted_paths.append(self.VL_paths[i]-self.x_offset)

        # Y offset
        if y_axis=="Deg":
            self.y_offset=y_offset
            self.y_offseted=np.round(self.y+self.y_offset, ORDER_Y)
            
    def generate_an_edc(self, z, y, y_slice_min, y_slice_max, mode="edc"):
        self.z_edc_offseted=None
        self.z_edc_offset=None
        """EDCを作成
        mode (str): edcのときEDCを一本作成。self.z_edcを出力。
                    edcsのとき、EDCs stackのためのEDCを作成する。self.z_edcは定義せず、リストをreturnする。
        """
        self.y_slice_min=y_slice_min
        self.y_slice_max=y_slice_max

        self.y_slice_center = np.round((self.y_slice_max+self.y_slice_min)/2, 4)
        # EDC作成
        # print(self.y_slice_min, self.y_slice_max)
        if mode=="edc":
            self.z_edc=np.sum(z[rpa.get_idx_of_the_nearest(y, self.y_slice_min): rpa.get_idx_of_the_nearest(y, self.y_slice_max)], axis=0)
            # self.z_edc_offseted=copy.deepcopy(self.z_edc) # offsetかける用
        elif mode=="return":
            return np.sum(z[rpa.get_idx_of_the_nearest(y, self.y_slice_min): rpa.get_idx_of_the_nearest(y, self.y_slice_max)], axis=0)

    def generate_a_ydc(self, z, x, x_slice_min, x_slice_max, mode="ydc"):
        self.z_ydc_offseted=None
        self.z_ydc_offset=None
        """EDCを作成
        mode (str): ydcのときYDCを一本作成。self.z_ydcを出力。
                    ydcsのとき、YDCs stackのためのEDCを作成する。self.y_edcは定義せず、リストをreturnする。
        """
        self.x_slice_min=x_slice_min
        self.x_slice_max=x_slice_max
        self.x_slice_center = np.round((self.x_slice_max+self.x_slice_min)/2, 4)
        z=z.T
        # EDC作成
        # print(self.y_slice_min, self.y_slice_max)
        if mode=="ydc":
            z_ydc=np.sum(z[rpa.get_idx_of_the_nearest(x, self.x_slice_min): rpa.get_idx_of_the_nearest(x, self.x_slice_max)], axis=0)
            self.z_ydc=z_ydc.T
            self.z_ydc_offseted=copy.deepcopy(self.z_ydc)
        elif mode=="ydcs":
            z_ydc=np.sum(z[rpa.get_idx_of_the_nearest(x, self.x_slice_min): rpa.get_idx_of_the_nearest(x, self.x_slice_max)], axis=0)
            return z_ydc.T
    
    def subtract_background_intensity(self, background_intensity, mode="EDC"):
        if mode=="EDC":
            self.z_edc_offset=background_intensity
            self.z_edc_offseted=self.z_edc-self.z_edc_offset
            # self.z_edc_offseted_=copy.deepcopy(self.z_edc_offseted)

    def generate_edcs_stack(self, y, y_step_edcs, z, mode="normal"):
        """
        EDCs stack作成
        y (list): 刻まれる軸
        y_step_edcs (float): 刻み幅 [pixcel数でなく、リストの値 (deg, mm) で記入]
        z (入れ子のリスト): 刻まれる画像のリスト
        """
        # 初期化
        self.z_edcs=[]
        self.y_slice_center_edcs=[]
        self.z_offset_edcs_lst=[]
        self.y_step_edcs=y_step_edcs
        
        idx_num=int(self.y_step_edcs/abs(y[0]-y[1])) # 切り出しEDC一本(unit)あたりのyのpixel数
        print("Yステップ(pixel数):", idx_num)
        if len(y)/idx_num >= 200:
            mode='None'
            
        if mode=="split_at_zero":
            if idx_num % 2 == 0: # unit内の要素数を奇数にする。
                idx_num+=1    
            # 切り出しEDCごとのyのidxリストを作成 (2次元の入れ子リスト)
            idxlst_y_slice_edcs=rpa.split_around_zero(y, idx_num)
            idxlst_y_slice_edcs=idxlst_y_slice_edcs[::-1]
            # EDCs stack作成
            for i in range(len(idxlst_y_slice_edcs)):
                z_edc_temp=self.generate_an_edc(self.z, y, y[idxlst_y_slice_edcs[i][0]], y[idxlst_y_slice_edcs[i][-1]], mode="return") # EDCの切り出し。EDCs stack mode (返り値が１次元リスト。インスタンス変数ではない)
                # self.z_offset_edcs_lst.append(i*z_offset_edcs)
                # z_edc_temp-=self.z_offset_edcs_lst[i] #edc1本ずつz_offsetを足していく。
                self.z_edcs.append(z_edc_temp) #EDCs stackリストにアペンド。
                y_slice_edcs_center_temp=np.round((y[idxlst_y_slice_edcs[i][0]] + y[idxlst_y_slice_edcs[i][-1]])/2, 5) # EDC切り出しのyの中心
                self.y_slice_center_edcs.append(y_slice_edcs_center_temp) # EDCs stackのlegend nameをリストに格納
        
        if mode=="normal":
            i=0 # offsetをかけるためのカウンター
            idx_min=-2
            idx_max=-2
            # print(len(y))
            # print(idx_num)
            while abs(idx_max)<len(y)-idx_num and abs(idx_min)<len(y)-idx_num:
                idx_max=int(idx_min+1)
                idx_min=int(idx_max-idx_num+1)
                self.y_slice_center_edcs.append(np.round((y[idx_min]+y[idx_max])/2, ORDER_Y)) # sliceのセンター
                # print(y[idx_start], y[idx_end])
                z_edc_temp=self.generate_an_edc(z, y, y[idx_min], y[idx_max], mode="return") # EDCの切り出し。EDCs stack mode (返り値が１次元リスト。インスタンス変数ではない)
                self.z_edcs.append(z_edc_temp) #EDCs stackリストにアペンド。
                i+=1
            # print(len(self.y_slice_center_edcs))
            # print(len(self.z_edcs))

    def save_data(self, filename, data_type, axis):
        # resultsというフォルダを作る
        foldername=f'STPy_{VERSION_NUMBER}_PESImage'
        foldername = foldername.replace('.', '_')
        # print(foldername)
        rpa.create_folder_at_current_path(self.path, foldername)
        
        # filename作成
        filename=filename.replace(".txt","") # ファイル名から拡張子を除いたものがlabel名となる
        if axis=="Ek":
            filename_new=filename+"_Ek"
        elif axis=="EF":
            filename_new=filename+"_EF"
        elif axis=="VL":
            filename_new=filename+"_VL"

        # fileのパスを作成
        directory_path = os.path.dirname(self.path) # ディレクトリパスを取得
        savefile_path = directory_path+f"/{foldername}/{filename_new}.txt"

        # save data (fileの書き込みと保存)
        self.write_data(savefile_path, filename, data_type, axis)


    def write_data(self, savefile_path, label, data_type, axis):
        def write():
            # DATA: 以降の行を取得
            try:
                index=self.l.index('DATA:')
            except ValueError:
                index=1
            data_index = index + 1

            # 追加するヘッダー
            added_header=[]
            added_header.append('')  # 空行
            added_header.append("[SpecTaroscoPy — PES image]")
            added_header.append("Author\tR Nakazawa")
            added_header.append("Contact\tnakazawa@ims.ac.jp")
            added_header.append(f"Version\t{VERSION_NUMBER}")
            added_header.append("--- Info ---")
            added_header.append(f"User\t{user}")
            added_header.append("Load File Path\t" + '\t'.join(map(str, self.path_lst)))
            added_header.append(f"Save File Path\t{savefile_path}")
            added_header.append(f"Total Actual Scans\t{self.totalactscan}")
            if axis=="EF":
                added_header.append(f"X Label\tBinding Energy (eV)")
            elif axis=="Ek":
                added_header.append(f"X Label\tKinetic Energy (eV)")
            elif axis=="VL":
                added_header.append(f"X Label\tBinding Energy (eV)")
            
            added_header.append(f"Y Label\t{self.y_label}")
            added_header.append(f"Z Label\t{self.z_label}")
            if axis=="EF":
                added_header.append(f"X Min\t{np.amin(self.EF_offseted)}")
                added_header.append(f"X Max\t{np.amax(self.EF_offseted)}")
            elif axis=="VL":
                added_header.append(f"X Min\t{np.amin(self.VL_offseted)}")
                added_header.append(f"X Max\t{np.amax(self.VL_offseted)}")
            elif axis=='Ek':
                added_header.append(f"X Min\t{np.amin(self.x_offseted)}")
                added_header.append(f"X Max\t{np.amax(self.x_offseted)}")
            added_header.append(f'X Step\t{self.x_step}')
            added_header.append(f"Ek Offset\t{self.x_offset}")
            if self.kh is not None:
                added_header.append(f"Y Min\t{np.amin(self.kh_offseted)}")
                added_header.append(f"Y Max\t{np.amax(self.kh_offseted)}")
                added_header.append(f"Y Step\t{self.kh_step}")
            else:
                added_header.append(f"Y Min\t{np.amin(self.y_offseted)}")
                added_header.append(f"Y Max\t{np.amax(self.y_offseted)}")
                added_header.append(f"Y Step\t{self.y_step}")
            added_header.append(f"Ang or Posi Offset\t{self.y_offset}")
            added_header.append(f"MCP Function Path\t{self.filename_mcp_function}")
            added_header.append("--- Axis Conversion ---") # 軸変換
            added_header.append(f"Photon Energy\t{self.hn}")
            added_header.append(f"Applied Voltage\t{self.Vsample}")
            added_header.append(f"kinetic Energy at Fermi Level\t{self.x_EF}")
            added_header.append(f"Secondary Electron Cutoff\t{self.SECO}")

            if data_type=='edc':
                added_header.append("--- EDC ---") # EDC/YDC
                added_header.append(f"Y Min Slice\t{self.y_slice_min}")
                added_header.append(f"Y Max Slice\t{self.y_slice_max}")
                added_header.append(f"Y Slice Center\t{self.y_slice_center}")
                added_header.append(f"Background Intensity of EDC\t {self.z_edc_offset}")
            elif data_type=='ydc':
                added_header.append("--- YDC ---") # EDC/YDC
                added_header.append(f"Start X Slice\t{self.x_slice_min}")
                added_header.append(f"End X Slice\t{self.x_slice_max}")
                added_header.append(f"X Slice Center List\t{self.x_slice_center}")
            elif data_type=='edcs':
                added_header.append("--- EDCs Stacking ---")
                added_header.append("Y Slice Center\t" + ' '.join(map(str, self.y_slice_center_edcs)))
                added_header.append("Z Offset EDCs\t" + ' '.join(map(str, self.z_offset_edcs_lst)))

            added_header.append(' ')
            added_header.append("DATA:")

            ################################
            # data 作成
            # 新しいデータのリストを作成
            intensity_data = []

            # Xのリスト作成
            if axis=="Ek":
                x=self.x_offseted
            elif axis=="EF":
                x=self.EF_offseted
            elif axis=="VL":
                x=self.VL_offseted

            # image型の場合
            if data_type=='image':
                # intensityは2通り(Ang/Posi or k//)
                if self.kh is not None:
                    z=self.z_kh_offseted
                else:
                    z=self.z

                # EFに置き換えたxの値を先頭に追加して、対応するzの値と一緒に書き換え
                for x_value, z_values in zip(x, z.T):  # zは転置して対応
                    intensity_data.append(f"{x_value:.10f}\t" + "\t".join(f"{z:.10f}" for z in z_values))            


            if data_type=='ydc':
                x=self.y # edc_dataに収納する横軸
                z=self.z_ydc # edc_dataに収納する縦軸
                z_bg=self.z_ydc_offseted # edc_dataに収納する縦軸
                # label情報
                if self.y_label=="Position (mm)":
                    x_label=f"Pos_{label}"
                elif self.y_label=="Angle (Degrees)":
                    x_label=f"Deg_{label}"
                elif self.y_label==r"$k_{//} \ \mathrm{(\AA)}$":
                    x_label=f"kh_{label}"


            # 強度label, 強度データ決定
            # EDC, YDC共通
            elif data_type=='edc' or data_type=='edcs':
                # X label
                if axis=="Ek":
                    x_label=f"Ek_{label}"
                elif axis=="EF":
                    x_label=f"EF_{label}"
                elif axis=="VL":
                    x_label=f"VL_{label}"

                # 強度データ EDC
                if data_type=='edc':
                    z=self.z_edc
                    z_bg=self.z_edc_offseted

            if data_type=='edc' or data_type=='ydc':
                # Z offsetかけるとそれをラベルに追加する。
                if z_bg is not None:
                    added_header.append(f"{x_label}\t{label}\t{label}_bg")
                else:
                    added_header.append(f"{x_label}\t{label}")
                
                # EDC spectrum data
                if z_bg is not None: # offsetかけた場合
                    for i in range(len(x)): 
                        if z[i]==0:
                            if z_bg[i]==0:
                                intensity_data.append(f"{x[i]}\tnan\tnan")
                            else:
                                intensity_data.append(f"{x[i]}\tnan\t{z_bg[i]}")
                        else:
                            intensity_data.append(f"{x[i]}\t{z[i]}\t{z_bg[i]}")           
                else: # offsetかけてない場合
                    for i in range(len(x)): 
                        if z[i]==0:
                            intensity_data.append(f"{x[i]}\tnan")
                        else:
                            intensity_data.append(f"{x[i]}\t{z[i]}")
                
            # 強度データ EDCs
            elif data_type=='edcs':                        
                # label
                legend_lst = [f"{x_label}"]
                for i in range(len(self.y_slice_center_edcs)):
                    legend_lst.append(f"{label}_{np.round(self.y_slice_center_edcs[i], 3)}")
                # y_legend_lstを適切にフォーマットして文字列に変換
                added_header.append("\t".join(legend_lst))
                
                # data
                for i in range(len(x)):
                    data_lst = [f"{x[i]}"]
                    for j in range(len(self.y_slice_center_edcs)):
                        data_lst.append(f"{self.z_edcs[j][i]}")
                    # data_lstを適切にフォーマットして文字列に変換
                    intensity_data.append("\t".join(data_lst))

            # 元のファイルのヘッダー部分と書き換えたデータ部分を結合
            output_lines = self.l[:data_index-2] + added_header + intensity_data

            #################################
            # 出力用ファイルに書き込み
            with open(savefile_path, 'w', encoding='utf-8', errors='replace') as f:
                for line in output_lines:
                    try:
                        f.write(line + '\n')
                    except Exception as e:
                        print(f"Error writing line to file: {e}")
                        print(f"Line content: {line}")

        # save
        if not os.path.isfile(savefile_path): # saveファイルが重複しない場合はsave
            write()
            print("Data was saved.")
        else: # saveファイルが存在する場合、上書きするか確認する
            overwrite = rpa.ask_me("Confirmation of save", "Do you want to overwrite existing file? (y/n)") # popup
            if overwrite == 'y': # yesを選択すればsave
                write()
            else: # noを選択すれば保存しない
                print('Aborted.')     


    def smooth_image_SG(self, z_lst, order, point, iteration):
        """スムージングを行う。返り値は入力したz_lstと同じ次元のリスト"""
        # 初期化
        z_num=len(z_lst)
        # # print(z_num)
        # if z_num == 1: # zが一つのEDCのときエラーが起こるため回避。
        #     z_sg=[copy.deepcopy(z)]
        # else:
        # print(z_lst)
        z_sg_lst=copy.deepcopy(z_lst)
        # yのピクセルごとにサビツキゴーレイ法を実施していく
        for i in range(z_num):
            z_sg_lst[i]= rpa.smooth_spectrum_by_SG(z_lst[i], order, point, iteration)
        return z_sg_lst

    def calculate_RMSE(self, y1_lst, y2_lst):
        pass

    def smooth_image_binomial(self, z, step, order, iteration):
        binomial_function=rpa.binomial_function(order, step=step)
        iteration=int(iteration)
        z_binomial=[]
        for i in range(len(z)):
            z_binomial_=copy.deepcopy(z[i])
            for j in range(iteration):
                z_binomial_=rpa.conv(z_binomial_, binomial_function, step)
            z_binomial.append(z_binomial_)
        return np.array(z_binomial)

    def second_derivative(self, z, axis, return_first_derivative=False):
        """
        入れ子のリストで二次微分を行う関数。

        Parameters:
        - z: 入れ子リスト。光電子放出強度マップ（エネルギーと角度の値）。
        - axis: 微分を行う軸。0はx(エネルギー)方向、1はy方向。
        - first derivative: bool値。一次微分「も」出力させるときTrue。
        Returns:
        - 二次微分された同じ大きさの入れ子リスト。ただしfirst derivativeがTrueのときは二次・一次微分どちらも返す。
        """
        # numpy配列に変換（計算のため）
        z_array = np.array(z)

        if axis == 1:
            z_array = z_array.T

        # 二次微分を計算
        first_derivative_array = copy.deepcopy(z_array)
        second_derivative_array = copy.deepcopy(z_array)

        # まず一次微分を計算
        for i in range(len(z_array)):
            first_derivative_array[i] = np.gradient(z_array[i])

        # 次に一次微分の差分を取って二次微分
        for i in range(len(z_array)):
            second_derivative_array[i] = np.gradient(first_derivative_array[i])

        # 軸の変更を元に戻す
        if axis == 1:
            z_array = z_array.T
            second_derivative_array = second_derivative_array.T
            first_derivative_array = first_derivative_array.T

        # 結果を返す
        if return_first_derivative:  # ブール値として判定
            return second_derivative_array, first_derivative_array
        else:
            return second_derivative_array

    def curvature_analysis(self, z, axis, a0, cy=None, dimention=1):
        second_derivative, first_derivative = self.second_derivative(z, axis, return_first_derivative=True)
        
        abs_first_derivative_max=0
        first_derivative_min = np.amin(first_derivative)
        first_derivative_max = np.amax(first_derivative)
        if abs(first_derivative_min)>=abs(first_derivative_max):
            abs_first_derivative_max=abs(first_derivative_min)
        else:
            abs_first_derivative_max=abs(first_derivative_max)
        sq_abs_first_derivative_max=(abs_first_derivative_max)
        c0=sq_abs_first_derivative_max*a0
        
        if dimention==1:
            curvature = second_derivative/((c0+first_derivative**(2))**(2/3))
        return curvature
    

    def detect_peaks_in_nested_list(self, x, nested_list, order=5, negative_peak=True, another_list=None):
        """
        入れ子リスト内の各データ（y）に対して局所的な最大値（ピーク）を検出する。

        Parameters:
            nested_data (list of list): 入れ子のデータリスト。
            order (int): ピークを検出する際の局所的比較範囲。
            negative_peak (bool): 負ピークを検出するか、正ピークを検出するか。
            another_list (list of list): 入れ子の別のデータリスト。
        Returns:
            peak_x_list (list of list): 各スペクトルの局所的な最大値のインデックスを格納したリスト。
            peak_z_list (list of list): 各スペクトルの局所的な最大値の強度を格納したリスト。
            peak_another_z_list (list of list): peak_x_listに対応する別リストの強度を格納したリスト。
        """
        order = int(order)
        peak_x_list = []
        peak_z_list = []
        peak_another_z_list = []

        for i in range(len(nested_list)):
            # 局所的な最大(小)値のインデックスを取得
            if not negative_peak:
                peak_indices = argrelmax(nested_list[i], order=order)[0]
            else:
                peak_indices = argrelmin(nested_list[i], order=order)[0]

            # 最大値の強度（値）を取得
            peak_x = list(x[peak_indices])  # リスト化
            peak_z = list(nested_list[i][peak_indices])  # リスト化
            
            # 結果をリストに格納
            peak_x_list.append(peak_x)
            peak_z_list.append(peak_z)
            
            # 他のリストで対応する強度をピックアップ
            if another_list is not None:
                peak_another_z = list(another_list[i][peak_indices])  # リスト化
                peak_another_z_list.append(peak_another_z)

        return peak_x_list, peak_z_list, peak_another_z_list



if __name__ == "__main__":
    # pass
    main()