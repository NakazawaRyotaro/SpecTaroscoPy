import customtkinter
import numpy as np
import copy
import matplotlib.pyplot as plt
import platform
import subprocess
import math
import re

from pathlib import Path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from matplotlib.ticker import ScalarFormatter, LogFormatter
from scipy.interpolate import interp1d

# -------------------- モジュール読み込み --------------------
import sys
import os

# matplotlibのバックエンドをmacOS用に設定
if platform.system() == "Darwin":
    import matplotlib
    matplotlib.use('tkagg')  # GUIありバックエンド
# 自作モジュールのインポートのため、srcディレクトリをsys.pathに追加
CURRENT_DIR = Path(__file__).resolve().parent          # このファイルのあるディレクトリ（例: src/analysis）
SRC_PATH = CURRENT_DIR.parent                          # 1つ上が src/
sys.path.append(str(SRC_PATH))                         # str()で文字列に変換してappendする

# 自作モジュールのインポート（srcを基準にした絶対import）
from RyoPy import defs_for_analysis as rpa
from RyoPy.MBS_A1 import MBS_A1
from RyoPy.SCIENTA_DA30 import SCIENTA_DA30
from RyoPy.PlotControl import ImagePlotControl, PlotControl
from RyoPy.Spectrum import Spectrum
from setting.setting import App as SettingApp


# -------------------- ファイルパスの設定 --------------------
SETTING_PATH = SRC_PATH / "setting"
default_setting_path = SETTING_PATH / "default_setting.txt"
arpes_image_setting_path = SETTING_PATH / "ARPES_image_setting.txt"

# -------------------- 設定ファイルからの読み込み --------------------
# フォルダパスを取得（なければデフォルトにする）
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
if not has_IDIR:
    IDIR = SRC_PATH.parent.parent  # default
    
# ユーザー名などのその他設定
USER, _ = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")

# ウィンドウや画像のサイズ設定
WINDOW_WIDTH, has_WINDOW_WIDTH = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "window_width_photoemission_intensity_map")
WINDOW_HEIGHT, has_WINDOW_HEIGHT = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "window_height_photoemission_intensity_map")
IMAGE_WIDTH, has_IMAGE_WIDTH = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "image_width_photoemission_intensity_map")
IMAGE_HEIGHT, has_IMAGE_HEIGHT = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "image_height_photoemission_intensity_map")

# 初期値の設定
if not has_WINDOW_WIDTH:
    WINDOW_WIDTH = 800
if not has_WINDOW_HEIGHT:
    WINDOW_HEIGHT = 750
if not has_IMAGE_HEIGHT:
    IMAGE_HEIGHT = 3.3
if not has_IMAGE_WIDTH:
    IMAGE_WIDTH = 5.8

EDCS_HEIGHT=IMAGE_HEIGHT*2.3
EDCS_WIDTH=IMAGE_WIDTH*0.6

print(f"windowの幅: {WINDOW_WIDTH}, windowの高さ: {WINDOW_HEIGHT}")
print(f"図の幅: {IMAGE_WIDTH}, 図の高さ: {IMAGE_HEIGHT}")

FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")
COLORMAP, has_COLORMAP = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "colormap_photoemission_intensity_map", type="str")
if not has_COLORMAP:
    COLORMAP = "viridis"

# EDC(s)　plotのカラー
SPECTRAL_COLOR_='darkslateblue'
SPECTRAL_COLOR, has_SPECTRAL_COLOR = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "color_edc", type="str")
if not has_SPECTRAL_COLOR:
    SPECTRAL_COLOR=SPECTRAL_COLOR_
    
# 表示する桁数
ORDER_X = 10
ORDER_Y = copy.copy(ORDER_X)    
ORDER_Z = 10


# 大枠
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # 解析で出てきた変数の初期化
        self.x_label='X'
        self.y_label='Y'    
        self.x=None
        self.x_min=None
        self.x_max=None
        self.y=None
        self.y_min=None
        self.y_max=None
        self.z_min=None
        self.z_max=None
        self.x_offset=0
        self.y_offset=0
        self.z_ini=None
        self.colormap=COLORMAP
        self.file_output_label=None
        self.hn=None
        self.Vsample=None
        self.x_EF=None
        self.y_slice_min=None
        self.y_slice_max=None
        self.yscale_edc='linear'
        self.intensity_edc_ydc_offset=None
        self.flag_swap_image_xy_axes=False
        self.flag_reverse_image_y_axis=False
        self.flag_reverse_image_x_axis=False
        self.background_intensity_edc_ydc=None
        # 各ファイルの設定を記憶する辞書（ファイル名をキーとして値を保持）
        self.edc_settings = {}
        # 元の x_data と y_data を保存するための辞書
        self.original_x_edc = {}
        self.original_y_edc = {}
        # プロットの表示/非表示状態を保持する辞書
        self.plot_visibility = {}
        # データ保持のため？
        self.selected_filename = None

        # メンバー変数の設定
        self.fonts = (FONT_TYPE, 15)
        # フォームのセットアップをする

        # CustomTkinter のフォームデザイン設定
        customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
        customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

        # title
        self.title("SpecTaroscoPy — PES Image")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")  # ウィンドウサイズ設定

        self.setup_form()

    def setup_form(self):       
        #アイコン
        # try:
        #     if platform.system() == "Darwin":  # macOS
        #         img_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'arpes.png')
        #         if os.path.exists(img_path):
        #             icon_image = PhotoImage(file=img_path)
        #             self.tk.call('wm', 'iconphoto', self._w, icon_image)
        #     elif platform.system() == "Windows":  # Windows
        #         ico_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'arpes.ico')
        #         if os.path.exists(ico_path):
        #             self.iconbitmap(ico_path)
        # except:
        #     pass  
        columnspan=5
        # frameを出力 
        self.generate_load_data_frame(columnspan-1) # data load
        self.generate_mcp_correction_frame(columnspan) # mcp correction
        self.generate_axis_conversion_frame(2*columnspan) # axis conversion

        self.generate_image_plot_frame(2*columnspan) # image plot data (全体)
        self.generate_color_tunner_frame()
        self.generate_image_button_frame()

        self.generate_edc_plot_frame() # 2D image slicer in image_plot_frame
        self.generate_edc_plot_buttons_frame() # 2D image slicerのボタンたち
        self.generate_edc_viewer()
        self.generate_edcs_stack_frame() # EDCs stack in image_plot_frame
        self.generate_edcs_stack_range_frame() #EDCs stackの範囲設定
        self.generate_other_buttons_GUI(columnspan) # その他のボタンたち

        # 行方向のマスのレイアウトを設定する。
        # リサイズしたときに一緒に拡大したい行をweight 1に設定。
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)  
        # 列方向のマスのレイアウトを設定する
        self.grid_columnconfigure(columnspan+1, weight=1, uniform="group1") 


    def generate_other_buttons_GUI(self, columnspan):
        # open manualボタン
        self.manual_button = customtkinter.CTkButton(master=self, text="Manual", font=self.fonts, command=self.open_manual_button_callback, width=120)
        self.manual_button.grid(row=4, column=0, padx=(20, 10), pady=(0, 10), sticky="nw")

        # Settingボタン
        setting_button = customtkinter.CTkButton(self, command=self.open_setting, text="Setting", font=self.fonts, width=120)
        setting_button.grid(row=4, column=1, padx=(0, 10), pady=(0, 10), sticky="nw")

        # File explorerボタン
        # オペレーティングシステムを判別
        if platform.system() == 'Darwin':  # macOSの場合
            # Finderボタン
            Finder_button = customtkinter.CTkButton(self, command=self.finder_button_callback, text="Finder", font=self.fonts, width=120)
        elif platform.system() == 'Windows':  # Windowsの場合
            # explorerボタン
            Finder_button = customtkinter.CTkButton(self, command=self.finder_button_callback, text="File Explorer", font=self.fonts, width=120)
        # 配置
        Finder_button.grid(row=4, column=2, padx=(0, 10), pady=(0, 10), sticky="nw")

        # show_fig_button = customtkinter.CTkButton(self, command=self.show_all_figures_button_callback, text="Show Figs", font=self.fonts, width=120)
        # show_fig_button.grid(row=4, column=3, padx=(0, 10), pady=(0, 10), sticky="nw")
        # close_fig_button = customtkinter.CTkButton(self, command=self.show_all_figures_button_callback, text="Close Figs", font=self.fonts, width=120)
        # close_fig_button.grid(row=4, column=4, padx=(0, 10), pady=(0, 10), sticky="nw")

        # バッファー (rangeとcolumnの最後の数字をボタンの数にする)
        for i in range(2*columnspan-3):
            customtkinter.CTkLabel(master=self, text=' ', font=self.fonts, width=110).grid(row=4, column=i+3, padx=(0,10), pady=(0,10), sticky="nw")

    def open_manual_button_callback(self):
        # 現在のスクリプトの親ディレクトリを取得
        parent_directory = os.path.dirname(os.path.abspath(__file__))
        # 親ディレクトリにあるmanual.pdfのパスを作成
        pdf_path = os.path.join(parent_directory, '..', '..', 'manual.pdf')
        pdf_path = os.path.abspath(pdf_path)  # 絶対パスに変換

        # ファイルの存在確認
        if not os.path.exists(pdf_path):
            print(f"Error: {pdf_path} does not exist.")
            return

        # オペレーティングシステムを判別
        if platform.system() == 'Darwin':  # macOSの場合
            # PDFをプレビューで開くための指定
            import subprocess
            subprocess.run(["open", pdf_path])
        elif platform.system() == 'Windows':  # Windowsの場合
            # WindowsでPDFを開く場合は、startコマンドを使用
            command = ['start', pdf_path]
            # PDF を開く
            try:
                subprocess.Popen(command, shell=True)
            except Exception as e:
                print(f"Failed to open the PDF: {e}")
        else:
            raise Exception('Unsupported operating system')

    def open_setting(self):
        # 初期タブを指定してAppを直接呼び出す
        initial_tab = "ARPES"  # ARPES タブを初期表示
        app = SettingApp(initial_tab=initial_tab)
        app.resizable(True, True)
        app.mainloop()

    def finder_button_callback(self):
        # 優先：self.peim.path、なければ IDIR を使用
        try:
            target_dir = os.path.dirname(self.peim.path)
        except AttributeError:
            target_dir = IDIR

        if not os.path.exists(target_dir):
            print(f"Directory does not exist: {target_dir}")
            messagebox.showinfo("Tips", "After you load data, you can open the data directory.")
            return  # ← ここで処理を止める

        system_platform = platform.system()

        if system_platform == "Darwin":  # macOS
            subprocess.run(["open", target_dir])
        elif system_platform == "Windows":
            os.startfile(target_dir)
        elif system_platform == "Linux":
            subprocess.run(["xdg-open", target_dir])
        else:
            print("Unsupported OS")

    # figを出したり消したりしようと思ったがバグが多いのでとりあえず断念
    def show_all_figures_button_callback(self):
        self.peim_pltctrl.show_figures()  
    def close_figs_button_callback(self):
        plt.close('all')
        print("All matplotlib figures closed.")

################################################################################################
    def generate_load_data_frame(self, columnspan):
        # Load Data Frame ########################
        self.load_data_frame = customtkinter.CTkFrame(self)
        self.load_data_frame.grid(row=1, column=0, padx=10, pady=(10,10), sticky="ew", columnspan=columnspan+1)
        # title
        load_data_label = customtkinter.CTkLabel(self.load_data_frame, text='Load Data', font=self.fonts, width=100)
        load_data_label.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
         # loadボタン
        load_file_button = customtkinter.CTkButton(self.load_data_frame, command=self.load_file_button_callback, text="Load", font=self.fonts, width=120)
        load_file_button.grid(row=0, column=3, padx=(0,10), pady=(10,5), sticky="w")
        customtkinter.CTkLabel(self.load_data_frame, text='Equipment', width=70).grid(row=0, column=1, padx=(5,5), pady=(10,5), sticky="e")
        self.equipment_combo = customtkinter.CTkComboBox(self.load_data_frame, font=self.fonts, command=None, width=200,
                                                    values=["MBS A-1 (Kera G, IMS)/General text", 
                                                            "Scienta DA30 (IMS)",
                                                            "MBS A-1 (G1, BL7U, UVSOR)", 
                                                            "MBS A-1 (G2, BL7U, UVSOR)", 
                                                            "MBS A-1 (G3, BL7U, UVSOR)"
                                                            ])
        self.equipment_combo.grid(row=0, column=2, padx=(0, 9), pady=(10,5), sticky="ew", columnspan=1)
        # パスを表示
        file_label = customtkinter.CTkLabel(self.load_data_frame, text='Base Filename')
        file_label.grid(row=1, column=0, padx=(0,10), pady=(0,5), sticky="ew")

        self.file_output_label = customtkinter.CTkLabel(master=self.load_data_frame, text='')
        self.file_output_label.grid(row=1, column=1, padx=(0,10), pady=(0,5), sticky="ew", columnspan=3)

    def load_file_button_callback(self):
        print("--- Data Loading ---")
        # 初期化
        self.x_offset=0
        self.y_offset=0
        
        self.hn=None
        self.Vsample=None
        self.x_EF=None
        self.y_slice_min=None
        self.y_slice_max=None
        self.intensity_edc_ydc_offset=None
        self.legend_loc_edc="best"
        self.legend_loc_edcs=None
        self.z_min=None
        self.z_max=None

        self.flag_swap_image_xy_axes=False
        self.flag_reverse_image_y_axis=False
        self.flag_reverse_image_x_axis=False
        self.label_edc=None
        
        self.z_ini=None

        # photoemission intensity map インスタンス生成
        if self.equipment_combo.get() == "MBS A-1 (Kera G, IMS)/General text":
            self.peim=MBS_A1(idir=IDIR)
        elif self.equipment_combo.get() == "MBS A-1 (G2, BL7U, UVSOR)":
            self.peim=MBS_A1(idir=IDIR)
        elif self.equipment_combo.get() == "MBS A-1 (G3, BL7U, UVSOR)":
            self.peim=MBS_A1(idir=IDIR)
        
        elif self.equipment_combo.get() == "Scienta DA30 (IMS)":
            self.peim=SCIENTA_DA30(idir=IDIR)



        if self.peim.z is None: # 平均化処理できなかった場合は、最後に読み込んだfileを解析する
            self.peim.z = copy.deepcopy(self.peim.z_paths[-1])
            self.z_image = copy.deepcopy(self.peim.z_paths[-1])
            self.z_image_paths=copy.deepcopy(self.peim.z_paths)

            # zはリストがそろっていない場合の処理を別で行うため少し複雑
            self.z_min=np.inf
            self.z_max=-np.inf
            for i in range(len(self.peim.z_paths)):
                z_min=np.amin(np.array(self.peim.z_paths[i]))
                z_max=np.amax(np.array(self.peim.z_paths[i]))
                if self.z_min>=z_min:
                    self.z_min=z_min
                if self.z_max<=z_max:
                    self.z_max=z_max

        else:
            self.z_image=copy.deepcopy(self.peim.z)
            self.z_image_paths=copy.deepcopy(self.peim.z_paths)
            self.z_min=np.amin(self.z_image)
            self.z_max=np.amax(self.z_image)         
        
        if self.peim.EF is None:
            self.x=self.peim.x_paths[-1]
            self.x_offseted=copy.deepcopy(self.x)
            self.x_offseted_paths = self.peim.x_paths
        else:

            self.x_offseted=copy.deepcopy(self.peim.EF)
            self.x_offseted_paths = self.peim.EF_paths
        self.y=self.peim.y
        self.y_offseted=copy.deepcopy(self.y)
        
        if self.peim.x_label is not None:
            self.x_label=self.peim.x_label
        if self.peim.y_label is not None:
            self.y_label=self.peim.y_label

        self.y_min=self.peim.y_min
        self.y_max=self.peim.y_max
        self.y_step=self.peim.y_step

        # xはリストがそろっていない場合の処理を別で行うため少し複雑
        self.x_min=np.inf
        self.x_max=-np.inf
        for i in range(len(self.peim.z_paths)):
            if self.peim.EF is None:
                x_min=np.amin(np.array(self.peim.x_paths[i]))
                x_max=np.amax(np.array(self.peim.x_paths[i]))
            else:
                x_min=np.amin(np.array(self.peim.EF_paths[i]))
                x_max=np.amax(np.array(self.peim.EF_paths[i]))

            if self.x_min>=x_min:
                self.x_min=x_min
            if self.x_max<=x_max:
                self.x_max=x_max
        self.x_step=self.peim.x_step

        # pathのlabelを更新
        self.file_output_label.configure(text=self.peim.filename)
        
        # 以前のプロットがあれば閉じる
        if hasattr(self, 'peim_canvas') and self.peim_canvas is not None:
            plt.close(self.peim_pltctrl.fig)  # 特定の図を閉じる
            self.peim_canvas.get_tk_widget().destroy() # 消えないので追加したがダメ。
            self.peim_canvas = None
        if hasattr(self, 'edc_pltctrl') and self.edc_pltctrl is not None:
            plt.close(self.edc_pltctrl.fig)  
        if hasattr(self, 'edcs_pltctrl') and self.edcs_pltctrl is not None:
            plt.close(self.edcs_pltctrl.fig)

        # filename
        self.filename_image_entry.delete(0, customtkinter.END)
        self.filename_image_entry.insert(0, f'{self.peim.filename}')

        # インスタンス作製
        self.peim_pltctrl = ImagePlotControl(self.x_offseted, self.y_offseted, self.z_image,
                                                title=f"{self.filename_image_entry.get()}\n", 
                                                colormap=self.colormap, 
                                                x_label=self.peim.x_label, 
                                                y_label=self.peim.y_label, 
                                                z_label=self.peim.z_label,
                                                figsize_w=IMAGE_WIDTH, figsize_h=IMAGE_HEIGHT,
                                                scientific_zscale=True)

        if self.peim.x_label=="Binding Energy (eV)":
            self.peim_pltctrl.ax.invert_xaxis()
        # canvasを再描画
        self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)

        # Range frameの更新
        self.x_lim_min_entry.delete(0, customtkinter.END)
        self.x_lim_max_entry.delete(0, customtkinter.END)
        self.y_lim_min_entry.delete(0, customtkinter.END)
        self.y_lim_max_entry.delete(0, customtkinter.END)
        self.x_offset_entry.delete(0, customtkinter.END)
        self.y_offset_entry.delete(0, customtkinter.END)
        self.x_lim_min_entry.insert(0, self.x_min)
        self.x_lim_max_entry.insert(0, self.x_max)
        self.y_lim_min_entry.insert(0, self.y_min)
        self.y_lim_max_entry.insert(0, self.y_max)
        self.x_offset_entry.insert(0, 0)
        self.y_offset_entry.insert(0, 0)
        
        # color tunner frameの更新
        self.z_lim_min_entry.delete(0, customtkinter.END)
        self.z_lim_max_entry.delete(0, customtkinter.END)
        self.z_lim_min_entry.insert(0, self.z_min)
        self.z_lim_max_entry.insert(0, self.z_max)

        # Sliderの初期化と更新
        self.z_lim_min_slider.configure(from_=self.z_min, to=self.z_max)
        self.z_lim_max_slider.configure(from_=self.z_min, to=self.z_max)
        self.z_lim_min_slider.set(self.z_min)
        self.z_lim_max_slider.set(self.z_max)

        # Y slice (EDC)
        self.y_slice_min_entry.delete(0, customtkinter.END)
        self.y_slice_max_entry.delete(0, customtkinter.END)
        self.y_slice_center_entry.delete(0, customtkinter.END)
        self.y_slice_width_entry.delete(0, customtkinter.END)
        self.background_intensity_edc_ydc_entry.delete(0, customtkinter.END)
        self.y_slice_min_entry.insert(0, self.y_min)
        self.y_slice_max_entry.insert(0, self.y_max)
        self.y_slice_center_entry.insert(0, np.round((self.y_min+self.y_max)/2, ORDER_Y))
        self.y_slice_width_entry.insert(0, np.round(abs(self.y_max-self.y_min), ORDER_Y))
        # Sliderの初期化と更新
        self.y_slice_max_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_min_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_center_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_width_slider.configure(from_=self.y_step, to=self.y_max-self.y_min)
        self.y_slice_max_slider.set(self.y_max)
        self.y_slice_min_slider.set(self.y_min)
        self.y_slice_center_slider.set(np.round((self.y_min+self.y_max)/2, ORDER_Y))
        self.y_slice_width_slider.set(np.round(abs(self.y_max-self.y_min), ORDER_Y))


        # Energy slice (YDS)
        self.x_slice_min_entry.delete(0, customtkinter.END)
        self.x_slice_max_entry.delete(0, customtkinter.END)
        self.x_slice_center_entry.delete(0, customtkinter.END)
        self.x_slice_width_entry.delete(0, customtkinter.END)
        self.x_slice_min_entry.insert(0, self.x_min)
        self.x_slice_max_entry.insert(0, self.x_max)
        self.x_slice_center_entry.insert(0, np.round((self.x_min+self.x_max)/2, ORDER_X))
        self.x_slice_width_entry.insert(0, np.round(abs(self.x_max-self.x_min), ORDER_X))
        # slider
        self.x_slice_max_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_min_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_center_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_width_slider.configure(from_=self.x_step, to=self.x_max-self.x_min)
        self.x_slice_max_slider.set(self.x_max)
        self.x_slice_min_slider.set(self.x_min)
        self.x_slice_center_slider.set(np.round((self.x_min+self.x_max)/2, ORDER_X))
        self.x_slice_width_slider.set(np.round(abs(self.x_max-self.x_min), ORDER_X))

        # # EDCの範囲更新 X 
        self.x_edc_max_entry.delete(0, customtkinter.END)
        self.x_edc_min_entry.delete(0, customtkinter.END)
        self.x_edc_max_entry.insert(0, self.x_max)
        self.x_edc_min_entry.insert(0, self.x_min)

        # EDCsエントリーボックス初期化
        self.filename_edcs_entry.delete(0, customtkinter.END)
        self.edcs_ystep_entry.delete(0, customtkinter.END)
        self.edcs_z_offset_entry.delete(0, customtkinter.END)
        self.edcs_stack_x_lim_min_entry.delete(0, customtkinter.END)
        self.edcs_stack_x_lim_max_entry.delete(0, customtkinter.END)
        self.edcs_stack_y_lim_min_entry.delete(0, customtkinter.END)
        self.edcs_stack_y_lim_max_entry.delete(0, customtkinter.END)

        # EDC作成
        self.generate_an_edc() # EDCを作成
        # plot
        self.plot_edc()

        # 前回の設定をひきづりたい
        self.edc_pltctrl.ax.set_yscale(self.yscale_edc)
        self.update_edc_z_range_event()
        self.edc_pltctrl.ax.legend(loc='best', fontsize='small') # 凡例を表示
        if self.legend_loc_edc==None:
            self.edc_pltctrl.ax.get_legend().remove()
        self.update_edc_legend()
        self.edc_pltctrl.update_canvas()

        # Stack EDCsは初期化する。
        self.edcs_stack_pltctrl=PlotControl(title="EDCs will be shown here.", x_label=self.x_label, y_label='Intensity (cps)', figsize_w=EDCS_WIDTH, figsize_h=EDCS_HEIGHT, fontsize=12)
        self.edcs_stack_pltctrl.add_spectrum(0, 0, "EDCs", color="white")
        self.edcs_stack_pltctrl.change_legend_position(mode="best")
        self.edcs_stack_canvas = FigureCanvasTkAgg(self.edcs_stack_pltctrl.fig, master=self.image_plot_frame)
        self.edcs_stack_canvas.get_tk_widget().grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.edcs_stack_pltctrl.update_canvas()



