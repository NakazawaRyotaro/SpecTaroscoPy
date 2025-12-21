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
    peim=SCIENTA_DA30(plt_show=False) #photoemission intensity map
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
    plt.plot(peim.x, peim.z_edc)
    plt.show()

    # edc stack
    # y_step_edcs=2 # n (degree) or n (mm) 刻み
    # z_offset_edcs=500 # EDCs stackの強度offset
    # peim.generate_edcs_stack(y_step_edcs, z_offset_edcs)
    # for i in range(len(peim.z_edcs)):
    #     plt.plot(peim.x, peim.z_edcs[i]+z_offset_edcs*i)
    # plt.show()


class SCIENTA_DA30(MBS_A1):

    def _extract_measurement_conditions(self):
        r = rpa.get_words_next_to_search_term

        # self.line, _ = r(self.l, "Lines")
        self.frame, has_frame = r(self.l, "Step Time", words_for_failure=self.frame, mark="=")
        # if has_frame:
        #     self.frame, has_frame = r(self.l, "Step Time", words_for_failure=self.frame, mark="=")
        self.frame = float(self.frame)/1000
        self.Epass, _ = r(self.l, "Pass Energy", mark="=")
        self.lens, _ = r(self.l, "Lens Mode", type="str", mark="=")
        self.x_min, _ = r(self.l, "Low Energy", mark="=")
        self.x_step, _ = r(self.l, "Energy Step", mark="=")
        self.x_max, _ = r(self.l, "High Energy", mark="=")
        self.x_center, _ = r(self.l, "Center Energy", mark="=")

        # self.step_number, _ = r(self.l, "No. Steps")
        # self.region_number, _ = r(self.l, "RegNo")
        # self.totsteps, _ = r(self.l, "Totsteps")
        # self.add_fms, _ = r(self.l, "AddFMS")
        # self.dithsteps, _ = r(self.l, "DithSteps")

        # self.spinoffs, _ = r(self.l, "SpinOffs")
        # self.x_width, _ = r(self.l, "Width")
        # self.x_first, _ = r(self.l, "FirstEnergy")
        # self.deflx, _ = r(self.l, "DeflX")
        # self.defly, _ = r(self.l, "DeflY")
        # self.dbl10, _ = r(self.l, "Dbl10")
        # self.AcqMode, _ = r(self.l, "Swept", type="str")
        # self.numbername, _ = r(self.l, "Number Name", type="str")
        # self.localdetector, _ = r(self.l, "Local Detector", type="str")
        # self.xtab_on, _ = r(self.l, "XTAB ON", type="str")
        # self.spin, _ = r(self.l, "Spinn", type="str")
        # self.sx, _ = r(self.l, "SX")
        # self.ex, _ = r(self.l, "EX")
        # self.sy, _ = r(self.l, "SY")
        # self.nos, _ = r(self.l, "NoS")
        # self.endy, _ = r(self.l, "EndY")
        # self.discr, _ = r(self.l, "Discr")
        # self.adcmask, _ = r(self.l, "ADCMask")
        # self.pcnttype, _ = r(self.l, "PCntType")
        # self.softbinx, _ = r(self.l, "SoftBinX")
        # self.adcoffset, _ = r(self.l, "ADCOffset")
        # self.oradon, _ = r(self.l, "ORadON?")
        # self.pcnton, _ = r(self.l, "PCntON?")
        # self.region_name, _ = r(self.l, "RegName", type="str")
        # self.name_string, _ = r(self.l, "NameString", type="str")
        # self.time_start, _ = r(self.l, "Stim")
        # self.sxscalemult, _ = r(self.l, "SuScaleMult")
        # self.y2_max, _ = r(self.l, "SXScaleMax")
        # self.y2_min, _ = r(self.l, "SXScaleMin")
        # self.y2_label, _ = r(self.l, "SXScaleName", type="str")
        # self.s0scalemult, _ = r(self.l, "S0ScaleMult")
        # self.s0scalemax, _ = r(self.l, "S0ScaleMax")
        # self.s0scalemin, _ = r(self.l, "S0ScaleMin")
        # self.y2_label, _ = r(self.l, "XMapScaleName", type="str")
        # self.y_label_for_deflectormap, _ = r(self.l, "YMapScaleName", type="str")
        # self.time_end, _ = r(self.l, "Time", type="str")

        self.x_label, _ = r(self.l, "Dimension 1 name", type="str", words_for_failure=self.x_label, mark="=")
        if self.x_label == 'Kinetic Energy [eV]':
            self.x_label = 'Kinetic Energy (eV)'


    def _extract_measurement_conditions_from_spectaro_data(self):
        # DA30用
        r = rpa.get_words_next_to_search_term
        # if "[SpecTaroscoPy — PES image]" in self.l or "[Spectrum Analyzer]" in self.l:
        #     self.y_label, _ = r(self.l, "Y Label", type="str", words_for_failure=self.y_label)
        #     self.x_label, _ = r(self.l, "X Label", type="str", words_for_failure=self.x_label)
        #     self.y_min, _ = r(self.l, "Y Min")
        #     self.y_max, _ = r(self.l, "Y Max")
        #     self.y_step, _ = r(self.l, "Y Step")
        #     self.actscan, _ = r(self.l, "Total Actual Scans", words_for_failure=self.actscan)
        # else:
        if self.lens == "Transmission":
            self.y_label = "Position (mm)"
        else:
            self.y_label = "Angle (Degrees)"
        y_lst, _ =rpa.get_list_next_to_search_term(self.l, "Dimension 2 scale", mark="=", inner_mark=' ')
        # print('y_lst:', y_lst)
        self.y_min = np.amin(np.array(y_lst, dtype=float))
        self.y_max = np.amax(np.array(y_lst, dtype=float))
        self.y_step = abs(np.round(y_lst[0]-y_lst[1], 6))
        self.actscan, _ = r(self.l, "Number of Sweeps", words_for_failure=self.actscan, mark="=")
        self.totalactscan += int(self.actscan)


    def _extract_intensity_data(self, data_index='[Data 1]'):
        data = []
        self.labels = []
        try:
            index=self.l.index(data_index)
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
                if row != []: # 空行対策 (SCIENTA DA30のデータファイルに空行が含まれる場合があるのでその対策)
                    data.append(row)
        # print(data)
        return data # 改行対策

if __name__ == "__main__":
    main()