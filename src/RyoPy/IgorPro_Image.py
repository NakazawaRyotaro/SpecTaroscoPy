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
    """Read Igor Pro tab-delimited image exports.

    File layout: first line is a title; second line contains the horizontal
    coordinates after an empty first cell; subsequent lines contain a vertical
    coordinate followed by intensity values.

    SpecTaroScopy convention: x = energy (file's first column),
    y = momentum/angle (file's second line), z.shape = (len(y), len(x)).
    """

    def load_data(self):
        self._initialize_variables()
        # Parent initialization aliases these lists; keep them independent.
        self.x_paths = []
        self.x_offseted_paths = []
        self.EF_paths = []
        self.EF_offseted_paths = []
        self.VL_paths = []
        self.VL_offseted_paths = []
        self.y_paths = []
        self.z_paths = []
        reference_x = reference_y = None
        sum_z = None
        compatible = True

        for path in self.path_lst:
            print(f'Load File: {path}')
            self._read_file(path)
            self._extract_measurement_conditions()
            data = self._extract_intensity_data()
            # Rows in the file are energies, columns are momentum points.
            # The rest of SpecTaroScopy expects rows = y, columns = x.
            z = np.nan_to_num(np.asarray(data, dtype=float).T,
                              nan=0.0, posinf=0.0, neginf=0.0)
            x = self.x.copy()
            y = self.y.copy()
            if z.shape != (len(y), len(x)):
                raise ValueError(f'Axis/image mismatch in {path}: '
                                 f'z={z.shape}, x={len(x)}, y={len(y)}')
            self.z_paths.append(z.copy())
            self.x_paths.append(x)
            self.y_paths.append(y)
            if reference_x is None:
                reference_x, reference_y = x.copy(), y.copy()
                sum_z = z.copy()
            elif (np.array_equal(reference_x, x) and
                  np.array_equal(reference_y, y)):
                if compatible:
                    sum_z += z
            else:
                compatible = False
                print(f'Axis coordinates differ: {path}; using last file instead of averaging.')

        if not self.z_paths:
            raise ValueError('No IgorPro Image files were selected.')
        self.z_sekisan_flag = compatible
        self.z = sum_z / len(self.z_paths) if compatible else self.z_paths[-1].copy()
        # Keep displayed coordinates consistent with the displayed image.
        if compatible:
            self.x, self.y = reference_x.copy(), reference_y.copy()
        else:
            self.x, self.y = self.x_paths[-1].copy(), self.y_paths[-1].copy()
        self._set_axis_metadata()
        self.filename = (self._create_filename(self.filename_lst)
                         if compatible else self.filename_lst[-1])
        self.x_offseted = self.x.copy()
        self.y_offseted = self.y.copy()

    def _read_file(self, path):
        with open(path, encoding='utf-8-sig', errors='replace') as f:
            self.l = [line.rstrip('\r\n') for line in f]

    def _extract_measurement_conditions(self):
        self.Epass = None
        self.x_label = 'X' #'Binding Energy (eV)'
        self.y_label = 'Y' # r'$k_{\parallel}\ \mathrm{(\AA^{-1})}$'
        self.y_label_initial = self.y_label
        self.z_label = 'Z' #'Intensity (counts)'
        if len(self.l) < 3:
            raise ValueError('Expected title, coordinate header, and data rows.')
        header = self.l[1].split('\t')
        if len(header) < 2:
            raise ValueError('Second line must contain tab-separated momentum coordinates.')
        try:
            self.y = np.asarray([float(v) for v in header[1:]], dtype=float)
        except ValueError as exc:
            raise ValueError('Non-numeric momentum coordinate in second line.') from exc
        if not np.all(np.isfinite(self.y)):
            raise ValueError('Non-finite momentum coordinate.')

    def _extract_intensity_data(self, data_index='DATA:'):
        energies = []
        intensities = []
        n_y = len(self.y)
        for lineno, line in enumerate(self.l[2:], start=3):
            if not line.strip():
                continue
            fields = line.split('\t')
            if len(fields) != n_y + 1:
                raise ValueError(f'Line {lineno}: expected {n_y + 1} columns, '
                                 f'found {len(fields)}.')
            try:
                energy = float(fields[0])
                values = [float(v) if v.strip() else 0.0 for v in fields[1:]]
            except ValueError as exc:
                raise ValueError(f'Line {lineno}: invalid numeric value.') from exc
            energies.append(energy)
            intensities.append(values)
        if not energies:
            raise ValueError('No image data rows found.')
        self.x = np.asarray(energies, dtype=float)
        if not np.all(np.isfinite(self.x)):
            raise ValueError('Non-finite energy coordinate.')
        self._set_axis_metadata()
        return np.asarray(intensities, dtype=float)

    def _set_axis_metadata(self):
        self.x_min, self.x_max = float(np.min(self.x)), float(np.max(self.x))
        self.y_min, self.y_max = float(np.min(self.y)), float(np.max(self.y))
        self.x_step = float(abs(self.x[1] - self.x[0])) if len(self.x) > 1 else 0.0
        self.y_step = float(abs(self.y[1] - self.y[0])) if len(self.y) > 1 else 0.0

    def _append_data(self, z_):
        """Compatibility method; load_data handles averaging explicitly."""
        if self.z is None:
            self.z = np.asarray(z_, dtype=float).copy()
        else:
            if self.z.shape != np.shape(z_):
                self.z_sekisan_flag = False
                return
            self.z += z_

    def _finalize_z_image(self):
        """Compatibility method; averaging is performed in load_data."""
        return

if __name__ == "__main__":
    main()