################################################################################################
    def generate_mcp_correction_frame(self, columnspan):
        # MCP Correction Frame #############
        self.mcp_correction_frame = customtkinter.CTkFrame(self)
        self.mcp_correction_frame.grid(row=1, column=columnspan, padx=(0,10), pady=(10,10), sticky="ew", columnspan=columnspan)
        # title
        mcp_correction_label = customtkinter.CTkLabel(self.mcp_correction_frame, text='Intensity\nCorrection', font=self.fonts, width=100)
        mcp_correction_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="ew")
        
        # tabで切り替えることにする
        self.mcp_selection = customtkinter.StringVar(value="Image File\n→fMDC")  # デフォルトは "Image"
        # セグメントボタン
        self.mcp_segmented = customtkinter.CTkSegmentedButton(
            self.mcp_correction_frame,
            values=["Image File\n→fMDC", "MDC\nFile", "Max"],
            variable=self.mcp_selection
        )
        self.mcp_segmented.grid(row=0, column=1, padx=(0, 8), pady=(5,0), sticky="ew")
        
        # 実行ボタン
        mcp_correction_do_it_button = customtkinter.CTkButton(self.mcp_correction_frame, command=self.do_mcp_correction_callback, text="Do It", font=self.fonts, width=110)
        mcp_correction_do_it_button.grid(row=0, column=3, padx=(0,8), pady=(10,5), sticky="ew")
        # データロードボタン
        Load_mcp_button = customtkinter.CTkButton(self.mcp_correction_frame, command=self.load_mcp_correction_callback, text="Load", font=self.fonts, width=110)
        Load_mcp_button.grid(row=0, column=2, padx=(0,8), pady=(10,5), sticky="ew")
        # resetボタン
        mcp_correction_do_it_button = customtkinter.CTkButton(self.mcp_correction_frame, command=self.reset_mcp_correction_callback, text="Cancel", font=self.fonts, width=110)
        mcp_correction_do_it_button.grid(row=0, column=4, padx=(0,8), pady=(10,5), sticky="ew")
        # path label
        filename_label = customtkinter.CTkLabel(self.mcp_correction_frame, text='Filename')
        filename_label.grid(row=1, column=0, padx=(0,8), pady=(0,5), sticky="ew")

        self.file_mcp_correction_label = customtkinter.CTkLabel(master=self.mcp_correction_frame, text='', wraplength=400)
        self.file_mcp_correction_label.grid(row=1, column=1, padx=(0,10), pady=(0,5), sticky="ew", columnspan=4)

    def load_mcp_correction_callback(self):
        # 以前のプロットがあれば閉じる
        if hasattr(self, 'mcp_spectrum_pltctrl') and self.mcp_spectrum_pltctrl is not None:
            plt.close(self.mcp_spectrum_pltctrl.fig)  # 図を閉じる
        
        if self.mcp_segmented.get()=="Image File\n→fMDC":
            if self.equipment_combo.get()=='MBS A-1 (Kera G, IMS)/General text' or self.equipment_combo.get()=='MBS A-1 (G1, BL7U, UVSOR)'or self.equipment_combo.get()=='MBS A-1 (G2, BL7U, UVSOR)'or self.equipment_combo.get()=='MBS A-1 (G3, BL7U, UVSOR)':
                mcp_image=MBS_A1(idir=IDIR)
                # YDC作成
                mcp_image.generate_a_ydc(mcp_image.z, mcp_image.y, mcp_image.y_min, mcp_image.y_max)
                    
                # mcp function作成
                mcp_spectrum_x=copy.deepcopy(mcp_image.y)
                self.mcp_spectrum_y=copy.deepcopy(mcp_image.z_ydc)
                self.mcp_spectrum_filename=mcp_image.filename.replace('.txt', '_fMDC.txt')
                x_label=mcp_image.y_label

        elif self.mcp_segmented.get()=='MDC\nFile':
            mcp_ydc=Spectrum()
            mcp_ydc.read_labels_from_file_auto(idir=IDIR)
            print(mcp_ydc.label_list[0])
            mcp_ydc.load_xy_data_from_file_auto_2(mcp_ydc.label_list[0], mcp_ydc.label_list[1])
             
            # mcp function作成
            mcp_spectrum_x=copy.deepcopy(mcp_ydc.x)
            self.mcp_spectrum_y=copy.deepcopy(mcp_ydc.y)
            hoge, x_label = mcp_ydc.load_y2_data_from_info_of_file(mcp_ydc.path, key_y2_label='Y Label')
            self.mcp_spectrum_filename=mcp_ydc.filename

        elif self.mcp_segmented.get()=='Max':
            mcp_spectrum_x=copy.deepcopy(self.y)
            self.mcp_spectrum_y=np.max(self.peim.z, axis=1)
            self.mcp_spectrum_filename=f'Max Intensity per pixel {self.peim.filename}'
            x_label=self.peim.y_label

        # mcp_spectrum_yの強度規格化
        self.mcp_spectrum_y/=max(self.mcp_spectrum_y)

        # pathのlabelを更新
        self.file_mcp_correction_label.configure(text=self.mcp_spectrum_filename)

        # plot
        self.mcp_spectrum_pltctrl=PlotControl(f"MDC: {self.mcp_spectrum_filename}", x_label=x_label, y_label="Intensity (arb. units)", initialize_figs=True, fontsize=12, figsize_w=4, figsize_h=3)
        self.mcp_spectrum_pltctrl.plot_spectrum(mcp_spectrum_x, self.mcp_spectrum_y, label='', scatter=False)
        self.mcp_spectrum_pltctrl.show_figures()

    def do_mcp_correction_callback(self):
        if self.peim.y_label!=r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$":
            if self.z_ini is None:
                self.z_ini = copy.deepcopy(self.peim.z)
                self.z_paths_ini = copy.deepcopy(self.peim.z_paths)

            # MCP補正
            self.peim.z=(self.peim.z.T/self.mcp_spectrum_y).T
            self.z_image=copy.deepcopy(self.peim.z)
            for i in range(len(self.peim.z_paths)):
                self.peim.z_paths[i]=(self.peim.z_paths[i].T/self.mcp_spectrum_y).T
            self.z_image_paths=copy.deepcopy(self.peim.z_paths)

            self.z_min=np.amin(self.peim.z)
            self.z_max=np.amax(self.peim.z)
            self.update_range_event()
            self.peim_pltctrl.set_z_range(self.z_min, self.z_max)
            self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)

            # color tunner frameの更新
            self.z_lim_min_entry.delete(0, customtkinter.END)
            self.z_lim_max_entry.delete(0, customtkinter.END)
            self.z_lim_min_entry.insert(0, self.z_min)
            self.z_lim_max_entry.insert(0, self.z_max)
            # Sliderの初期化と更新
            self.z_lim_min_slider.configure(from_=self.z_min, to=self.z_max, command=self.update_z_range_slider_event)
            self.z_lim_max_slider.configure(from_=self.z_min, to=self.z_max, command=self.update_z_range_slider_event)
            self.z_lim_min_slider.set(self.z_min)
            self.z_lim_max_slider.set(self.z_max)

            # savefileのためにpeimに追加
            self.peim.mcp_function = copy.deepcopy(self.mcp_spectrum_y)
            self.peim.filename_mcp_function = copy.deepcopy(self.mcp_spectrum_filename)

            # EDCプロット
            self.generate_an_edc() # EDCを作成
            self.plot_edc() # plot初期化->plot
            print("MCP Correction was applied.")
        else:
            messagebox.showerror("Error!", "After converting angles to inverse wave numbers, you cannot normalize the image with a Y distribution curve.")
            
    def reset_mcp_correction_callback(self):
        if self.peim.y_label!=r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$":
            # save時のためにインスタンス変数をNoneに変更。
            self.peim.mcp_function = None
            self.peim.filename_mcp_function = None

            # データを戻す
            self.peim.z=copy.deepcopy(self.z_ini)
            self.z_image=copy.deepcopy(self.peim.z)
            self.peim.z_paths=copy.deepcopy(self.z_paths_ini)
            self.z_min=np.amin(self.peim.z)
            self.z_max=np.amax(self.peim.z)
            self.update_range_event()
            self.peim_pltctrl.set_z_range(self.z_min, self.z_max)
            self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)

            # color tunner frameの更新
            self.z_lim_min_entry.delete(0, customtkinter.END)
            self.z_lim_max_entry.delete(0, customtkinter.END)
            self.z_lim_min_entry.insert(0, self.z_min)
            self.z_lim_max_entry.insert(0, self.z_max)
            # Sliderの初期化と更新
            self.z_lim_min_slider.configure(from_=self.z_min, to=self.z_max)
            self.z_lim_max_slider.configure(from_=self.z_min, to=self.z_max)
            self.z_lim_min_slider.set(self.z_min)
            self.z_lim_max_slider.set(self.z_max)

            # EDCプロット
            self.generate_an_edc() # EDCを作成
            self.plot_edc() # plot初期化->plot
            print("MCP Correction was removed from the image.")

        else:
            messagebox.showerror("Error!", "After converting the angles to inverse wave numbers, you cannot change the image.")
            
#################################################################################################
    def generate_axis_conversion_frame(self, columnspan):
        # Axis Conversion Frame #############
        self.axis_conversion_frame = customtkinter.CTkFrame(self)
        self.axis_conversion_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew", columnspan=columnspan)
        # title 
        customtkinter.CTkLabel(self.axis_conversion_frame, text=f'Axes\nConversion', font=self.fonts, width=150).grid(row=0, column=0, padx=10, pady=(0,0), sticky="ewns", rowspan=2)
        
        # buttonの大きさ
        width_buttons_light_source=85
        # HeIaボタン
        HeIa_button = customtkinter.CTkButton(self.axis_conversion_frame, command=lambda: self.one_photon_buttons_callback(self.get_x_EF_and_hn_of_HeIaUPS), 
                                              text="HeIa", font=self.fonts, width=width_buttons_light_source)
        HeIa_button.grid(row=0, column=1, padx=(0,5), pady=(10,0), sticky="w")
         # HeIIaボタン
        HeIIa_button = customtkinter.CTkButton(self.axis_conversion_frame, command=lambda: self.one_photon_buttons_callback(self.get_x_EF_and_hn_of_HeIIaUPS), 
                                               text="HeIIa", font=self.fonts, width=width_buttons_light_source)
        HeIIa_button.grid(row=0, column=2, padx=(0,5), pady=(10,0), sticky="w")
         # XeIaボタン
        XeIa_button = customtkinter.CTkButton(self.axis_conversion_frame, command=lambda: self.one_photon_buttons_callback(self.get_x_EF_and_hn_of_XeIaUPS), 
                                              text="XeIa", font=self.fonts, width=width_buttons_light_source)
        XeIa_button.grid(row=0, column=3, padx=(0,5), pady=(10,0), sticky="w")
        # AlKa
        AlKa_button = customtkinter.CTkButton(self.axis_conversion_frame, command=lambda: self.one_photon_buttons_callback(self.get_x_EF_and_hn_of_AlKaXPS),
                                              text="AlKa", font=self.fonts, width=width_buttons_light_source)
        AlKa_button.grid(row=0, column=4, padx=(0,5), pady=(10,0), sticky="w")
        # MgKa
        MgKa_button = customtkinter.CTkButton(self.axis_conversion_frame, command=lambda: self.one_photon_buttons_callback(self.get_x_EF_and_hn_of_MgKaXPS), 
                                            text="MgKa", font=self.fonts, width=width_buttons_light_source)
        MgKa_button.grid(row=0, column=5, padx=(0,5), pady=(10,0), sticky="w")
        # hn entry
        self.hn_entry = customtkinter.CTkEntry(self.axis_conversion_frame, placeholder_text="hv (eV)", font=self.fonts, width=100)
        self.hn_entry.grid(row=0, column=6, padx=(0,5), pady=(10,0), sticky="w")
        self.hn_entry.bind("<Return>",lambda event: self.one_photon_buttons_callback(self.get_x_EF_and_variable_hn))
        
        # EF手打ち
        self.EF_manual_entry = customtkinter.CTkEntry(self.axis_conversion_frame, placeholder_text="Ek@EF (eV)", font=self.fonts, width=100)
        self.EF_manual_entry.grid(row=0, column=7, padx=(0,5), pady=(10,0), sticky="ew")
        self.EF_manual_entry.bind("<Return>",lambda event: self.one_photon_buttons_callback(self.get_x_EF_manually))

        # 試料電圧
        sample_bias_label = customtkinter.CTkLabel(self.axis_conversion_frame, text="Supplied Bias", width=100)
        sample_bias_label.grid(row=0, column=8, padx=(0,5), pady=(10,0), sticky="e")
        self.Vsample_entry = customtkinter.CTkEntry(self.axis_conversion_frame, placeholder_text="V", width=50)
        self.Vsample_entry.insert(0, 0)
        self.Vsample_entry.grid(row=0, column=9, padx=(0,10), pady=(10,0), sticky="ew")

        # 2PPE
        twoPPE_frame = customtkinter.CTkFrame(self.axis_conversion_frame, width=220)
        twoPPE_frame.grid(row=1, column=1, padx=(0,5), pady=(5,10), sticky="ew", columnspan=6)
        self.make_2PPE_frame(twoPPE_frame)

        # 角度, k//変換
        # Frame
        angkhconversion_frame = customtkinter.CTkFrame(self.axis_conversion_frame, width=100)
        angkhconversion_frame.grid(row=1, column=7, padx=(0,5), pady=(5,10), sticky="ew")
        self.switch_value_angkhconversion = customtkinter.BooleanVar() # チェックボックスの変数を作成し、初期値をTrueに設定
        self.switch_value_angkhconversion.set(True)
        self.angkhconversion_switch = customtkinter.CTkSwitch(
            angkhconversion_frame,
            text=f"Angle\n→k//",
            variable=self.switch_value_angkhconversion)
        self.angkhconversion_switch.grid(row=0, column=1, padx=(5,5), pady=10, sticky="ew")

        # 真空準位基準のEB
        # Frame
        VL_frame = customtkinter.CTkFrame(self.axis_conversion_frame, width=200)
        VL_frame.grid(row=1, column=8, padx=(0, 5), pady=(5,10), sticky="ew", columnspan=2)
        self.switch_value_VL = customtkinter.BooleanVar()
        self.switch_value_VL.set(False)
        self.VL_switch = customtkinter.CTkSwitch(
            VL_frame,
            text=f"Ek\n→VL",
            variable=self.switch_value_VL, width=50)
        self.VL_switch.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="ew")
        self.SECO_entry = customtkinter.CTkEntry(VL_frame, placeholder_text="Ek@SECO (eV)", width=110)
        self.SECO_entry.grid(row=0, column=2, padx=(10,10), pady=10, sticky="ew")
    

    def make_2PPE_frame(self, twoPPE_frame):
        customtkinter.CTkLabel(twoPPE_frame, text="2PPE", width=30, font=self.fonts).grid(row=0, column=0, padx=(10,0), pady=(10,10), sticky="w")
        self.hn_2PPE_entry = customtkinter.CTkEntry(twoPPE_frame, placeholder_text="λ_ω (nm)", font=self.fonts, width=80)
        self.hn_2PPE_entry.grid(row=0, column=1, padx=(10,0), pady=(10,10), sticky="ew")
        self.hn_2PPE_entry.bind("<Return>",command=self.get_x_EF_and_hn_of_2PPE_entry)

        # Pumpラベル
        customtkinter.CTkLabel(twoPPE_frame, text="Pump", width=30).grid(row=0, column=3, padx=(10, 0), pady=(10, 10), sticky="w")

        # Pump選択用変数
        self.pump_selection = customtkinter.StringVar(value="3ω")  # デフォルトは "1w"
        # セグメントボタン（Pump）
        self.pump_segmented = customtkinter.CTkSegmentedButton(
            twoPPE_frame,
            values=["ω", "2ω", "3ω"],
            variable=self.pump_selection,
            command=lambda value: print(f"Selected Pump: {value}")
        )
        self.pump_segmented.grid(row=0, column=4, columnspan=2, padx=(10, 0), pady=5, sticky="ew")

        # # probe
        customtkinter.CTkLabel(twoPPE_frame, text="Probe", width=30).grid(row=0, column=6, padx=(10,0), pady=(10,10), sticky="w")
        self.probe_selection = customtkinter.StringVar(value="3ω")  # デフォルトを "3w"

        # セグメントボタンとしてまとめて配置
        self.probe_segmented = customtkinter.CTkSegmentedButton(
            twoPPE_frame,
            values=["ω", "2ω", "3ω"],
            variable=self.probe_selection,
            command=lambda value: print(f"Selected Probe: {value}")  # 任意のコールバック処理
        )
        self.probe_segmented.grid(row=0, column=7, padx=(10, 0), pady=5, sticky="ew")

        # zero delay
        # トグルスイッチの状態管理用変数（初期値: True）
        switch_value_zero_delay = customtkinter.BooleanVar()
        switch_value_zero_delay.set(True)
        # トグルスイッチ作成
        self.zero_delay_switch = customtkinter.CTkSwitch(
            twoPPE_frame,
            text="Zero\nDelay",
            variable=switch_value_zero_delay,
            width=30)
        # レイアウト設定（grid）
        self.zero_delay_switch.grid(row=0, column=9, padx=(10, 5), pady=10, sticky="ew")


    def get_x_EF_manually(self):
        self.hn=None
        self.x_EF=float(self.EF_manual_entry.get())

    def get_x_EF_and_hn_of_HeIaUPS(self):
        self.hn=21.218
        if self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            if self.peim.Epass==2:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep02_MBSA1_KeraG")
            if self.peim.Epass==5:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep05_MBSA1_KeraG")
            if self.peim.Epass==10:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep10_MBSA1_KeraG")
            if self.peim.Epass==20:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep20_MBSA1_KeraG")

    def get_x_EF_and_hn_of_HeIIaUPS(self):
        self.hn=40.814
        if self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            if self.peim.Epass==2:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep02_MBSA1_KeraG")
            if self.peim.Epass==5:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep05_MBSA1_KeraG")
            if self.peim.Epass==10:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep10_MBSA1_KeraG")
            if self.peim.Epass==20:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep20_MBSA1_KeraG")
        
    def get_x_EF_and_hn_of_XeIaUPS(self):
        self.hn=8.437
        if self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            if self.peim.Epass==2:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep02_MBSA1_KeraG")
            if self.peim.Epass==5:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep05_MBSA1_KeraG")
            if self.peim.Epass==10:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep10_MBSA1_KeraG")
            if self.peim.Epass==20:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep20_MBSA1_KeraG") 

    def get_x_EF_and_hn_of_AlKaXPS(self):
        self.hn=1486.65
        if self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            if self.peim.Epass==100:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_AlKa_Ep100_MBSA1_KeraG")

    def get_x_EF_and_hn_of_MgKaXPS(self):
        self.hn=1253.6
        if self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            if self.peim.Epass==100:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_MgKa_Ep100_MBSA1_KeraG")

    def get_x_EF_and_variable_hn(self, event=None):
        x_EF0=None
        hn0=None
        
        # hn取得
        self.hn=float(self.hn_entry.get())
        if self.equipment_combo.get()=="MBS A-1 (G1, BL7U, UVSOR)":
            if self.peim.Epass==2:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep02_G1_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep02_G1_MBSA1_BL7U")
            if self.peim.Epass==5:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep05_G1_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep05_G1_MBSA1_BL7U")
            if self.peim.Epass==10:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep10_G1_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep10_G1_MBSA1_BL7U")
            if self.peim.Epass==20:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep20_G1_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep20_G1_MBSA1_BL7U")

        elif self.equipment_combo.get()=="MBS A-1 (G2, BL7U, UVSOR)":
            if self.peim.Epass==2:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep02_G2_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep02_G2_MBSA1_BL7U")
            if self.peim.Epass==5:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep05_G2_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep05_G2_MBSA1_BL7U")
            if self.peim.Epass==10:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep10_G2_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep10_G2_MBSA1_BL7U")
            if self.peim.Epass==20:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep20_G2_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep20_G2_MBSA1_BL7U")

        elif self.equipment_combo.get()=="MBS A-1 (G3, BL7U, UVSOR)":
            if self.peim.Epass==2:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep02_G3_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep02_G3_MBSA1_BL7U")
            if self.peim.Epass==5:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep05_G3_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep05_G3_MBSA1_BL7U")
            if self.peim.Epass==10:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep10_G3_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep10_G3_MBSA1_BL7U")
            if self.peim.Epass==20:
                x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_variable_hn_Ep20_G3_MBSA1_BL7U")
                hn0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "hn_variable_hn_Ep20_G3_MBSA1_BL7U")

        elif self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            # hn=0-15eVの時はXeIのEFと差分を取る
            if self.hn>=0 and self.hn<=15:
                hn0=8.437
                if self.peim.Epass==2:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep02_MBSA1_KeraG")
                if self.peim.Epass==5:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep05_MBSA1_KeraG")
                if self.peim.Epass==10:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep10_MBSA1_KeraG")
                if self.peim.Epass==20:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_XeIa_Ep20_MBSA1_KeraG") 
            
            # hn=15-30eVの時はHeIのEFと差分を取る
            if self.hn>15 and self.hn<30:
                hn0=21.218
                if self.peim.Epass==2:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep02_MBSA1_KeraG")
                if self.peim.Epass==5:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep05_MBSA1_KeraG")
                if self.peim.Epass==10:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep10_MBSA1_KeraG")
                if self.peim.Epass==20:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIa_Ep20_MBSA1_KeraG")
            #hn>=30 eVのときはHeIIとの差分をとる (こんな状況はない？)
            if self.hn>=30:
                hn0=40.814
                if self.peim.Epass==2:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep02_MBSA1_KeraG")
                if self.peim.Epass==5:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep05_MBSA1_KeraG")
                if self.peim.Epass==10:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep10_MBSA1_KeraG")
                if self.peim.Epass==20:
                    x_EF0, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_HeIIa_Ep20_MBSA1_KeraG")
        
        # EF計算
        try:
            self.x_EF = np.round(x_EF0 + (self.hn - hn0), ORDER_X)
        except:
            pass # errorの場合どうせこのあとmesasgeboxが出るのでここでは説明しない。


    def get_x_EF_and_hn_of_2PPE(self):
        if self.equipment_combo.get()=="MBS A-1 (Kera G, IMS)/General text":
            self.nm=float(self.hn_2PPE_entry.get())
            self.hn=1240/self.nm
            if self.peim.Epass==10:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_2PPE_EP10_MBSA1_KeraG")
            if self.peim.Epass==5:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_2PPE_EP05_MBSA1_KeraG")
            if self.peim.Epass==2:
                self.x_EF, _ = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "EF_2PPE_EP02_MBSA1_KeraG")
        
        if self.f_checkbox.get()==False and self.sh_checkbox.get()==False and self.th_checkbox.get()==True:
            pass
    
    def get_x_EF_and_hn_of_2PPE_entry(self, event=None):
        self.get_x_EF_and_hn_of_2PPE()

    def one_photon_buttons_callback(self, function):
        # flagの初期化
        self.flag_swap_image_xy_axes=False
        self.flag_reverse_image_y_axis=False
        self.flag_reverse_image_x_axis=True
        self.peim.kh=None
        self.peim.VL=None
        self.peim.VL_offseted=None
        self.SECO=None
        # 真空準位基準EFのためのパラメータ取得
        if self.switch_value_VL.get():
            self.SECO=float(self.SECO_entry.get())
        
        self.x_EF = None # フェルミ準位初期化
        function() # kinetic energy at fermi level を取
        
        # print('test', self.x_EF)
        if self.x_EF is None:
            messagebox.showerror('Error!',
                                'The kinetic energy at the Fermi level could not be found.\nPlease check:\n(i) the "Equipment" combo box in the "PES Image" window, and\n(ii) the entry boxes in both the "PES Image" and "Setting" windows.')

        try:
            self.Vsample=float(self.Vsample_entry.get()) # sample bias
        except ValueError:
            messagebox.showerror('Error!',
                                'The Supplied bias of a sample could not be found.'
                                'Please check the "Supplied Bias" entry box.')
        
        print("---Ek-EB変換---")
        # offsetのかけ忘れ防止のためoffsetイベント
        self.update_offset_event()

        # convert Ek to EB_EF and/or EB_VL
        print(f"Epass: {self.peim.Epass}\tPhoton Energy: {self.hn}\tFermi level: {self.x_EF}")
        print(f"Vsample: {self.Vsample}\tSECO: {self.SECO_entry.get()}")
        print(f"Ek Offset: {self.x_offset}\tY Offset: {self.y_offset}")
        
        self.peim.convert_axis_in_one_photon_process(self.hn, self.Vsample, self.x_EF, SECO=self.SECO, 
                                                     VL_conversion=self.switch_value_VL.get(), 
                                                     kh_conversion=self.switch_value_angkhconversion.get())
        # print(self.peim.kh)
        # EDC用にそれぞれのimported dataも軸変換
        self.x_offseted_paths = self.peim.EF_offseted_paths

        # plot用 x軸更新
        if self.switch_value_VL.get(): # VL
            self.WF=self.SECO-self.Vsample-(self.x_EF-self.hn) # 5V印加したときのSECO
            self.x=self.peim.VL
            self.x_offseted=self.peim.VL_offseted
            # EDC用にそれぞれのimported dataも軸変換
            self.x_offseted_paths = self.peim.VL_offseted_paths
        else: # EF
            self.x=self.peim.EF
            self.x_offseted=self.peim.EF_offseted
            self.x_offseted_paths=self.peim.EF_offseted_paths
        # x関連の変数を更新
        self.x_min=np.amin(self.x_offseted)
        self.x_max=np.amax(self.x_offseted)
        
        # plot用 y軸更新
        if self.switch_value_angkhconversion.get()==True and self.peim.y_label==r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$":
            self.y=copy.deepcopy(self.peim.kh)
            self.y_offseted=copy.deepcopy(self.peim.kh_offseted)
            self.z_image=copy.deepcopy(self.peim.z_kh_offseted)
            self.z_image_paths=copy.deepcopy(self.peim.z_kh_paths)
            self.flag_swap_image_xy_axes=True
            self.flag_reverse_image_y_axis=True
        else:
            self.y=copy.deepcopy(self.peim.y)
            self.y_offseted=copy.deepcopy(self.y_offseted)
            self.z_image=copy.deepcopy(self.peim.z)
            self.z_image_paths=copy.deepcopy(self.peim.z_paths)
            self.flag_swap_image_xy_axes=False
            self.flag_reverse_image_y_axis=False
            
        # y更新
        self.y_min=np.amin(self.y_offseted)
        self.y_max=np.amax(self.y_offseted)
        self.y_step=abs(self.y[0]-self.y[1])


        # entrybox更新
        # YDC切り出し範囲
        self.x_slice_min_entry.delete(0, customtkinter.END)
        self.x_slice_max_entry.delete(0, customtkinter.END)
        self.x_slice_center_entry.delete(0, customtkinter.END)
        self.x_slice_width_entry.delete(0, customtkinter.END)
        self.x_slice_min_entry.insert(0, self.x_min)
        self.x_slice_max_entry.insert(0, self.x_max)
        self.x_slice_center_entry.insert(0, np.round((self.x_min+self.x_max)/2, ORDER_X))
        self.x_slice_width_entry.insert(0, np.round(abs(self.x_max-self.x_min), ORDER_X))
        # Sliderの初期化と更新
        self.x_slice_max_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_min_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_center_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_width_slider.configure(from_=self.x_step, to=self.x_max-self.x_min)
        self.x_slice_max_slider.set(self.x_max)
        self.x_slice_min_slider.set(self.x_min)
        self.x_slice_center_slider.set(np.round((self.x_min+self.x_max)/2, ORDER_X))
        self.x_slice_width_slider.set(np.round(abs(self.x_max-self.x_min), ORDER_X))
        
        # EDC切り出し範囲
        self.y_slice_min_entry.delete(0, customtkinter.END)
        self.y_slice_max_entry.delete(0, customtkinter.END)
        self.y_slice_center_entry.delete(0, customtkinter.END)
        self.y_slice_width_entry.delete(0, customtkinter.END)
        self.y_slice_min_entry.insert(0, self.y_min)
        self.y_slice_max_entry.insert(0, self.y_max)
        self.y_slice_center_entry.insert(0, np.round((self.y_min+self.y_max)/2, ORDER_Y))
        self.y_slice_width_entry.insert(0, np.round(abs(self.y_max-self.y_min), ORDER_Y))
        # Sliderの初期化と更新
        self.y_slice_max_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_min_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_center_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_width_slider.configure(from_=self.y_step, to=self.y_max-self.y_min)
        self.y_slice_max_slider.set(self.y_max)
        self.y_slice_min_slider.set(self.y_min)
        self.y_slice_center_slider.set(np.round((self.y_min+self.y_max)/2, ORDER_Y))
        self.y_slice_width_slider.set(np.round(abs(self.y_max-self.y_min), ORDER_Y))

        # image範囲
        self.x_lim_min_entry.delete(0, customtkinter.END)
        self.x_lim_max_entry.delete(0, customtkinter.END)
        self.x_lim_min_entry.insert(0, self.x_min)
        self.x_lim_max_entry.insert(0, self.x_max)
        self.y_lim_min_entry.delete(0, customtkinter.END)
        self.y_lim_max_entry.delete(0, customtkinter.END)
        self.y_lim_min_entry.insert(0, self.y_min)
        self.y_lim_max_entry.insert(0, self.y_max)     
        # EDCの範囲更新
        self.x_edc_max_entry.delete(0, customtkinter.END)
        self.x_edc_min_entry.delete(0, customtkinter.END)
        self.x_edc_max_entry.insert(0, self.x_max)
        self.x_edc_min_entry.insert(0, self.x_min)
        
        # EDCsエントリーボックス初期化
        self.edcs_stack_x_lim_min_entry.delete(0, customtkinter.END)
        self.edcs_stack_x_lim_max_entry.delete(0, customtkinter.END)
        self.edcs_stack_y_lim_min_entry.delete(0, customtkinter.END)
        self.edcs_stack_y_lim_max_entry.delete(0, customtkinter.END)

        # image range調整->image plot
        self.update_range_event()

        # plot edc
        self.generate_an_edc() # EDCを作成
        # backgroundが定義されていたらバックグラウンド処理する
        if self.background_intensity_edc_ydc_entry.get() != '':
            self.subtract_background_intensity_of_EDC_YDC()
        self.plot_edc() #plot初期化->plot

        # 前回の設定をひきづりたい
        self.edc_pltctrl.ax.set_yscale(self.yscale_edc)
        self.update_edc_z_range_event()
        self.edc_pltctrl.ax.legend(loc='best', fontsize='small') # 凡例を表示
        if self.legend_loc_edc==None:
            self.edc_pltctrl.ax.get_legend().remove()
        self.update_edc_legend()
        self.edc_pltctrl.update_canvas()

        # EDC y scale, legend表示 更新
        self.toggle_plot_visibility()
        self.edc_pltctrl.ax.legend(loc='best', fontsize='small') # 凡例を表示
        if self.legend_loc_edc==None:
            self.edc_pltctrl.ax.get_legend().remove()
        self.update_edc_legend() # 凡例を更新
        self.edc_pltctrl.update_canvas()

        # EDCs stacking 初期化
        if hasattr(self, 'edcs_pltctrl') and self.edcs_pltctrl is not None:
            plt.close(self.edcs_pltctrl.fig)
        self.edcs_stack_pltctrl=PlotControl(title=f"{self.filename_edcs_entry.get()}", x_label=self.peim.x_label, y_label="Intensity (cps)", figsize_w=EDCS_WIDTH, figsize_h=EDCS_HEIGHT, fontsize=12, plt_interaction=False)
        if self.edcs_ystep_entry.get()!='' and self.edcs_z_offset_entry.get()!='':
            ystep_number_old=int( float(self.edcs_ystep_entry.get()) / abs(self.peim.y[0]-self.peim.y[1]) )
            ystep_new=float( abs(self.y[0]-self.y[1])*ystep_number_old )
            self.edcs_ystep_entry.delete(0, customtkinter.END)
            self.edcs_ystep_entry.insert(0, ystep_new)
            self.generate_edcs_stack()
            self.edcs_stack_pltctrl.change_legend_position(mode=self.legend_loc_edcs, fontsize='small')

        # canvas更新
        self.edcs_stack_pltctrl.update_canvas()
        self.edc_pltctrl.update_canvas()
        
        # filename初期化
        self.filename_image_entry.delete(0, customtkinter.END)
        # filename更新
        # if self.peim.VL is None:
        #     self.filename_image_entry.insert(0, f"{self.peim.filename.replace('.txt', '_EF.txt')}")
        # else:
        #     self.filename_image_entry.insert(0, f"{self.peim.filename.replace('.txt', '_VL.txt')}")
        self.filename_image_entry.insert(0, self.peim.filename)

#################################################################################################
    def generate_image_plot_frame(self, columnspan):
        # Image Plot Frame ##########
        #大枠フレーム
        self.image_plot_frame = customtkinter.CTkScrollableFrame(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT) #スクロールバーつき 
        # self.image_plot_frame = customtkinter.CTkFrame(self) # スクロールバーなし
        self.image_plot_frame.grid(row=3, column=0, padx=(10,10), pady=(0, 10), sticky="ew", columnspan=columnspan)
        # # フレームのデフォルトの背景色を取得

        # tabで図を切り替える (作成途中)
        """
        self.edc_ydc_tabview = customtkinter.CTkTabview(master=self.image_plot_frame, fg_color='gray20', width=220)
        self.edc_ydc_tabview.grid(row=0, column=0, columnspan=1, padx=10, pady=(0,10), sticky="new")
        self.edc_ydc_tabview.add("Ek")
        self.edc_ydc_tabview.add("EF")
        self.edc_ydc_tabview.add("VL")
        """

        # Image Frame #
        x= np.zeros(2)
        y= copy.deepcopy(x)
        z= np.zeros((2,2))
        self.peim_pltctrl = ImagePlotControl(x, y, z,
                                            title="An image will be shown here.\n", 
                                            colormap=self.colormap, 
                                            x_label=self.x_label, y_label=self.y_label, z_label="Intensity (cps)", 
                                            figsize_w=IMAGE_WIDTH, figsize_h=IMAGE_HEIGHT, 
                                            scientific_zscale=True)
        
        self.peim_canvas = FigureCanvasTkAgg(self.peim_pltctrl.fig, master=self.image_plot_frame)
        # get_frameが出来ないので暫定的にtab_dictを行う。
        # self.image_plot_frame_ek = self.edc_ydc_tabview._tab_dict["Ek"] # self.edc_ydc_tabview.get_frame("Ek")
        self.peim_canvas = FigureCanvasTkAgg(self.peim_pltctrl.fig, master=self.image_plot_frame)
        self.peim_canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=(5, 10), sticky="new", rowspan=1)
        self.image_plot_frame.canvas = self.peim_canvas


        # Range frame #############
        self.range_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.range_frame.grid(row=0, column=1, padx=(10, 10), pady=(5, 10), sticky="ew")
        # title
        self.range_label = customtkinter.CTkLabel(self.range_frame, text='XY Range', font=self.fonts)
        self.range_label.grid(row=0, column=0, padx=10, pady=(10,10), sticky="ew", columnspan=2)

        # 最大エネルギーラベル
        x_lim_max_label = customtkinter.CTkLabel(self.range_frame, text='Max Energy')
        x_lim_max_label.grid(row=1, column=0, padx=(10, 10), pady=(0,5), sticky="ew")
        self.x_lim_max_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_lim_max_entry.grid(row=1, column=1, padx=(10, 10), pady=(0,5), sticky="ew")
        self.x_lim_max_entry.bind("<Return>", self.update_range_event)      
        # 最小エネルギーラベル
        x_lim_min_label = customtkinter.CTkLabel(self.range_frame, text='Min Energy')
        x_lim_min_label.grid(row=2, column=0, padx=(10, 10), pady=(0,5), sticky="ew")
        self.x_lim_min_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="eV", width=80, font=self.fonts)
        self.x_lim_min_entry.grid(row=2, column=1, padx=(10, 10), pady=(0,5), sticky="ew")
        self.x_lim_min_entry.bind("<Return>", self.update_range_event)

        # 最大yラベル
        z_lim_max_label = customtkinter.CTkLabel(self.range_frame, text='Max Y', width=120)
        z_lim_max_label.grid(row=3, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.y_lim_max_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="", width=120, font=self.fonts)
        self.y_lim_max_entry.grid(row=3, column=1, padx=10, pady=(0,5), sticky="ew")
        self.y_lim_max_entry.bind("<Return>", self.update_range_event)
        # 最小yラベル
        y_lim_min_label = customtkinter.CTkLabel(self.range_frame, text='Min Y')
        y_lim_min_label.grid(row=4, column=0, padx=(10, 10), pady=(0,5), sticky="ew")
        self.y_lim_min_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="", width=80, font=self.fonts)
        self.y_lim_min_entry.grid(row=4, column=1, padx=(10, 10), pady=(0,5), sticky="ew")
        self.y_lim_min_entry.bind("<Return>", self.update_range_event)

        x_offset_label = customtkinter.CTkLabel(self.range_frame, text='Offset Ek (not Eb!)')
        x_offset_label.grid(row=6, column=0, padx=10, pady=(0,5), sticky="ew")
        self.x_offset_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_offset_entry.grid(row=6, column=1, padx=10, pady=(0,5), sticky="ew") 
        self.x_offset_entry.bind("<Return>", self.update_offset_event)
        # y offset
        y_offset_label = customtkinter.CTkLabel(self.range_frame, text='Offset Y (not k//!)')
        y_offset_label.grid(row=7, column=0, padx=10, pady=(0,33), sticky="ew")
        self.y_offset_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="", width=120, font=self.fonts)
        self.y_offset_entry.grid(row=7, column=1, padx=10, pady=(0,33), sticky="ew") 
        self.y_offset_entry.bind("<Return>", self.update_offset_event)


    def generate_color_tunner_frame(self):
        # カラーチューナーラベル ##################
        self.color_tunner_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.color_tunner_frame.grid(row=0, column=2, padx=(0,10), pady=(5, 10), sticky="ew")
        #title
        color_tunner_label = customtkinter.CTkLabel(self.color_tunner_frame, text='Color Tunner', font=self.fonts)
        color_tunner_label.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew", columnspan=2)
        # カラーマップラベル
        colormap_label = customtkinter.CTkLabel(self.color_tunner_frame, text='Color Map')
        colormap_label.grid(row=1, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        # 取り込みモード選択
        self.colormap_combo = customtkinter.CTkComboBox(self.color_tunner_frame, font=self.fonts, command=self.update_colormap, 
                                                    #values=[COLORMAP, "hot", "seismic", "plasma", "rainbow", "pwr", "PuOrYl", "inferno"]
                                                    values=[
                                                    COLORMAP, 'YlGnBu_r', 'coolwarm', 'bwr', 'magma', 'Blues', 'Purples', 'Reds', 'bone_r', 'RdYlBu_r', 'Spectral_r', 'rainbow', 'cividis', 'plasma', 'viridis',
                                                    'gist_earth_r', 'gist_gray_r', 'gist_grey', 'gist_heat', 'gist_ncar', 'gist_rainbow', 'gist_stern_r', 'gist_yarg', 
                                                    'gist_yerg','GnBu', 'BuGn', 'BuPu', 'CMRmap_r', 'Grays', 'Greens', 'Greys', 'OrRd', 'Oranges', 'PuBu', 'PuBuGn', 'PuRd', 'RdPu','RdYlGn', 'YlGn', 'YlOrBr', 'YlOrRd', 
                                                    'afmhot', 'binary', 'ocean', 'copper', 'gnuplot2', 'gray', 'grey', 'hot', 'hsv', 'inferno', 'jet', 'pink', 'seismic', 'spring', 
                                                    'summer', 'terrain','turbo', 'twilight','twilight_shifted', 'winter', 'cool', 'autumn', 'brg', 'gnuplot', 'BrBG', 'PRGn', 'PiYG', 'PuOr', 'RdGy', 'RdBu', 'nipy_spectral'
                                                    ])
        self.colormap_combo.grid(row=1, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        # 色反転ボタン
        self.reverse_colormap_button = customtkinter.CTkButton(self.color_tunner_frame, command=self.reverse_colormap_buttom_callback, text="Reverse", font=self.fonts, width=120)
        self.reverse_colormap_button.grid(row=2, column=1, padx=(0,10), pady=(0,10), sticky="ew")
        #title
        color_tunner_label = customtkinter.CTkLabel(self.color_tunner_frame, text='Z Range', font=self.fonts)
        color_tunner_label.grid(row=3, column=0, padx=10, pady=(0,5), sticky="ew", columnspan=2)
        # 最大光電子強度EntryBox
        customtkinter.CTkLabel(self.color_tunner_frame, text='Max Intensity', width=120).grid(row=4, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.z_lim_max_entry = customtkinter.CTkEntry(self.color_tunner_frame, placeholder_text="cps", font=self.fonts, width=120)
        self.z_lim_max_entry.grid(row=4, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.z_lim_max_entry.bind("<Return>", self.update_z_range_event)
        # 最大光電子強度 slider
        self.z_lim_max_slider = customtkinter.CTkSlider(self.color_tunner_frame, from_=0, to=100, command=self.update_z_range_slider_event, width=120)
        self.z_lim_max_slider.set(100)
        self.z_lim_max_slider.grid(row=5, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)
        # 最小光電子強度EntryBox
        customtkinter.CTkLabel(self.color_tunner_frame, text='Min Intensity', width=120).grid(row=6, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.z_lim_min_entry = customtkinter.CTkEntry(self.color_tunner_frame, placeholder_text="cps", font=self.fonts, width=120)
        self.z_lim_min_entry.grid(row=6, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.z_lim_min_entry.bind("<Return>", self.update_z_range_event)
        # 最小光電子強度 slider
        self.z_lim_min_slider = customtkinter.CTkSlider(self.color_tunner_frame, from_=0, to=100, command=self.update_z_range_slider_event, width=120)
        self.z_lim_min_slider.set(0)
        self.z_lim_min_slider.grid(row=7, column=1, padx=(0,10), pady=(0,20), sticky="ew", columnspan=1)
        
    def generate_image_button_frame(self):
        # 軸反転 ######################################
        self.axis_reverse_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.axis_reverse_frame.grid(row=0, column=3, padx=(0,10), pady=(5,10), sticky="ew", columnspan=1)
        
        for i in range(1):
            customtkinter.CTkLabel(self.axis_reverse_frame, text='').grid(row=i, column=0, pady=(0,2.5))

        # Full Range
        button=customtkinter.CTkButton(self.axis_reverse_frame, text="(D)Replace Dead Pixel", command=None, width=90, font=self.fonts)
        button.grid(row=2, column=0, padx=(0,10), pady=(0,5), sticky="e", columnspan=2)

        self.fullrange_checkbox = customtkinter.CTkButton(self.axis_reverse_frame, text="Full Range", command=self.autorange_button_callback, width=90, font=self.fonts)
        self.fullrange_checkbox.grid(row=3, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        
        button=customtkinter.CTkButton(self.axis_reverse_frame, command=self.reverse_x_axis_button_callback, text="Reverse X", font=self.fonts, width=90)
        button.grid(row=4, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        button=customtkinter.CTkButton(self.axis_reverse_frame, command=self.reverse_y_axis_button_callback, text="Reverse Y", font=self.fonts, width=90)
        button.grid(row=5, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        button=customtkinter.CTkButton(self.axis_reverse_frame, command=self.swap_image, text="Swap XY", font=self.fonts, width=90)
        button.grid(row=6, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        customtkinter.CTkLabel(self.axis_reverse_frame, text='Output Filename', width=120).grid(row=7, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.filename_image_entry = customtkinter.CTkEntry(self.axis_reverse_frame, placeholder_text='Image Filename', font=self.fonts, width=120)
        self.filename_image_entry.grid(row=7, column=1, padx=(0, 10), pady=(0,5), sticky="ew")

        button=customtkinter.CTkButton(self.axis_reverse_frame, command=self.save_peim_image_data_button_callback, text="Save Image", font=self.fonts, width=90)
        button.grid(row=8, column=1, padx=(0, 10), pady=(0,20), sticky="ew")
        
    def save_peim_image_data_button_callback(self):
        if self.peim.EF is None:
            axis_list=['Ek']
        elif self.peim.VL is None:
            axis_list=['EF', 'Ek']
        elif self.peim.VL is not None:
            axis_list=['VL', 'EF', 'Ek']

        for axis in axis_list:        
           self.peim.save_data(data_type='image', axis=axis, filename=self.filename_image_entry.get())

    def update_range_event(self, event=None):
        # imageの初期化
        self.peim_pltctrl.delete_image()
        
        """xとyの表示範囲を変更"""
        try:
            # entry boxから値を取得
            x_lim_min = float(self.x_lim_min_entry.get())
            x_lim_max = float(self.x_lim_max_entry.get())
            y_lim_min = float(self.y_lim_min_entry.get())
            y_lim_max = float(self.y_lim_max_entry.get())
        
        except ValueError:
            print("Invalid value")

        # plot image
           
        # kpを計算していないとき
        if not self.flag_swap_image_xy_axes:
            self.peim_pltctrl.plot_image(self.x_offseted, self.y_offseted, self.z_image, 
                                        new_x_label=self.peim.x_label, new_y_label=self.peim.y_label)
            # range設定
            self.peim_pltctrl.set_range(x_lim_min, x_lim_max, y_lim_min, y_lim_max)
        else: # kp計算しているとき
            self.peim_pltctrl.plot_image(self.y_offseted, self.x_offseted, self.z_image.T,
                                        new_x_label=self.peim.y_label, new_y_label=self.peim.x_label)
            # range設定
            self.peim_pltctrl.set_range(y_lim_min, y_lim_max, x_lim_min, x_lim_max)   
            self.peim_pltctrl.ax.invert_yaxis()
            # x軸はkpのためを入れ替えておく
            self.peim_pltctrl.ax.invert_xaxis()
        
        if self.flag_reverse_image_x_axis: # EFのときx軸反転
            self.peim_pltctrl.ax.invert_xaxis()

        # 再描画
        self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)
        self.edc_pltctrl.fig.canvas.draw()
  
    def update_offset_event(self, event=None):
        """xとyにoffsetを与える"""
        # エントリーボックスの値を取得
        print("offset処理")
        x_offset =float(self.x_offset_entry.get())
        y_offset =float(self.y_offset_entry.get())
        x_lim_min=float(self.x_lim_min_entry.get())
        x_lim_max=float(self.x_lim_max_entry.get())
        y_lim_min=float(self.y_lim_min_entry.get())
        y_lim_max=float(self.y_lim_max_entry.get())

        # y offset (kp変換していた場合オフセットをかけてはいけないため場合分け)
        if self.peim.kh is not None: # kp変換していた場合
            # 警告文を表示
            title = "Warning"
            sentence = "After converting the angle to k//, you can execute the axis conversion by pressing the Enter key or clicking the button in\"Axes Conversion\".\nUsing the X & Y offset boxes or the \"Full Range\" button leads to incorrect results."
            messagebox.showerror(title, sentence)
    
        # y offset
        self.peim.apply_offset(0, y_offset, y_axis="Deg") # offsetをかける
        self.y_offseted=self.peim.y_offseted


        # x offset
        if self.peim.EF is None: # 運動エネルギー
            self.peim.apply_offset(x_offset, 0, x_axis="Ek") # offsetをかける
            self.x_offseted=self.peim.x_offseted
            self.x_offseted_paths=self.peim.x_offseted_paths

        elif self.peim.VL is None: #フェルミ準位基準の結合エネルギー
            self.peim.apply_offset(x_offset, 0, x_axis="EB_EF") # offsetをかける
            self.x_offseted=self.peim.EF_offseted
            self.x_offseted_paths=self.peim.EF_offseted_paths

        else: # VL基準の結合エネルギー
            self.peim.apply_offset(x_offset, 0, x_axis="EB_VL") # offsetをかける
            self.x_offseted=self.peim.VL_offseted
            self.x_offseted_paths=self.peim.VL_offseted_paths

        # 値を取得
        self.x_min=np.amin(self.x_offseted)
        self.x_max=np.amax(self.x_offseted)
        self.y_min=np.amin(self.y_offseted)
        self.y_max=np.amax(self.y_offseted)

        # エントリーボックスを修正
        self.x_lim_min_entry.delete(0, customtkinter.END)
        self.x_lim_max_entry.delete(0, customtkinter.END)
        self.y_lim_min_entry.delete(0, customtkinter.END)
        self.y_lim_max_entry.delete(0, customtkinter.END)

        if self.peim.EF is None: # 運動エネルギー
            self.x_lim_min_entry.insert(0, x_lim_min+x_offset-self.x_offset) # 以前のoffsetとの差をみるため、x_offset-self.x_offset
            self.x_lim_max_entry.insert(0, x_lim_max+x_offset-self.x_offset)
        else: # 結合エネルギーのときはoffsetのかけ方が逆転する
            self.x_lim_min_entry.insert(0, x_lim_min-(x_offset-self.x_offset)) # 以前のoffsetとの差をみるため、x_offset-self.x_offset
            self.x_lim_max_entry.insert(0, x_lim_max-(x_offset-self.x_offset))  
        self.y_lim_min_entry.insert(0, y_lim_min+y_offset-self.y_offset)
        self.y_lim_max_entry.insert(0, y_lim_max+y_offset-self.y_offset)

        # スライダーのつまみを設定
        self.x_slice_max_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_min_slider.configure(from_=self.x_min, to=self.x_max)
        self.x_slice_center_slider.configure(from_=self.x_min, to=self.x_max)
        self.y_slice_max_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_min_slider.configure(from_=self.y_min, to=self.y_max)
        self.y_slice_center_slider.configure(from_=self.y_min, to=self.y_max)


        # エントリーボックスに従ってプロット領域を修正
        self.update_range_event()

        # offset valuesの更新
        self.x_offset=x_offset
        self.y_offset=y_offset

        # edcも更新する
        self.generate_an_edc() # EDCを作成
        if self.background_intensity_edc_ydc_entry.get() != '':
            # background intensityが定義されていたらバックグラウンド処理する
            self.background_intensity_edc_ydc = float(self.background_intensity_edc_ydc_entry.get())    
            self.subtract_background_intensity_of_EDC_YDC()
        self.plot_edc() #plot初期化->plot
        self.edc_pltctrl.ax.legend(loc='best', fontsize='small') # 凡例を表示
        if self.legend_loc_edc==None:
            self.edc_pltctrl.ax.get_legend().remove()
        self.update_edc_legend() # 凡例を更新

        # エントリーボックスを修正
        self.x_edc_min_entry.delete(0, customtkinter.END)
        self.x_edc_max_entry.delete(0, customtkinter.END)
        # self.y_ydc_min_entry.delete(0, customtkinter.END)
        # self.y_ydc_max_entry.delete(0, customtkinter.END)

        if self.peim.EF is None: # 運動エネルギー
            self.x_edc_min_entry.insert(0, x_lim_min+x_offset-self.x_offset) # 以前のoffsetとの差をみるため、x_offset-self.x_offset
            self.x_edc_max_entry.insert(0, x_lim_max+x_offset-self.x_offset)
        else: # 結合エネルギーのときはoffsetのかけ方が逆転する
            self.x_edc_min_entry.insert(0, x_lim_min-(x_offset-self.x_offset)) # 以前のoffsetとの差をみるため、x_offset-self.x_offset
            self.x_edc_max_entry.insert(0, x_lim_max-(x_offset-self.x_offset))  
        # self.y_ydc_min_entry.insert(0, y_lim_min+y_offset-self.y_offset)
        # self.y_ydc_max_entry.insert(0, y_lim_max+y_offset-self.y_offset)
        # EDCの範囲更新
        self.edc_pltctrl.update_canvas()    

    def autorange_button_callback(self):
        # 初期化
        self.x_lim_min_entry.delete(0, customtkinter.END)
        self.x_lim_max_entry.delete(0, customtkinter.END)
        self.y_lim_min_entry.delete(0, customtkinter.END)
        self.y_lim_max_entry.delete(0, customtkinter.END)
        # 更新 (EntryBox)
        self.x_lim_min_entry.insert(0, self.x_min)
        self.x_lim_max_entry.insert(0, self.x_max)
        self.y_lim_min_entry.insert(0, self.y_min)
        self.y_lim_max_entry.insert(0, self.y_max)

        self.update_offset_event()

    def update_z_range_event(self, event=None):
        """zの表示範囲を変更"""
        try:
            z_lim_min = float(self.z_lim_min_entry.get())
            z_lim_max = float(self.z_lim_max_entry.get())
            
            # スライダーのつまみを設定
            self.z_lim_min_slider.set(z_lim_min)
            self.z_lim_max_slider.set(z_lim_max)

            # pltctrlに反映 (image)
            self.peim_pltctrl.set_z_range(z_lim_min, z_lim_max) # EDCプロット
            self.edc_pltctrl.update_canvas()

        except ValueError:
            print("Invalid value")

    def update_z_range_slider_event(self, event=None):
        """スライダーの値が変更されたときの処理"""
        z_lim_min = self.z_lim_min_slider.get()  # z_min スライダーの値を取得
        z_lim_max = self.z_lim_max_slider.get()  # z_max スライダーの値を取得
        # print(f"z_lim_min: {z_lim_min}, z_lim_max: {z_lim_max}")
        
        # entryboxの更新
        self.z_lim_min_entry.delete(0, customtkinter.END)
        self.z_lim_max_entry.delete(0, customtkinter.END)
        self.z_lim_min_entry.insert(0, z_lim_min)
        self.z_lim_max_entry.insert(0, z_lim_max)
        
        # entryboxの値でimageを更新
        self.update_z_range_event()

    def update_colormap(self, event=None):
        self.colormap=self.colormap_combo.get()
        self.change_image_cmap()

    def reverse_colormap_buttom_callback(self):
        # colormapを反転させる
        # "_r" が含まれているかどうかをチェック
        if "_r" in self.colormap:
            # "_r" を削除
            self.colormap = self.colormap.replace("_r", "")
        else:
            # "_r" を追加
            self.colormap = self.colormap + "_r"
        self.change_image_cmap()

    def change_image_cmap(self):    
        print(self.colormap)
        # color map変更
        self.peim_pltctrl.change_colormap(self.colormap)
        # plot
        self.update_range_event()
        self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)
        print(self.flag_reverse_image_y_axis, self.flag_swap_image_xy_axes)

    def reverse_x_axis_button_callback(self):
        self.peim_pltctrl.ax.invert_xaxis()

        self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)
        print(f"Reverse X axis")

    def reverse_y_axis_button_callback(self):
        self.peim_pltctrl.ax.invert_yaxis()

        self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)
        print(f"Reverse Y axis")

    def swap_image(self):
        # plotの初期化
        self.peim_pltctrl.delete_image()
        # 設定の更新        
        if self.flag_swap_image_xy_axes==False:
            self.flag_swap_image_xy_axes=True
        elif self.flag_swap_image_xy_axes==True:
            self.flag_swap_image_xy_axes=False
        
        self.update_range_event()
        self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame)
        print(f"Swap XY axes")

    # 2D image Slicer (Y) ###############################################
    def generate_edc_plot_frame(self):
        # EDC plot
        self.edc_pltctrl=PlotControl(title="An EDC/MDC will be shown here.", x_label=self.x_label, y_label='Intensity (cps)', figsize_w=IMAGE_WIDTH, figsize_h=IMAGE_HEIGHT*1.25, fontsize=12)
        self.edc_pltctrl.add_spectrum(0, 0, "EDC/MDC", color="white")
        self.edc_pltctrl.change_legend_position(mode="best", fontsize="small")
        self.edc_canvas = FigureCanvasTkAgg(self.edc_pltctrl.fig, master=self.image_plot_frame)
        self.edc_canvas.get_tk_widget().grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
        self.edc_pltctrl.update_canvas()

        # 2D image slicer (Y) #############
        self.twod_image_slice_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.twod_image_slice_frame.grid(row=2, column=1, padx=(10,10), pady=(0,10), sticky="ew")

        # --- CTkTabview を追加 ---
        # title
        customtkinter.CTkLabel(self.twod_image_slice_frame, text='EDC/MDC Generator', font=self.fonts, width=120).grid(row=0, column=0, padx=(0,0), pady=(10,10), sticky="ew", columnspan=2)
        # tabで切り替えることにする
        self.edc_ydc_tabview = customtkinter.CTkTabview(master=self.twod_image_slice_frame, fg_color='gray20', width=220)
        self.edc_ydc_tabview.grid(row=1, column=0, columnspan=2, padx=(0,0), pady=(0,10), sticky="new")
        self.edc_ydc_tabview.add("Y Direction (EDC)")
        self.edc_ydc_tabview.add("E Direction (MDC)")

        # EDC tab #################
        self.edc_slice_frame = self.edc_ydc_tabview.tab("Y Direction (EDC)")
        # self.edc_slice_frame.configure(fg_color='gray20', corner_radius=10)
        # Maxmum Y
        customtkinter.CTkLabel(self.edc_slice_frame, text="Max Y", width=120).grid(row=1, column=0, padx=(10,10), pady=(10,3), sticky="ew")
        self.y_slice_max_entry = customtkinter.CTkEntry(self.edc_slice_frame, placeholder_text="", width=120, font=self.fonts)
        self.y_slice_max_entry.grid(row=1, column=1, padx=(0,10), pady=(10,3), sticky="ew")
        self.y_slice_max_entry.bind("<Return>",command=self.update_y_slice_min_or_max_event)
        # slider
        self.y_slice_max_slider = customtkinter.CTkSlider(self.edc_slice_frame, from_=0, to=100, command=self.update_y_slice_min_or_max_slider_event, width=120)
        self.y_slice_max_slider.set(100)
        self.y_slice_max_slider.grid(row=2, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)
        
        # Min Y
        customtkinter.CTkLabel(self.edc_slice_frame, text="Min Y", width=120).grid(row=3, column=0, padx=(10,10), pady=(0,3), sticky="ew")
        self.y_slice_min_entry = customtkinter.CTkEntry(self.edc_slice_frame, placeholder_text="", width=120, font=self.fonts)
        self.y_slice_min_entry.grid(row=3, column=1, padx=(0,10), pady=(0,3), sticky="ew")
        self.y_slice_min_entry.bind("<Return>",command=self.update_y_slice_min_or_max_event)
        # slider
        self.y_slice_min_slider = customtkinter.CTkSlider(self.edc_slice_frame, from_=0, to=100, command=self.update_y_slice_min_or_max_slider_event, width=120)
        self.y_slice_min_slider.set(0)
        self.y_slice_min_slider.grid(row=4, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)
        
        # Center Y
        customtkinter.CTkLabel(self.edc_slice_frame, text="Center Y", width=120).grid(row=5, column=0, padx=(10,10), pady=(0,3), sticky="ew")
        self.y_slice_center_entry = customtkinter.CTkEntry(self.edc_slice_frame, placeholder_text="", width=120, font=self.fonts)
        self.y_slice_center_entry.grid(row=5, column=1, padx=(0,10), pady=(0,3), sticky="ew")
        self.y_slice_center_entry.bind("<Return>",command=self.update_y_slice_center_or_width_event)
        # slider
        self.y_slice_center_slider = customtkinter.CTkSlider(self.edc_slice_frame, from_=-15, to=15, command=self.update_y_slice_center_or_width_slider_event, width=120)
        self.y_slice_center_slider.set(0)
        self.y_slice_center_slider.grid(row=6, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)

        # Y Width
        customtkinter.CTkLabel(self.edc_slice_frame, text="Width Y", width=120).grid(row=7, column=0, padx=(10,10), pady=(0,3), sticky="ew")
        self.y_slice_width_entry = customtkinter.CTkEntry(self.edc_slice_frame, placeholder_text="", width=120, font=self.fonts)
        self.y_slice_width_entry.grid(row=7, column=1, padx=(0,10), pady=(0,3), sticky="ew")
        self.y_slice_width_entry.bind("<Return>",command=self.update_y_slice_center_or_width_event)
        # slider
        self.y_slice_width_slider = customtkinter.CTkSlider(self.edc_slice_frame, from_=0, to=30, command=self.update_y_slice_center_or_width_slider_event, width=120)
        self.y_slice_width_slider.set(30)
        self.y_slice_width_slider.grid(row=8, column=1, padx=(0,10), pady=(0,27), sticky="ew", columnspan=1)

        # YDC tab ##############
        self.ydc_slice_frame = self.edc_ydc_tabview.tab("E Direction (MDC)")
        # Maxmum X
        customtkinter.CTkLabel(self.ydc_slice_frame, text="Max Energy", width=75).grid(row=0, column=0, padx=(10,10), pady=(10,3), sticky="ew")
        self.x_slice_max_entry = customtkinter.CTkEntry(self.ydc_slice_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_slice_max_entry.grid(row=0, column=1, padx=(0,10), pady=(10,3), sticky="ew")
        self.x_slice_max_entry.bind("<Return>",command=self.update_x_slice_min_or_max_event)
        # slider
        self.x_slice_max_slider = customtkinter.CTkSlider(self.ydc_slice_frame, from_=0, to=15, command=self.update_x_slice_min_or_max_slider_event, width=120)
        self.x_slice_max_slider.set(15)
        self.x_slice_max_slider.grid(row=1, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)

        # Min
        customtkinter.CTkLabel(self.ydc_slice_frame, text="Min Energy", width=120).grid(row=2, column=0, padx=(10,10), pady=(0,3), sticky="ew")
        self.x_slice_min_entry = customtkinter.CTkEntry(self.ydc_slice_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_slice_min_entry.grid(row=2, column=1, padx=(0,10), pady=(0,3), sticky="ew")
        self.x_slice_min_entry.bind("<Return>",command=self.update_x_slice_min_or_max_event)
        # slider
        self.x_slice_min_slider = customtkinter.CTkSlider(self.ydc_slice_frame, from_=0, to=15, command=self.update_x_slice_min_or_max_slider_event, width=120)
        self.x_slice_min_slider.set(0)
        self.x_slice_min_slider.grid(row=3, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)

        # Center X
        customtkinter.CTkLabel(self.ydc_slice_frame, text="Center Energy", width=120).grid(row=4, column=0, padx=(10,10), pady=(0,3), sticky="ew")
        self.x_slice_center_entry = customtkinter.CTkEntry(self.ydc_slice_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_slice_center_entry.grid(row=4, column=1, padx=(0,10), pady=(0,3), sticky="ew")
        self.x_slice_center_entry.bind("<Return>",command=self.update_x_slice_center_or_width_event)
        # slider
        self.x_slice_center_slider = customtkinter.CTkSlider(self.ydc_slice_frame, from_=-15, to=15, command=self.update_x_slice_center_or_width_slider_event, width=120)
        self.x_slice_center_slider.set(0)
        self.x_slice_center_slider.grid(row=5, column=1, padx=(0,10), pady=(0,10), sticky="ew", columnspan=1)

        # X width
        customtkinter.CTkLabel(self.ydc_slice_frame, text="Width Energy", width=120).grid(row=6, column=0, padx=(10,10), pady=(0,3), sticky="ew")
        self.x_slice_width_entry = customtkinter.CTkEntry(self.ydc_slice_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_slice_width_entry.grid(row=6, column=1, padx=(0,10), pady=(0,3), sticky="ew")
        self.x_slice_width_entry.bind("<Return>",command=self.update_x_slice_center_or_width_event)
        # slider
        self.x_slice_width_slider = customtkinter.CTkSlider(self.ydc_slice_frame, from_=0, to=30, command=self.update_x_slice_center_or_width_slider_event, width=120)
        self.x_slice_width_slider.set(30)
        self.x_slice_width_slider.grid(row=7, column=1, padx=(0,10), pady=(0,27), sticky="ew", columnspan=1)

    def generate_edc_plot_buttons_frame(self):
        self.twod_image_slice_botton_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.twod_image_slice_botton_frame.grid(row=2, column=2, padx=(0,10), pady=(0, 10), sticky="ew")

        # title
        edc_label = customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text="XY Range", font=self.fonts)
        edc_label.grid(row=0, column=0, padx=(10,5), pady=(10,10), sticky="ew", columnspan=2)

        # Maxmum X
        x_edc_max_label = customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text="Max Energy", width=120)
        x_edc_max_label.grid(row=1, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.x_edc_max_entry = customtkinter.CTkEntry(self.twod_image_slice_botton_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_edc_max_entry.grid(row=1, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.x_edc_max_entry.bind("<Return>",command=self.update_edc_x_range_event)
        # Min X
        edc_label = customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text="Min Energy", width=120)
        edc_label.grid(row=2, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.x_edc_min_entry = customtkinter.CTkEntry(self.twod_image_slice_botton_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.x_edc_min_entry.grid(row=2, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.x_edc_min_entry.bind("<Return>",command=self.update_edc_x_range_event)

        # Maxmum Y
        z_edc_max_label = customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text="Max Intensity", width=120)
        z_edc_max_label.grid(row=3, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.z_edc_max_entry = customtkinter.CTkEntry(self.twod_image_slice_botton_frame, placeholder_text="cps", width=120, font=self.fonts)
        self.z_edc_max_entry.grid(row=3, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.z_edc_max_entry.bind("<Return>",command=self.update_edc_z_range_event)
        # Min
        edc_label = customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text="Min Intensity", width=120)
        edc_label.grid(row=4, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.z_edc_min_entry = customtkinter.CTkEntry(self.twod_image_slice_botton_frame, placeholder_text="cps", width=120, font=self.fonts)
        self.z_edc_min_entry.grid(row=4, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.z_edc_min_entry.bind("<Return>",command=self.update_edc_z_range_event)

        # full_range_button
        full_range_edc_button = customtkinter.CTkButton(self.twod_image_slice_botton_frame, command=self.autorange_button_edc_callback, text="Full Range", font=self.fonts, width=120)
        full_range_edc_button.grid(row=6, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        # background intensity
        intensity_offset_label = customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text="BG Intensity")#, width=120)
        intensity_offset_label.grid(row=5, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.background_intensity_edc_ydc_entry = customtkinter.CTkEntry(self.twod_image_slice_botton_frame, placeholder_text="cps", font=self.fonts)#, width=120)
        self.background_intensity_edc_ydc_entry.grid(row=5, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.background_intensity_edc_ydc_entry.bind("<Return>",command=self.subtract_background_intensity_of_EDC_YDC)

        change_z_scale_button = customtkinter.CTkButton(self.twod_image_slice_botton_frame, command=self.change_z_edc_scale_button_callback, text="Change Y Scale", font=self.fonts, width=120)
        change_z_scale_button.grid(row=7, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        legend_button = customtkinter.CTkButton(self.twod_image_slice_botton_frame, command=self.change_edc_legend_position_button_callback, text="Move Legend", font=self.fonts, width=120)
        legend_button.grid(row=6, column=0, padx=(10,10), pady=(0,5), sticky="ew")

        customtkinter.CTkLabel(self.twod_image_slice_botton_frame, text='Output Filename', width=120).grid(row=9, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.filename_edc_entry = customtkinter.CTkEntry(self.twod_image_slice_botton_frame, placeholder_text='EDC Filename', font=self.fonts, width=120)
        self.filename_edc_entry.grid(row=9, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        save_EDC_data_button= customtkinter.CTkButton(self.twod_image_slice_botton_frame, command=self.save_edc_data_button_callback, text="Save EDC/MDC", font=self.fonts, width=120)
        save_EDC_data_button.grid(row=10, column=1, padx=(0,10), pady=(0,20), sticky="ew")

    def subtract_background_intensity_of_EDC_YDC(self, event=None):
        # background2回目以降はlineの初期化
        if self.peim.z_edc_offseted is not None:
            # lineを消す
            self.edc_pltctrl.remove_line_spectrum(-1)
            self.edc_pltctrl.remove_line_spectrum(-1)

        # background 処理
        self.background_intensity_edc_ydc=float(self.background_intensity_edc_ydc_entry.get())
        self.peim.subtract_background_intensity(self.background_intensity_edc_ydc)

        self.edc_pltctrl.add_spectrum(self.x_offseted, self.peim.z_edc_offseted, "BG Subtracted", 
                                    color='orangered', scatter=False, linewidth=2)
        self.edc_pltctrl.add_spectrum([np.amin(self.x_offseted), np.amax(self.x_offseted)], [self.background_intensity_edc_ydc, self.background_intensity_edc_ydc], "BG", 
                                    color='black', scatter=False, linewidth=1, linestyle="--")

        # print(self.edc_pltctrl.line)

        self.update_edc_x_range_event()
        self.update_edc_z_range_event()
        if self.yscale_edc=='log':
            self.show_log_yscale_edc()

        # legend表示
        self.reset_all_edc_setting_values()
        self.initialize_edc_setting_values()
        self.toggle_plot_visibility()
        self.update_edc_legend() # 凡例を更新
        self.edc_pltctrl.ax.legend(loc='best', fontsize='small') # 凡例を表示
        if self.legend_loc_edc==None:
            self.edc_pltctrl.ax.get_legend().remove()
        self.edc_pltctrl.update_canvas()
        

    def update_y_slice_min_or_max_event(self, event=None):
        self.y_slice_center_entry.delete(0, customtkinter.END)
        self.y_slice_width_entry.delete(0, customtkinter.END)

        y_slice_min=float(self.y_slice_min_entry.get())
        y_slice_max=float(self.y_slice_max_entry.get())

        # 入力が最大・最小値を超えている場合は最大・最小値で置換
        if y_slice_min <= self.y_min:
            y_slice_min=self.y_min
            self.y_slice_min_entry.delete(0, customtkinter.END)
            self.y_slice_min_entry.insert(0, y_slice_min)
        if y_slice_max > self.y_max:
            y_slice_max=self.y_max
            self.y_slice_max_entry.delete(0, customtkinter.END)
            self.y_slice_max_entry.insert(0, y_slice_max)

        y_slice_center=np.round((y_slice_min+y_slice_max)/2,ORDER_Y)
        y_slice_width=np.round(abs(y_slice_max-y_slice_min),ORDER_Y)

        self.y_slice_center_entry.insert(0,y_slice_center)
        self.y_slice_width_entry.insert(0,y_slice_width)

        # スライダーのつまみを設定
        self.y_slice_max_slider.set(y_slice_max)
        self.y_slice_min_slider.set(y_slice_min)
        self.y_slice_center_slider.set(y_slice_center)
        self.y_slice_width_slider.set(y_slice_width)

        # EDCを生成
        self.generate_an_edc()
        self.plot_edc()
        self.edc_pltctrl.ax.set_yscale(self.yscale_edc)
        self.update_edc_x_range_event()
        self.update_edc_z_range_event()
        self.edc_pltctrl.change_legend_position(mode=self.legend_loc_edc, fontsize="small")
        

    def update_y_slice_center_or_width_event(self, event=None):
            self.y_slice_min_entry.delete(0, customtkinter.END)
            self.y_slice_max_entry.delete(0, customtkinter.END)
            y_slice_min=float(self.y_slice_center_entry.get())-float(self.y_slice_width_entry.get())/2
            y_slice_max=float(self.y_slice_center_entry.get())+float(self.y_slice_width_entry.get())/2
            
            # out of rangeの時の処理
            if y_slice_min<=self.y_min:
                y_slice_min=self.y_min
                y_slice_max=self.y_min+float(self.y_slice_width_entry.get())
            elif y_slice_max>=self.y_max:
                y_slice_max=self.y_max
                y_slice_min=y_slice_max-float(self.y_slice_width_entry.get())
           
            # entryboxの更新
            self.y_slice_min_entry.insert(0, np.round(y_slice_min,10))
            self.y_slice_max_entry.insert(0, np.round(y_slice_max,10))
            self.update_y_slice_min_or_max_event()

    def update_y_slice_min_or_max_slider_event(self, event=None):
        """スライダーの値が変更されたときの処理"""
        y_slice_max = self.y_slice_max_slider.get()  # スライダーの値を取得
        y_slice_min = self.y_slice_min_slider.get()
        
        # entryboxの更新
        self.y_slice_max_entry.delete(0, customtkinter.END)
        self.y_slice_min_entry.delete(0, customtkinter.END)
        self.background_intensity_edc_ydc_entry.delete(0, customtkinter.END)

        self.y_slice_max_entry.insert(0, y_slice_max)
        self.y_slice_min_entry.insert(0, y_slice_min)

        # entryboxの値でimageを更新 
        self.update_y_slice_min_or_max_event()

    def update_y_slice_center_or_width_slider_event(self, event=None):
        self.y_slice_min_entry.delete(0, customtkinter.END)
        self.y_slice_max_entry.delete(0, customtkinter.END)
        self.background_intensity_edc_ydc_entry.delete(0, customtkinter.END)
        y_slice_min=float(self.y_slice_center_slider.get())-float(self.y_slice_width_slider.get())/2
        y_slice_max=float(self.y_slice_center_slider.get())+float(self.y_slice_width_slider.get())/2
        # out of rangeの時の処理
        if y_slice_min<=self.y_min:
            y_slice_min=self.y_min
            y_slice_max=self.y_min+float(self.y_slice_width_slider.get())
        elif y_slice_max>=self.y_max:
            y_slice_max=self.y_max
            y_slice_min=y_slice_max-float(self.y_slice_width_slider.get())
        # entryboxの更新
        self.y_slice_min_entry.insert(0, np.round(y_slice_min, ORDER_Y))
        self.y_slice_max_entry.insert(0, np.round(y_slice_max, ORDER_Y))
        self.update_y_slice_min_or_max_event()

    def generate_an_edc(self):
        self.peim.z_ydc=None
        # 更新した値を取得
        print("---2D Image Slice (Y direction) ---")
        self.y_slice_min=float(self.y_slice_min_entry.get())
        self.y_slice_max=float(self.y_slice_max_entry.get())
        print(f"切り出し最小値{self.y_slice_min}, 切り出し最大値{self.y_slice_max}")

        self.z_edc_paths=[]

        # EDC作成
        # 入力したすべてのファイルのEDCを作成
        for i in range(len(self.peim.z_paths)):
            self.z_edc_paths.append(self.peim.generate_an_edc(self.z_image_paths[i], self.y_offseted, 
                                                                self.y_slice_min, self.y_slice_max, 
                                                                mode="return"))
        # 平均処理している場合の処理
        if self.peim.z_sekisan_flag:
            self.peim.generate_an_edc(self.z_image, self.y_offseted, 
                                      self.y_slice_min, self.y_slice_max, 
                                      mode="edc")
            self.z_edc_offseted=self.peim.z_edc
        else:
            self.z_edc_offseted=self.z_edc_paths[-1]

        self.edc_pltctrl.update_canvas()

        # filenameの更新
        self.filename_edc_entry.delete(0, customtkinter.END)
        if self.y_slice_min==self.y_min and self.y_slice_max==self.y_max:
            filename=self.peim.filename.replace('.txt', '_fEDC.txt')
        else:
            filename=self.peim.filename.replace('.txt', '_EDC.txt')
        # 軸ごとにfilenameを変える
        # if self.peim.EF is None:
        self.filename_edc_entry.insert(0, filename)
        # elif self.peim.VL is None:
        #     self.filename_edc_entry.insert(0, f"{filename.replace('.txt', '_EF.txt')}")
        # elif self.peim.VL is not None:
        #     self.filename_edc_entry.insert(0, f"{filename.replace('.txt', '_VL.txt')}")

    def plot_edc(self):
        # legend作成
        if self.peim.y_label=="Position (mm)":
            self.label_edc=f"From {np.round(self.y_slice_min,2)} mm\nto {np.round(self.y_slice_max,2)} mm"
        elif self.peim.y_label=="Angle (Degrees)":
            self.label_edc=f"From {np.round(self.y_slice_min,2)} deg\nto {np.round(self.y_slice_max,2)} deg"
        elif self.peim.y_label==r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$":
            self.label_edc=f"From {np.round(self.y_slice_min, 2)} "+r"$\mathrm{\AA^{-1}}$"+f"\nto {np.round(self.y_slice_max, 2)} "+r"$\mathrm{\AA^{-1}}$"

        # plotting
        self.edc_pltctrl.clear_plot() # plotの初期化
        self.edc_pltctrl.line=[] # lineの初期化

        # 読み込んだスペクトルをプロット
        for i in range(len(self.peim.path_lst)):
            self.edc_pltctrl.add_spectrum(self.x_offseted_paths[i], self.z_edc_paths[i], 
                                        label=self.peim.filename_lst[i], 
                                        scatter=False, alpha=1, linewidth=1,
                                        new_title=f"{self.filename_edc_entry.get()}\n",
                                        new_x_label=self.peim.x_label, 
                                        new_y_label="Intensity (cps)")

        if self.peim.z_sekisan_flag:
            self.edc_pltctrl.add_spectrum(self.x_offseted, self.z_edc_offseted, 
                                            label=self.label_edc, 
                                            color=SPECTRAL_COLOR, 
                                            scatter=False, linewidth=2)
        
        # image plotを更新
        try:
            self.peim_pltctrl.remove_lines()
        except:
            pass
        if self.flag_swap_image_xy_axes==False: # XY軸swapなし       
            if self.y_min!=self.y_slice_min or self.y_max!=self.y_slice_max: # 全積分でないとき積分範囲をプロット
                    self.peim_pltctrl.add_line([self.x_min, self.x_max], [self.y_slice_min, self.y_slice_min], linecolor="black", linewidth=1)
                    self.peim_pltctrl.add_line([self.x_min, self.x_max], [self.y_slice_max, self.y_slice_max], linecolor="black", linewidth=1)
        else: # XY軸swap
            # imageにEDCを切り出した領域を示すlineを追加
            if self.y_min!=self.y_slice_min or self.y_max!=self.y_slice_max: # 全積分でないとき積分範囲をプロット
                    self.peim_pltctrl.add_line([self.y_slice_min, self.y_slice_min], [self.x_min, self.x_max], linecolor="black", linewidth=1)
                    self.peim_pltctrl.add_line([self.y_slice_max, self.y_slice_max], [self.x_min, self.x_max], linecolor="black", linewidth=1)

        # 軸の向きを設定
        if self.peim.EF is not None:
            self.edc_pltctrl.ax.invert_xaxis()
        
        # EDCの範囲初期化 Y
        self.z_edc_max_entry.delete(0, customtkinter.END)
        self.z_edc_min_entry.delete(0, customtkinter.END)
        # Yはリストがそろっていない場合の処理を別で行うため少し複雑
        z_min=np.inf
        z_max=-np.inf
        for i in range(len(self.z_edc_paths)):
            z_min_=np.amin(np.array(self.z_edc_paths[i]))
            z_max_=np.amax(np.array(self.z_edc_paths[i]))
            if z_min>=z_min_:
                z_min=z_min_
            if z_max<=z_max_:
                z_max=z_max_
        self.z_edc_min_entry.insert(0, np.round(z_min, 4))
        self.z_edc_max_entry.insert(0, np.round(z_max, 4))

        # プロットする領域を指定
        self.update_edc_x_range_event()
        self.update_edc_z_range_event()
        if self.yscale_edc=='log':
            self.show_log_yscale_edc()

        self.edc_pltctrl.change_legend_position(mode='best', fontsize='small')
        self.edc_pltctrl.update_canvas()
        
        #EDC viewerのための更新
        self.initialize_edc_setting_values() # 初期化

    def update_x_slice_center_or_width_event(self, event=None):
        self.x_slice_min_entry.delete(0, customtkinter.END)
        self.x_slice_max_entry.delete(0, customtkinter.END)
        x_slice_min=float(self.x_slice_center_entry.get())-float(self.x_slice_width_entry.get())/2
        x_slice_max=float(self.x_slice_center_entry.get())+float(self.x_slice_width_entry.get())/2
        # out of rangeの時の処理
        if x_slice_min<=self.x_min:
            x_slice_min=self.x_min
            x_slice_max=self.x_min+float(self.x_slice_width_entry.get())
        elif x_slice_max>=self.x_max:
            x_slice_max=self.x_max
            x_slice_min=x_slice_max-float(self.x_slice_width_entry.get())
        # entryboxの更新
        self.x_slice_min_entry.insert(0, np.round(x_slice_min,ORDER_X))
        self.x_slice_max_entry.insert(0, np.round(x_slice_max,ORDER_X))
        self.update_x_slice_min_or_max_event()

    def update_x_slice_min_or_max_event(self, event=None):
        self.x_slice_center_entry.delete(0, customtkinter.END)
        self.x_slice_width_entry.delete(0, customtkinter.END)

        x_slice_min=float(self.x_slice_min_entry.get())
        x_slice_max=float(self.x_slice_max_entry.get())
        print(x_slice_min, x_slice_max)

        # 入力が最大・最小値を超えている場合は最大・最小値で置換
        if x_slice_min <= self.x_min:
            x_slice_min=self.x_min
            self.x_slice_min_entry.delete(0, customtkinter.END)
            self.x_slice_min_entry.insert(0, x_slice_min)
        if x_slice_max >= self.x_max:
            x_slice_max=self.x_max
            self.x_slice_max_entry.delete(0, customtkinter.END)
            self.x_slice_max_entry.insert(0, x_slice_max)

        x_slice_center=np.round((x_slice_min+x_slice_max)/2,ORDER_X)
        x_slice_width=np.round(abs(x_slice_max-x_slice_min),ORDER_X)

        self.x_slice_center_entry.insert(0,x_slice_center)
        self.x_slice_width_entry.insert(0,x_slice_width)

        # スライダーのつまみを設定
        self.x_slice_max_slider.set(x_slice_max)
        self.x_slice_min_slider.set(x_slice_min)
        self.x_slice_center_slider.set(x_slice_center)
        self.x_slice_width_slider.set(x_slice_width)
        
        self.generate_a_ydc(self.x_offseted)

    def update_x_slice_min_or_max_slider_event(self, event=None):
        """スライダーの値が変更されたときの処理"""
        x_slice_max = self.x_slice_max_slider.get()  # スライダーの値を取得
        x_slice_min = self.x_slice_min_slider.get()
        
        # entryboxの更新
        self.x_slice_max_entry.delete(0, customtkinter.END)
        self.x_slice_min_entry.delete(0, customtkinter.END)
        self.background_intensity_edc_ydc_entry.delete(0, customtkinter.END)

        self.x_slice_max_entry.insert(0, x_slice_max)
        self.x_slice_min_entry.insert(0, x_slice_min)

        # entryboxの値でimageを更新 
        self.update_x_slice_min_or_max_event()

    def update_x_slice_center_or_width_slider_event(self, event=None):
            self.x_slice_min_entry.delete(0, customtkinter.END)
            self.x_slice_max_entry.delete(0, customtkinter.END)
            self.background_intensity_edc_ydc_entry.delete(0, customtkinter.END)
            x_slice_min=float(self.x_slice_center_slider.get())-float(self.x_slice_width_slider.get())/2
            x_slice_max=float(self.x_slice_center_slider.get())+float(self.x_slice_width_slider.get())/2

            # out of rangeの時の処理
            if x_slice_min<=self.x_min:
                x_slice_min=self.x_min
                x_slice_max=self.x_min+float(self.x_slice_width_slider.get())

            if x_slice_max>self.x_max:
                x_slice_max=self.x_max
                x_slice_min=x_slice_max-float(self.x_slice_width_slider.get())

            # entryboxの更新
            self.x_slice_min_entry.insert(0, np.round(x_slice_min,ORDER_X))
            self.x_slice_max_entry.insert(0, np.round(x_slice_max,ORDER_X))
            
            print(self.x_slice_min_entry.get(), self.x_slice_max_entry.get())

            self.update_x_slice_min_or_max_event()

    def generate_a_ydc(self, x):
        self.peim.z_edc=None
        # 更新した値を取得
        print("---2D Image Slice (Energy Direction) ---")
        if self.peim.EF is None: # Ek表示
            self.x_slice_min=float(self.x_slice_min_entry.get())
            self.x_slice_max=float(self.x_slice_max_entry.get())
        else: # EF表示
            self.x_slice_min=float(self.x_slice_max_entry.get())
            self.x_slice_max=float(self.x_slice_min_entry.get())

        print(f"切り出し最小値{self.x_slice_min}, 切り出し最大値{self.x_slice_max}", "EF表示のとき最大最小値は逆")

        # 取得した値を使用してYDCカーブを作る
        # khにしたあと、z imageも歪むのでself.z_imageを使用
        self.peim.generate_a_ydc(self.z_image, x, self.x_slice_min, self.x_slice_max, mode="ydc")
        # print(self.peim.z_ydc)

        # 以下でEDCをplot->canvasに出力   
        # EDCをplot ################################################
        self.edc_pltctrl.clear_plot() # plotの初期化 # edcではないのだが、そういう名前で定義してしまった。
        if self.peim.kh is None:
            y = self.peim.y_offseted
        elif self.peim.kh is not None:
            y = self.peim.kh_offseted
        label=f"From {np.round(self.x_slice_min,2)} eV\nto {np.round(self.x_slice_max,2)} eV"

        # YDC
        self.edc_pltctrl.add_spectrum(y, self.peim.z_ydc, label=label, new_title=f"YDC: {self.peim.filename}\n",
                                    new_x_label=self.peim.y_label, new_y_label="Intensity (cps)",color=SPECTRAL_COLOR, 
                                    scatter=False, linewidth=1.5)

        # imageにEDCを切り出したlineを追加 (XY軸 swapしているかどうかで条件分岐)
        self.peim_pltctrl.remove_lines() # lineを初期化
        if self.x_min!=self.x_slice_min or self.x_max!=self.x_slice_max: # 全積分でないとき積分範囲をプロット
            if self.flag_swap_image_xy_axes==False: # XY軸 swapなし
                self.peim_pltctrl.add_line([self.x_slice_min, self.x_slice_min], [self.y_min, self.y_max], linecolor="black", linewidth=1)
                self.peim_pltctrl.add_line([self.x_slice_max, self.x_slice_max], [self.y_min, self.y_max], linecolor="black", linewidth=1)
            else: # XY軸swapあり
                self.peim_pltctrl.add_line([self.y_min, self.y_max], [self.x_slice_min, self.x_slice_min], linecolor="black", linewidth=1)
                self.peim_pltctrl.add_line([self.y_min, self.y_max], [self.x_slice_max, self.x_slice_max], linecolor="black", linewidth=1)

        self.edc_pltctrl.update_canvas()

        # filenameの更新
        self.filename_edc_entry.delete(0, customtkinter.END)
        if self.x_slice_min==self.x_min and self.x_slice_max==self.x_max:
            self.filename_edc_entry.insert(0, f"{self.peim.filename.replace('.txt', '_fMDC.txt')}")
        else:
            self.filename_edc_entry.insert(0, f"{self.peim.filename.replace('.txt', '_MDC.txt')}")

    def update_edc_x_range_event(self, event=None):
        if self.peim.EF is None:
            self.edc_pltctrl.set_range(x_lim_min=float(self.x_edc_min_entry.get()), x_lim_max=float(self.x_edc_max_entry.get()))
        else:
            self.edc_pltctrl.set_range(x_lim_min=float(self.x_edc_max_entry.get()), x_lim_max=float(self.x_edc_min_entry.get()))

    def update_edc_z_range_event(self, event=None):
        # linearとlogで表示の仕方が違う。
        # linear->余白あり
        # log->余白なし
        if self.yscale_edc=="linear":
            self.edc_pltctrl.set_range(y_lim_min=float(self.z_edc_min_entry.get()), y_lim_max=float(self.z_edc_max_entry.get()))
            self.show_liner_yscale_edc()
        elif self.yscale_edc=="log":
            # logは負の数になると表示できなくなるので直接設定
            self.edc_pltctrl.ax.set_ylim(float(self.z_edc_min_entry.get()), float(self.z_edc_max_entry.get()))
            self.show_log_yscale_edc()
        # レイアウト最適化->表示
        self.edc_pltctrl.update_canvas()

    def autorange_button_edc_callback(self):
        # EDCの範囲更新 X 
        self.x_edc_max_entry.delete(0, customtkinter.END)
        self.x_edc_min_entry.delete(0, customtkinter.END)      
        self.z_edc_max_entry.delete(0, customtkinter.END)
        self.z_edc_min_entry.delete(0, customtkinter.END)

        x_min=np.inf
        x_max=-np.inf
        z_min=np.inf
        z_max=-np.inf
        
        z_edc=[]
        x_edc=[]
        # X data list
        if self.peim.EF_paths!=[]:
            x_edc.append(self.peim.EF_offseted_paths)
        else:
            x_edc.append(self.peim.x_offseted_paths)
        x_edc.append(self.x_offseted) # EDCのリストを取得

        # Z data list
        z_edc.append(self.z_edc_paths) # EDCのリストを取得
        z_edc.append(self.z_edc_offseted) # 平均EDCのリストを取得

        if self.peim.z_edc_offseted is not None: # bachground処理が行われている場合
            x_edc.append(self.x_offseted) # EDCのリストを取得
            z_edc.append(self.peim.z_edc_offseted)

        # 値の判定と更新
        for i in range(len(z_edc)):
            x_min_=np.amin(np.array(x_edc[i]))
            x_max_=np.amax(np.array(x_edc[i]))
            z_max_=np.amax(np.array(z_edc[i]))
            # zの最小値はlogスケール表示の場合は正の値のみを対象とするため処理が複雑
            z_array = np.array(z_edc[i])
            if self.yscale_edc == 'log':
                positive_vals = z_array[z_array > 0]
                if positive_vals.size == 0:
                    print(f"[警告] ログスケール表示できる正の値が存在しません (index={i})")
                    z_min_ = 1e-3  # fallback値、またはエラーにしても良い
                else:
                    z_min_ = np.amin(positive_vals)
            else:
                z_min_ = np.amin(z_array)

            # x範囲、Y範囲の更新
            if z_min>=z_min_:
                z_min=z_min_
            if z_max<=z_max_:
                z_max=z_max_
            if x_min>=x_min_:
                x_min=x_min_
            if x_max<=x_max_:
                x_max=x_max_


        self.x_edc_max_entry.insert(0, x_max)
        self.x_edc_min_entry.insert(0, x_min)
        self.z_edc_min_entry.insert(0, z_min)
        self.z_edc_max_entry.insert(0, z_max)

        # プロットする領域を指定
        self.update_edc_x_range_event()
        self.update_edc_z_range_event()
        # plotを出力
        self.edc_pltctrl.update_canvas()

    def change_z_edc_scale_button_callback(self):
        """
        Change the y-axis scale of the EDC plot between linear and log.
        Adjusts the y-axis tick format and updates the plot accordingly.
        """
        if self.yscale_edc == 'linear':
            # Switch to log scale
            self.show_log_yscale_edc()
        else:
            # Switch to linear scale
            self.show_liner_yscale_edc()

        # Update the y-axis range
        self.update_edc_z_range_event()

        # Optimize the plot layout
        self.edc_pltctrl.update_canvas()

    def show_log_yscale_edc(self):
        self.yscale_edc = 'log'
        self.edc_pltctrl.ax.set_yscale(self.yscale_edc)
        # Use LogFormatter with labelOnlyBase to ensure labels are 10^n
        self.edc_pltctrl.ax.yaxis.set_major_formatter(LogFormatter(base=10.0, labelOnlyBase=True))

    def show_liner_yscale_edc(self):
        self.yscale_edc = 'linear'
        self.edc_pltctrl.ax.set_yscale(self.yscale_edc)
        self.edc_pltctrl.ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        self.edc_pltctrl.ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))  # Scientific format

    def change_edc_legend_position_button_callback(self):
        if self.legend_loc_edc is None: # legend 非表示 -> legend 表示
            self.legend_loc_edc="best"
            self.edc_pltctrl.ax.legend(loc=self.legend_loc_edc, fontsize='small')
            self.update_edc_legend()
            print("Legend is displayed.")
        elif self.legend_loc_edc == "best": # legend 表示 -> legend 非表示
            self.legend_loc_edc = None
            self.edc_pltctrl.ax.legend(loc='best', fontsize='small') # エラー回避のため一度凡例作る。
            self.edc_pltctrl.ax.get_legend().remove()
            print("Legend is removed.")
        self.edc_pltctrl.update_canvas()

    def save_edc_data_button_callback(self):
        # 強度データの条件分岐
        if self.peim.z_edc is not None:
            data_type='edc'
            # X軸の条件分岐
            if self.peim.EF is None:
                axis_lst=['Ek']
            elif self.peim.VL is None:
                axis_lst=['EF', 'Ek']
            elif self.peim.VL is not None:
                axis_lst=['VL', 'EF', 'Ek']

        elif self.peim.z_ydc is not None:
            data_type='ydc'
            axis_lst=['Y']
        
        for axis in axis_lst:
            self.peim.save_data(data_type=data_type, axis=axis, filename=self.filename_edc_entry.get())
        

###########################################
    # EDC viewer
    def generate_edc_viewer(self):
        self.viewer_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.viewer_frame.grid(row=2, column=3, padx=(0, 10), pady=(0, 10), sticky="ew")

        # Title
        customtkinter.CTkLabel(self.viewer_frame, text='Modify EDC Appearance', font=self.fonts).grid(row=0, column=0, padx=(10, 10), pady=(10, 5), sticky="ew", columnspan=2)

        frame = customtkinter.CTkFrame(self.viewer_frame, fg_color='gray24')
        frame.grid(row=1, column=0, padx=(10, 10), pady=(0, 10), sticky="ew", columnspan=2)

        # Filename ComboBox
        self.filename_combo = customtkinter.CTkComboBox(
                                                        frame, font=self.fonts, 
                                                        values=[],
                                                        command=self.on_filename_select  # ファイル選択時のコールバックを設定
                                                        )
        self.filename_combo.grid(row=0, column=0, padx=(10, 10), pady=(10, 5), sticky="ew", columnspan=2)

        width=110

        # X Multiplier
        label = customtkinter.CTkLabel(frame, text='Mult Ek/Eb', width=width)
        label.grid(row=1, column=0, padx=(10, 10), pady=(0, 5), sticky="ew")
        self.x_mult_edc_entry = customtkinter.CTkEntry(frame, placeholder_text="倍数", width=width, font=self.fonts)
        self.x_mult_edc_entry.grid(row=1, column=1, padx=(0, 10), pady=(0, 5), sticky="ew")
        self.x_mult_edc_entry.insert(0, 1)
        self.x_mult_edc_entry.bind("<Return>", self.apply_edc_modifications)

        # Y Multiplier
        label = customtkinter.CTkLabel(frame, text='Mult Intensity', width=width)
        label.grid(row=2, column=0, padx=(10, 10), pady=(0, 5), sticky="ew")
        self.y_mult_edc_entry = customtkinter.CTkEntry(frame, placeholder_text="倍数", width=width, font=self.fonts)
        self.y_mult_edc_entry.grid(row=2, column=1, padx=(0, 10), pady=(0, 5), sticky="ew")
        self.y_mult_edc_entry.insert(0, 1)
        self.y_mult_edc_entry.bind("<Return>", self.apply_edc_modifications)

        # X Offset
        label = customtkinter.CTkLabel(frame, text='Offset Ek/Eb', width=width)
        label.grid(row=3, column=0, padx=(10, 10), pady=(0, 5), sticky="ew")
        self.x_offset_edc_entry = customtkinter.CTkEntry(frame, placeholder_text="定数", width=width, font=self.fonts)
        self.x_offset_edc_entry.grid(row=3, column=1, padx=(0, 10), pady=(0, 5), sticky="ew")
        self.x_offset_edc_entry.insert(0, 0)
        self.x_offset_edc_entry.bind("<Return>", self.apply_edc_modifications)

        # Intensity Offset
        label = customtkinter.CTkLabel(frame, text='Offset Intensity', width=width)
        label.grid(row=4, column=0, padx=(10, 10), pady=(0, 5), sticky="ew")
        self.y_offset_edc_entry = customtkinter.CTkEntry(frame, placeholder_text="定数", width=width, font=self.fonts)
        self.y_offset_edc_entry.grid(row=4, column=1, padx=(0, 10), pady=(0, 5), sticky="ew")
        self.y_offset_edc_entry.insert(0, 0)
        self.y_offset_edc_entry.bind("<Return>", self.apply_edc_modifications)

        # Reset Button
        reset_button = customtkinter.CTkButton(frame, text="Reset Values", command=self.reset_edc_setting_values, font=self.fonts, width=width)
        reset_button.grid(row=5, column=1, padx=(0, 10), pady=(0, 10), sticky="ew")

        # トグルスイッチの状態管理変数（必要なら初期状態をFalseに）
        self.hide_switch_var = customtkinter.BooleanVar()
        self.hide_switch_var.set(False)
        # トグルスイッチの作成
        self.hide_switch = customtkinter.CTkSwitch(
            frame,
            text="Hide Plot",
            variable=self.hide_switch_var,
            command=self.toggle_plot_visibility, 
            width=width
        )
        # レイアウト設定（grid）
        self.hide_switch.grid(row=5, column=0, padx=(10, 10), pady=(0, 10), sticky="ew")

        # トグルスイッチの状態管理変数（必要なら初期状態をFalseに）
        self.hide_switch_all_var = customtkinter.BooleanVar()
        self.hide_switch_all_var.set(False)
        # トグルスイッチの作成
        self.hide_switch_all = customtkinter.CTkSwitch(self.viewer_frame,
            text="Hide All Plot",
            variable=self.hide_switch_all_var,
            command=self.hide_all_plots, 
            width=width
        )
        self.hide_switch_all.grid(row=2, column=0, padx=(10, 10), pady=(0, 5), sticky="ew")

        # Reset Button
        reset_all_values_button = customtkinter.CTkButton(self.viewer_frame, text="Reset All Values", command=self.reset_all_edc_setting_values, font=self.fonts, width=width)
        reset_all_values_button.grid(row=2, column=1, padx=(0, 10), pady=(0, 5), sticky="ew")

        # Offsetを反映させたEDCを作成
        hide_all_plots_button = customtkinter.CTkButton(self.viewer_frame, text="(D)Integrate Modified Data", command=self.integrate_files, font=self.fonts, width=1.5*width)
        hide_all_plots_button.grid(row=3, column=0, padx=(10, 10), pady=(0, 33), sticky="e", columnspan=2)

#######
#######
    def integrate_files(self):
        # 「From * to *」および「New Integrated EDC」で始まるファイル名は除外する
        self.x_offseted_filename_lst = [
            fn for fn in self.original_x_edc.keys()
            if not (fn.startswith("From ") and "to" in fn) and not fn.startswith("New Integrated EDC")
        ]
        print(self.x_offseted_filename_lst)

        # 有効ファイルが2つ以上必要
        if len(self.x_offseted_filename_lst) < 2:
            messagebox.showerror("Error!", "平均化するにはEDCファイルが2つ以上必要です。")
            return

        # x変換適用済みデータの格納
        transformed_data = []
        min_step = None

        for filename in self.x_offseted_filename_lst:
            x = np.array(self.original_x_edc[filename])
            y = np.array(self.original_y_edc[filename])
            setting = self.edc_settings.get(filename, {
                "x_mult": 1.0, "x_offset": 0.0,
                "y_mult": 1.0, "y_offset": 0.0
            })

            x_new = (x + setting["x_offset"]) * setting["x_mult"]
            y_new = (y + setting["y_offset"]) * setting["y_mult"] 
            # y_new = y

            transformed_data.append((x_new, y_new))

            # x_step の最小値を取得
            step = np.min(np.diff(np.sort(x_new)))
            if min_step is None or step < min_step:
                min_step = step

        # 共通 x 範囲の抽出
        min_x = max(np.min(x) for x, _ in transformed_data)
        max_x = min(np.max(x) for x, _ in transformed_data)

        if min_x >= max_x:
            messagebox.showinfo("Info", f"共通のX範囲が見つかりませんでした。\n処理を終了します。")
            return

        # 共通 x 軸を再生成
        new_x = np.arange(min_x, max_x, min_step)

        # スプライン補間（1次）でyを再生成
        interpolated_ys = []
        for x, y in transformed_data:
            f = interp1d(x, y, kind="linear", bounds_error=False, fill_value="extrapolate")
            interpolated_y = f(new_x)
            interpolated_ys.append(interpolated_y)

        # 平均化
        avg_y = np.mean(interpolated_ys, axis=0)

        # 結果の保存
        num = 1
        new_edc = f"New Integrated EDC {num}"
        self.integrated_edc_x = new_x
        self.integrated_edc_y = avg_y

        # 元データとしても保存
        self.original_x_edc[new_edc] = new_x
        self.original_y_edc[new_edc] = avg_y

        # edc_settings にも初期設定を入れておく
        self.edc_settings[new_edc] = {
            "x_mult": 1.0,
            "y_mult": 1.0,
            "x_offset": 0.0,
            "y_offset": 0.0,
        }


        new_edc = 'New EDC'
        self.filename_lst_edc_viewer.append(new_edc)
        self.filename_combo.configure(values=self.filename_lst_edc_viewer)

        # プロット
        self.plot_integrated_edc(new_edc)
        self.update_edc_legend()
        print(f"統合EDC '{new_edc}' を生成し、{len(new_x)}点でプロットしました。")

        print(self.filename_lst_edc_viewer)
        
    def plot_integrated_edc(self, avg_name):
        # 新規プロット
        new_line = self.edc_pltctrl.ax.plot(
            self.integrated_edc_x,
            self.integrated_edc_y,
            label=avg_name,
            linewidth=2,
            linestyle="-",
            color="black"
        )
        self.edc_pltctrl.line.append(new_line)

        self.edc_pltctrl.ax.legend(loc='best', fontsize='small')
        self.edc_pltctrl.ax.relim()
        self.edc_pltctrl.ax.autoscale_view()
        self.edc_pltctrl.fig.canvas.draw()
####
####

    def get_plot_data(self, filename):
        """filename に対応する Line2D オブジェクトを返す"""
        line = self.plot_line_map.get(filename)
        if line:
            return [line]  # applyなどでfor loopできるようリスト形式にする
        return None

    def update_edc_setting_values(self, y_mult=1.0, x_mult=1.0, x_offset=0.0, y_offset=0.0):
        """倍率とオフセットのエントリを更新"""
        self.y_mult_edc_entry.delete(0, "end")
        self.y_mult_edc_entry.insert(0, y_mult)
        self.x_mult_edc_entry.delete(0, "end")
        self.x_mult_edc_entry.insert(0, x_mult)
        self.y_offset_edc_entry.delete(0, "end")
        self.y_offset_edc_entry.insert(0, y_offset)
        self.x_offset_edc_entry.delete(0, "end")
        self.x_offset_edc_entry.insert(0, x_offset)

    def initialize_edc_setting_values(self):
        # 新しいデータをロードする前に設定を初期化
        # 各ファイルの設定を記憶する辞書（ファイル名をキーとして値を保持）
        self.edc_settings.clear()
        # 元の x_data と y_data を保存するための辞書
        self.original_x_edc.clear()
        self.original_y_edc.clear()
        # プロットの表示/非表示状態を保持する辞書
        self.plot_visibility.clear()
        # データ保持のため
        self.selected_filename = None

        # Line2Dオブジェクトを明示的に filename に対応させる辞書
        self.plot_line_map = {}

        # Legend listを作成
        self.filename_lst_edc_viewer = None
        self.filename_lst_edc_viewer = copy.deepcopy(self.peim.filename_lst) # 各file名
        # print(self.peim.filename_lst)

        if self.peim.z_sekisan_flag and self.label_edc not in self.filename_lst_edc_viewer: # 平均EDCがあり、リストに追加していないとき
            # 該当要素を削除して新しい値を挿入
            self.filename_lst_edc_viewer += [self.label_edc]

        if self.peim.z_edc_offseted is not None: # EDC平均をバックグラウンド処理したとき
            if 'BG' not in self.filename_lst_edc_viewer: # まだbackground subtractedなどがlistにappendされていないとき
                self.filename_lst_edc_viewer += ['BG Subtracted', 'BG']

        # print('Plotted Filename (EDC):', self.filename_lst_edc_viewer)

        # Comboboxに代入
        try:
            self.filename_combo.configure(values=self.filename_lst_edc_viewer)
            # comboboxの更新
            self.filename_combo.set(self.filename_lst_edc_viewer[-1])
        except Exception as e:
            print(f"Error configuring filename combo box: {e}")
            
        # EDC設定の初期化
        self.edc_settings = {
                            filename: 
                                {
                                "x_mult": 1.0,
                                "y_mult": 1.0, 
                                "x_offset": 0.0,
                                "y_offset": 0.0, 
                                }
                            for filename in self.filename_lst_edc_viewer
                            }
        
        # 表示値の更新
        self.x_offset_edc_entry.delete(0,customtkinter.END)
        self.x_mult_edc_entry.delete(0,customtkinter.END)
        self.y_offset_edc_entry.delete(0,customtkinter.END)
        self.y_mult_edc_entry.delete(0,customtkinter.END)
        self.x_offset_edc_entry.insert(0,0)
        self.x_mult_edc_entry.insert(0,1)
        self.y_offset_edc_entry.insert(0,0)
        self.y_mult_edc_entry.insert(0,1)

        # 初期状態ではすべてのプロットを表示
        self.plot_visibility = {filename: True for filename in self.filename_lst_edc_viewer}
        self.hide_switch.deselect() # checkbox更新

        file_lst = self.peim.filename_lst.copy()
        # 平均スペクトル追加
        if self.peim.z_sekisan_flag and self.label_edc not in file_lst:
            file_lst.append(self.label_edc)
        # バックグラウンド処理結果追加
        if self.peim.z_edc_offseted is not None:
            for extra in ['BG Subtracted', 'BG']:
                if extra not in file_lst:
                    file_lst.append(extra)

        
        for selected_filename in self.filename_lst_edc_viewer:
            if selected_filename not in file_lst:
                continue  # 無効な場合はスキップ

            # 元の x_data と y_data を保持（最初の適用時）
            file_index = file_lst.index(selected_filename)
            line_data = self.edc_pltctrl.line[file_index]  # 1ファイルあたり[Line2D]

            self.original_x_edc[selected_filename] = line_data[0].get_xdata()
            self.original_y_edc[selected_filename] = line_data[0].get_ydata()

            # 対応するLine2Dオブジェクトを記録
            self.plot_line_map[selected_filename] = line_data[0]

        # all plot hide トグルスイッチ off
        self.hide_switch_all.deselect() 
            
    def _edc_setting_values_init(self):
        self.edc_settings = {
                            filename: 
                                {
                                "x_mult": 1.0,
                                "y_mult": 1.0, 
                                "x_offset": 0.0,
                                "y_offset": 0.0, 
                                }
                            for filename in self.filename_lst_edc_viewer
                            }


    def hide_all_plots(self):
        filename_now = self.filename_combo.get() # 現在のfilenameを取得

        # 全表示/全非表示
        if all(value is False for value in self.plot_visibility.values()): # 全てFalse (Hide) ならすべてプロットする
            for filename in self.filename_lst_edc_viewer:
                self.filename_combo.set(filename)
                self.hide_switch.deselect()
                self.toggle_plot_visibility()
        else:
            for filename in self.filename_lst_edc_viewer:
                self.filename_combo.set(filename)
                self.hide_switch.select()
                self.toggle_plot_visibility()

        # Viewer表示
        self.filename_combo.set(filename_now)
        self.y_mult_edc_entry.delete(0, customtkinter.END)
        self.x_offset_edc_entry.delete(0, customtkinter.END)
        self.x_mult_edc_entry.delete(0, customtkinter.END)
        self.y_offset_edc_entry.delete(0, customtkinter.END)
        self.x_mult_edc_entry.insert(0, self.edc_settings[filename_now]["x_mult"])
        self.y_mult_edc_entry.insert(0, self.edc_settings[filename_now]["y_mult"])
        self.x_offset_edc_entry.insert(0, self.edc_settings[filename_now]["x_offset"])
        self.y_offset_edc_entry.insert(0, self.edc_settings[filename_now]["y_offset"])

    def toggle_plot_visibility(self):
        """選択されたプロットの表示・非表示を切り替える"""
        selected_filename = self.filename_combo.get()
        visible = not self.hide_switch.get()  # チェックボックス状態から反転

        # プロットデータの取得
        plot_data = self.get_plot_data(selected_filename)
        if not plot_data:
            print(f"Error: No plot data found for {selected_filename}")
            return

        # 表示状態を更新
        for plot in plot_data:
            plot.set_visible(visible)

        # 表示状態を保存
        self.plot_visibility[selected_filename] = visible

        # 凡例更新
        self.update_edc_legend()

        # 描画更新
        self.edc_pltctrl.fig.canvas.draw()

    def update_edc_legend(self):
        """凡例を更新し、表示されているプロットに対応したアイテムだけを表示"""
        handles, labels = self.edc_pltctrl.ax.get_legend_handles_labels()

        # 表示されていないプロットを凡例から除外
        filtered_handles = []
        filtered_labels = []

        # 他のプロットについての処理
        for handle, label in zip(handles, labels):
            if label in self.plot_visibility and self.plot_visibility[label]:
                filtered_handles.append(handle)
                filtered_labels.append(label)

        # 凡例を再描画（フィルタリングされたハンドルとラベルを使用）
        if self.legend_loc_edc!=None:
            self.edc_pltctrl.ax.legend(filtered_handles, filtered_labels, fontsize='small')
        self.edc_pltctrl.fig.canvas.draw()  # 描画更新

    def on_filename_select(self, selected_filename):
        """コンボボックスでファイル名を選択したときの処理"""
        self.selected_filename = selected_filename

        # 選択されたファイルの設定を反映
        if selected_filename in self.edc_settings:
            settings = self.edc_settings[selected_filename]
            self.update_edc_setting_values(
                                            y_mult=settings["y_mult"], 
                                            x_offset=settings["x_offset"], 
                                            x_mult=settings["x_mult"], 
                                            y_offset=settings["y_offset"]
                                            ) # valuesを更新
        else:
            # 設定がなければデフォルト値を使用
            self.update_edc_setting_values() # 初期化

        # チェックボックスの状態を反映
        if selected_filename in self.plot_visibility:
            # `plot_visibility` に保存された表示状態をチェックボックスに反映
            self.hide_switch.select() if not self.plot_visibility[selected_filename] else self.hide_switch.deselect()
        else:
            # デフォルトは表示されている状態
            self.hide_switch.deselect()

    def apply_edc_modifications(self, event=None):
        """Y軸定数倍とX軸オフセットを適用し、設定を保存する"""
        selected_filename = self.filename_combo.get()

        # 入力値を取得
        try:
            y_multiplier = float(self.y_mult_edc_entry.get())
            y_offset = float(self.y_offset_edc_entry.get())
            x_multiplier = float(self.x_mult_edc_entry.get())
            x_offset = float(self.x_offset_edc_entry.get())
        except ValueError:
            print("無効な入力値です")
            return

        # 設定を保存
        self.edc_settings[selected_filename] = {
            "x_offset": x_offset,
            "x_mult": x_multiplier,
            "y_offset": y_offset,
            "y_mult": y_multiplier,
        }

        # プロットデータの取得
        plot_data = self.get_plot_data(selected_filename)
        if not plot_data:
            print(f"Error: No plot data found for {selected_filename}")
            return

        # 元データが存在しなければ終了
        # print(selected_filename)
        # print(self.original_x_edc)
        # print(self.original_y_edc)
        if selected_filename not in self.original_x_edc or selected_filename not in self.original_y_edc:
            print('a')
            print(f"Error: Original data not found for {selected_filename}")
            return

        x_data = self.original_x_edc[selected_filename]
        y_data = self.original_y_edc[selected_filename]

        # データ更新
        for plot in plot_data:
            plot.set_ydata([y * y_multiplier + y_offset for y in y_data])
            plot.set_xdata([x * x_multiplier + x_offset for x in x_data])

        # リミット再計算とビュー更新
        self.edc_pltctrl.ax.relim()
        self.edc_pltctrl.ax.autoscale_view()

        # 描画更新
        self.edc_pltctrl.fig.canvas.draw()

        print(f"Updated plot for '{selected_filename}' with y_new=y_original*{y_multiplier}+{y_offset} and x_new=x_original*{x_multiplier}+{x_offset}")

    def set_plot_visibility(self, filename, visible):
        """プロットの表示状態を設定"""
        file_index = self.peim.filename_lst.index(filename)
        if file_index < len(self.edc_pltctrl.line):
            line_data = self.edc_pltctrl.line[file_index]
            plot = line_data[0]
            plot.set_visible(visible)

        self.plot_visibility[filename] = visible
        self.update_edc_legend()

    def reset_edc_setting_values(self):
        """設定をリセット"""
        self.edc_settings[self.selected_filename] = {"y_mult": 1.0, "x_offset": 0.0, "x_mult": 1.0, "y_offset": 0.0}
        self.update_edc_setting_values()
        self.apply_edc_modifications()

    def reset_all_edc_setting_values(self):
        filename_now = self.filename_combo.get() # 現在のfilenameを取得
        
        for filename in self.filename_lst_edc_viewer:
            self.filename_combo.set(filename) # combobox指定
            self.update_edc_setting_values() # entrybox初期化
            self.apply_edc_modifications() # setting value適用

        # viewer表示
        self.filename_combo.set(filename_now)
        if self.plot_visibility[filename_now]:
            self.hide_switch.deselect()
        else:
            self.hide_switch.select()

#################################################################################################
    def generate_edcs_stack_frame(self):
        # EDCs stack plot
        self.edcs_stack_pltctrl=PlotControl(title="EDCs will be shown here.", x_label=self.x_label, y_label="Intensity (cps)", figsize_w=EDCS_WIDTH, figsize_h=EDCS_HEIGHT, fontsize=12)
        self.edcs_stack_pltctrl.add_spectrum(0, 0, "EDCs", color="white")
        self.edcs_stack_pltctrl.change_legend_position(mode="best", fontsize="small")
        self.edcs_stack_canvas = FigureCanvasTkAgg(self.edcs_stack_pltctrl.fig, master=self.image_plot_frame)
        self.edcs_stack_canvas.get_tk_widget().grid(row=3, column=0, padx=(10, 10), pady=(0,10), sticky="new", rowspan=1)
        self.edcs_stack_pltctrl.update_canvas()

        # EDC stack #############
        self.edcs_stack_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20') 
        self.edcs_stack_frame.grid(row=3, column=1, padx=(10,10), pady=(10, 10), sticky="new")         
        # title
        edcs_stack_label = customtkinter.CTkLabel(self.edcs_stack_frame, text='EDCs Generator', font=self.fonts, width=120)
        edcs_stack_label.grid(row=0, column=0, padx=(10,10), pady=(10,10), sticky="ew", columnspan=2)
        # edc step
        edcs_ystep_label = customtkinter.CTkLabel(self.edcs_stack_frame, text="Y Step", width=120)
        edcs_ystep_label.grid(row=1, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.edcs_ystep_entry = customtkinter.CTkEntry(self.edcs_stack_frame, placeholder_text="", width=120, font=self.fonts)
        self.edcs_ystep_entry.grid(row=1, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.edcs_ystep_entry.bind("<Return>", command=self.generate_edcs_stack)
        # Intensity Offset
        edcs_z_offset_label = customtkinter.CTkLabel(self.edcs_stack_frame, text="Offset Intensity", width=120)
        edcs_z_offset_label.grid(row=2, column=0, padx=(10,10), pady=(0,20), sticky="ew")
        self.edcs_z_offset_entry = customtkinter.CTkEntry(self.edcs_stack_frame, placeholder_text="cps", width=120, font=self.fonts)
        self.edcs_z_offset_entry.grid(row=2, column=1, padx=(0,10), pady=(0,20), sticky="ew")
        self.edcs_z_offset_entry.bind("<Return>", command=self.generate_edcs_stack)

    def generate_edcs_stack_range_frame(self):
        self.edcs_stack_range_frame = customtkinter.CTkFrame(self.image_plot_frame, fg_color='gray20')
        self.edcs_stack_range_frame.grid(row=3, column=2, padx=(0, 10), pady=(10,10), sticky="new")

        # title
        self.edcs_stack_range_label = customtkinter.CTkLabel(self.edcs_stack_range_frame, text='XY Range', font=self.fonts)
        self.edcs_stack_range_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=2)
        # 最大エネルギーラベル
        customtkinter.CTkLabel(self.edcs_stack_range_frame, text='Max Energy', width=120).grid(row=1, column=0, padx=10, pady=(0,5), sticky="ew")
        self.edcs_stack_x_lim_max_entry = customtkinter.CTkEntry(self.edcs_stack_range_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.edcs_stack_x_lim_max_entry.grid(row=1, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.edcs_stack_x_lim_max_entry.bind("<Return>", self.update_edcs_stack_range_event)   
        # 最小エネルギーラベル
        customtkinter.CTkLabel(self.edcs_stack_range_frame, text='Min Energy', width=120).grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")
        self.edcs_stack_x_lim_min_entry = customtkinter.CTkEntry(self.edcs_stack_range_frame, placeholder_text="eV", width=120, font=self.fonts)
        self.edcs_stack_x_lim_min_entry.grid(row=2, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.edcs_stack_x_lim_min_entry.bind("<Return>", self.update_edcs_stack_range_event)
        # 最大yラベル
        customtkinter.CTkLabel(self.edcs_stack_range_frame, text='Max Intensity', width=120).grid(row=3, column=0, padx=10, pady=(0,5), sticky="ew")
        self.edcs_stack_y_lim_max_entry = customtkinter.CTkEntry(self.edcs_stack_range_frame, placeholder_text="cps", width=120, font=self.fonts)
        self.edcs_stack_y_lim_max_entry.grid(row=3, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.edcs_stack_y_lim_max_entry.bind("<Return>", self.update_edcs_stack_range_event)   
        # 最小yラベル
        customtkinter.CTkLabel(self.edcs_stack_range_frame, text='Min Intensity', width=120).grid(row=4, column=0, padx=10, pady=(0,5), sticky="ew")
        self.edcs_stack_y_lim_min_entry = customtkinter.CTkEntry(self.edcs_stack_range_frame, placeholder_text="cps", width=120, font=self.fonts)
        self.edcs_stack_y_lim_min_entry.grid(row=4, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.edcs_stack_y_lim_min_entry.bind("<Return>", self.update_edcs_stack_range_event)
        
        # Full Range
        edcs_stack_fullrange_button = customtkinter.CTkButton(self.edcs_stack_range_frame, text="Full Range", command=self.edcs_stack_autorange_button_callback, width=120, font=self.fonts)
        edcs_stack_fullrange_button.grid(row=5, column=1, padx=(0,10), pady=(0,5), sticky="we")
        # reverse axis
        edcs_stack_x_reverse_button = customtkinter.CTkButton(self.edcs_stack_range_frame, text="Reverse X", command=self.edcs_stack_reverse_x_axis_callback, width=120, font=self.fonts)
        edcs_stack_x_reverse_button.grid(row=7, column=1, padx=(0,10), pady=(0,5), sticky="we")
        # legend
        edcs_stack_x_reverse_button = customtkinter.CTkButton(self.edcs_stack_range_frame, text="Move Legend", command=self.rearrange_edcs_stack_legend_callback, width=120, font=self.fonts)
        edcs_stack_x_reverse_button.grid(row=5, column=0, padx=(10,10), pady=(0,5), sticky="we")
        
        # filename
        customtkinter.CTkLabel(self.edcs_stack_range_frame, text='Output Filename').grid(row=8, column=0, padx=10, pady=(0,5), sticky="ew")
        self.filename_edcs_entry = customtkinter.CTkEntry(self.edcs_stack_range_frame, placeholder_text='EDCs Filename', font=self.fonts)
        self.filename_edcs_entry.grid(row=8, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        # saveボタン
        save_edcs_button = customtkinter.CTkButton(self.edcs_stack_range_frame, command=self.save_edcs_data_button_callback, text="Save EDCs", font=self.fonts, width=120)
        save_edcs_button.grid(row=9, column=1, padx=(0,10), pady=(0,20), sticky="ew")

    def generate_edcs_stack(self, event=None):
        print("---EDCs stack---")
        # 以前のプロットがあれば閉じる
        if hasattr(self, 'edcs_stack_pltctrl') and self.edcs_stack_pltctrl is not None:
            plt.close(self.edcs_stack_pltctrl.fig)  # 特定の図を閉じる

        # edcs stacking生成
        self.peim.generate_edcs_stack(self.y_offseted, float(self.edcs_ystep_entry.get()), self.z_image)
        # edcs offset list生成
        self.peim.z_offset_lst_edcs=[]
        for i in range(len(self.peim.z_edcs)):
            self.peim.z_offset_edcs_lst.append(float(self.edcs_z_offset_entry.get())*-i)
        
        # 以下でEDCをplot->canvasに出力
        # legendを生成
        if self.peim.y_label=="Angle (Degrees)":
            c_label="deg"
        elif self.peim.y_label==r"$k_{\parallel} \ \mathrm{(\AA^{-1})}$":
            c_label = r"$\mathrm{\AA^{-1}}$"            
        elif self.peim.y_label=="Position (mm)":
            c_label="mm"
        print(f"Yステップ: {self.edcs_ystep_entry.get()} {c_label}, 強度オフセット: {self.edcs_z_offset_entry.get()}")
    
        # filename更新
        # 初期化
        self.filename_edcs_entry.delete(0, customtkinter.END)
        # 軸ごとにfilenameを変える
        # if self.peim.EF is None:
        self.filename_edcs_entry.insert(0, f"{self.peim.filename.replace('.txt', '_EDCs.txt')}")
        # elif self.peim.VL is None:
        #     self.filename_edcs_entry.insert(0, f"{self.peim.filename.replace('.txt', '_EDCs_EF.txt')}")
        # elif self.peim.VL is not None:
        #     self.filename_edcs_entry.insert(0, f"{self.peim.filename.replace('.txt', '_EDCs_VL.txt')}")

        # plot ##########################################
        self.edcs_stack_pltctrl=PlotControl(title=f"{self.filename_edcs_entry.get()}\nY Step: {self.peim.y_step_edcs} {c_label}", x_label=self.peim.x_label, y_label="Intensity (cps)", figsize_w=EDCS_WIDTH, figsize_h=EDCS_HEIGHT, fontsize=12, plt_interaction=False)

        res = None  
        for i in range(len(self.peim.z_edcs)):
            if i <= 50:
                # i が50以下のときはプロットを続ける
                self.edcs_stack_pltctrl.add_spectrum(self.x_offseted, self.peim.z_edcs[i]+self.peim.z_offset_edcs_lst[i], 
                                                    str(np.round(self.peim.y_slice_center_edcs[i], 3)) + " " + c_label, 
                                                    color=SPECTRAL_COLOR, scatter=False, linewidth=1.5)   
                
            elif res is None:
                # i が50以上のとき一度だけ ask_me を呼び出す
                res = rpa.ask_me("Warning!", "There are too many spectra. Do you continue plotting?")
                # ask_meの結果に応じてプロットを継続するか判断
                if res != "y":
                    # プロットを中止し、凡例を消して"プロットが中止されました"を表示
                    self.edcs_stack_pltctrl.ax.get_legend().remove()  # 既存の凡例を削除
                    self.edcs_stack_pltctrl.ax.legend(["Plotting has been canceled."], loc="best")  # 凡例にメッセージを追加
                    print("プロットが中止されました。")
                    break  # プロットを中止
            if res == "y":
                # resがyならプロットを続ける
                self.edcs_stack_pltctrl.add_spectrum(self.x_offseted, self.peim.z_edcs[i]+self.peim.z_offset_edcs_lst[i], 
                                                    str(np.round(self.peim.y_slice_center_edcs[i], 3)) + " " + c_label, 
                                                    color="tab:blue", scatter=False, linewidth=1.5)

        # legendの位置と大きさ
        if len(self.peim.z_edcs)>=15: # 表示するプロット数が多いときはfontsizeを下げる
            self.edcs_stack_pltctrl.change_legend_position(mode=self.legend_loc_edc, fontsize="small")
        else:
            self.edcs_stack_pltctrl.change_legend_position(mode=self.legend_loc_edc)
        # legend設定
        self.legend_loc_edcs="edcs"
        self.rearrange_edcs_stack_legend_callback()
        # canvasに出力
        self.redraw_canvas(self.edcs_stack_pltctrl, self.image_plot_frame, row=3, column=0)
        # self.edcs_stack_pltctrl.fig.canvas.draw()
        print(f"切り出したyの中心値: {self.peim.y_slice_center_edcs[:]}")

        # entry boxの更新
        self.edcs_stack_autorange_button_callback()
        print("Stacked EDCs were plotted.")

        self.edcs_ystep_entry.delete(0, customtkinter.END)
        self.edcs_ystep_entry.insert(0, str(self.peim.y_step_edcs))
        

    def update_edcs_stack_range_event(self, event=None):
        # 軸調整
        """xとyの表示範囲を変更"""
        try:
            # entry boxから値を取得
            x_lim_min = float(self.edcs_stack_x_lim_min_entry.get())
            x_lim_max = float(self.edcs_stack_x_lim_max_entry.get())
            y_lim_min = float(self.edcs_stack_y_lim_min_entry.get())
            y_lim_max = float(self.edcs_stack_y_lim_max_entry.get())
            
            if self.peim.EF is None:
                self.edcs_stack_pltctrl.set_range(x_lim_min, x_lim_max, y_lim_min, y_lim_max)
            else:
                self.edcs_stack_pltctrl.set_range(x_lim_max, x_lim_min, y_lim_min, y_lim_max)

            # 再描画
            self.redraw_canvas(self.peim_pltctrl, self.image_plot_frame, row=0, column=0, sticky="ew", rowspan=2)
        except ValueError:
            print("Invalid value")

    def edcs_stack_autorange_button_callback(self):
        # 初期化
        self.edcs_stack_x_lim_min_entry.delete(0, customtkinter.END)
        self.edcs_stack_x_lim_max_entry.delete(0, customtkinter.END)
        self.edcs_stack_y_lim_min_entry.delete(0, customtkinter.END)
        self.edcs_stack_y_lim_max_entry.delete(0, customtkinter.END)
        # 更新 (EntryBox)
        self.edcs_stack_x_lim_min_entry.insert(0, np.amin(self.x_offseted))
        self.edcs_stack_x_lim_max_entry.insert(0, np.amax(self.x_offseted))
        self.edcs_stack_y_lim_min_entry.insert(0, np.amin(self.peim.z_edcs[-1])+self.peim.z_offset_edcs_lst[-1])
        self.edcs_stack_y_lim_max_entry.insert(0, np.amax(self.peim.z_edcs[0]))
        # plot
        self.update_edcs_stack_range_event()

    def edcs_stack_reverse_x_axis_callback(self):
        self.edcs_stack_pltctrl.ax.invert_xaxis()
        # canvasに出力
        self.redraw_canvas(self.edcs_stack_pltctrl, self.image_plot_frame, row=3, column=0)       

    def rearrange_edcs_stack_legend_callback(self):    
        if self.legend_loc_edcs=="edcs":
            self.legend_loc_edcs=None
            self.edcs_stack_pltctrl.change_legend_position(mode=self.legend_loc_edcs)
        
        elif self.legend_loc_edcs is None:
            self.legend_loc_edcs="best"
            self.edcs_stack_pltctrl.change_legend_position(mode=self.legend_loc_edcs, fontsize="small")        
        
        elif self.legend_loc_edcs=="best":
            self.legend_loc_edcs="edcs"
            # legend数を判定する
            ncol=math.ceil(len(self.peim.z_edcs)/50)
            # if len(self.peim.z_edcs)>=10:
            self.edcs_stack_pltctrl.change_legend_position(mode=self.legend_loc_edcs, fontsize="small", ncol=ncol)

    def save_edcs_data_button_callback(self):
        if self.peim.EF is None:
            axis_lst=['Ek']
        elif self.peim.VL is None:
            axis_lst=['EF', 'Ek']
        elif self.peim.VL is not None:
            axis_lst=['VL', 'EF', 'Ek']
        
        for axis in axis_lst:
            for data_type in ['edcs', 'edcs_offseted']:
                self.peim.save_data(data_type=data_type, axis=axis, filename=self.filename_edcs_entry.get())


#################################################################################################
    def redraw_canvas(self, pltctrl, frame, row=0, column=0, padx=10, pady=(0,5), sticky="ew", columnspan=1, rowspan=1):
        # フレームにキャンバスが管理されているか確認
        if not hasattr(frame, 'canvases'):
            frame.canvases = {}

        # 指定したrow, columnのcanvasを初期化
        canvas_key = (row, column)
        if canvas_key in frame.canvases and frame.canvases[canvas_key] is not None:
            frame.canvases[canvas_key].get_tk_widget().destroy()  # FigureCanvasTkAggに関連するTkinterウィジェットを削除
            del frame.canvases[canvas_key]  # 古いcanvasオブジェクトへの参照を削除

        # 新しいキャンバスを作成して再配置
        canvas = FigureCanvasTkAgg(pltctrl.fig, master=frame)
        canvas.draw()  # 新しいキャンバスを明示的に描画
        canvas.get_tk_widget().grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky, columnspan=columnspan, rowspan=rowspan)

        # 新しいcanvasオブジェクトを辞書に保存
        frame.canvases[canvas_key] = canvas

        print(f"現在のFigure ID一覧: {plt.get_fignums()}")

# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(True, True)
    app.mainloop()