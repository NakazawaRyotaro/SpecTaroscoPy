import customtkinter
from typing import Union, Callable
import customtkinter
import os 
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

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
import RyoPy.defs_for_ctk as rpc
from RyoPy.Spectrum import Spectrum
from RyoPy.MBS_A1 import MBS_A1
from RyoPy.PlotControl import PlotControl, ImagePlotControl
from pathlib import Path


# srcディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent
# print(CURRENT_PATH)
# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
arpes_image_setting_path = os.path.join(SRC_PATH, "setting", "ARPES_image_setting.txt")

FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")
USER, has_USER = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")
if not has_USER:
    USER=None
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")

COLORMAP, has_COLORMAP = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "colormap_photoemission_intensity_map", type="str")

SPECTRAL_COLOR_='darkslateblue'
SPECTRAL_COLOR, has_SPECTRAL_COLOR = rpa.open_file_and_get_words_next_to_search_term(arpes_image_setting_path, "color_edc", type="str")
if not has_SPECTRAL_COLOR:
    SPECTRAL_COLOR=SPECTRAL_COLOR_

# 値の変更を知らせるcallback関数
def my_callback(value):
    print("Value changed to:", value)


# widget関連
class CustomTkinterTool:
    def __init__(self) -> None:
        pass

    # あるframe内のwidgetをすべて削除する。
    def clear_all_widgets(frame):
        for widget in frame.winfo_children():
            widget.destroy()


# FloatSpinboxのclass
class FloatSpinbox(customtkinter.CTkFrame):
    def __init__(self, *args,
                 width: int = 100,
                 height: int = 32,
                 step_size: Union[int, float] = 1,
                 command: Callable = None,
                 callback: Callable = None,  # callback
                 lower_limit: Union[int, float] = None,  # 下限値のデフォルト値はNone
                 upper_limit: Union[int, float] = None,  # 上限値のデフォルト値はNone
                 **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        self.step_size = step_size
        self.command = command
        self.callback = callback  # callback

        self.lower_limit = lower_limit  # 下限値を保持
        self.upper_limit = upper_limit  # 上限値を保持

        self.step_size = step_size
        self.command = command

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.grid_columnconfigure((0, 2), weight=0)  # buttons don't expand
        self.grid_columnconfigure(1, weight=1)  # entry expands

        self.subtract_button = customtkinter.CTkButton(self, text="-", width=height-6, height=height-6,
                                                       command=self.subtract_button_callback)
        self.subtract_button.grid(row=0, column=0, padx=(3, 0), pady=3)

        self.entry = customtkinter.CTkEntry(self, width=width-(2*height), height=height-6, border_width=0)
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")

        self.add_button = customtkinter.CTkButton(self, text="+", width=height-6, height=height-6,
                                                  command=self.add_button_callback)
        self.add_button.grid(row=0, column=2, padx=(0, 3), pady=3)

        # default value
        self.entry.insert(0, "0.0")

    def add_button_callback(self):
        if self.command is not None:
            self.command()
        try:
            value = float(self.entry.get()) + self.step_size
            # 上限値のチェック
            if self.upper_limit is not None and value > self.upper_limit:
                value = self.upper_limit
            # 下限値のチェック
            if self.lower_limit is not None and value < self.lower_limit:
                value = self.lower_limit
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
            if self.callback:
                self.callback(value)
        except ValueError:
            return

    def subtract_button_callback(self):
        if self.command is not None:
            self.command()
        try:
            value = float(self.entry.get()) - self.step_size
            # 下限値のチェック
            if self.lower_limit is not None and value < self.lower_limit:
                value = self.lower_limit
            # 上限値のチェック
            if self.upper_limit is not None and value > self.upper_limit:
                value = self.upper_limit
            self.entry.delete(0, "end")
            self.entry.insert(0, value)
            if self.callback:
                self.callback(value)
        except ValueError:
            return

    def get(self) -> Union[float, None]:
        try:
            return float(self.entry.get())
        except ValueError:
            return None

    def set(self, value: float):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(float(value)))


# load data frame
class LoadDataFrame(customtkinter.CTkFrame): # GUI上部
    def __init__(self, master=None, header_name="Load Data", has_plot_data_frame=None, **kwargs):
        super().__init__(master)

        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.master = master

        # フォームのセットアップをする
        self.has_plot_data_frame=has_plot_data_frame
        self.setup_form()

    def setup_form(self):

        self.spectrum = Spectrum(plt_interaction=True)

        # 行方向のマスのレイアウトを設定する。リサイズしたときに一緒に拡大したい行をweight 1に設定。
        # self.grid_rowconfigure(0, weight=1)
        # 列方向のマスのレイアウトを設定する
        # self.grid_columnconfigure(0, weight=1)
        # フレームのラベルを表示
        self.label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        self.label.grid(row=0, column=0, padx=10, sticky="w")
        
        # loadボタン
        load_file_button = customtkinter.CTkButton(master=self, command=self.open_file_button_callback, text="Open File", font=self.fonts)
        load_file_button.grid(row=1, column=0, padx=10, pady=(0,10), sticky="w")

        # 取得するxの凡例名
        # ラベル
        x_legend_label = customtkinter.CTkLabel(master=self, text='X Data:')
        x_legend_label.grid(row=1, column=1, padx=10, pady=(0,10), sticky="w")
        # テキストボックス
        self.x_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["---X Legend---"])
                                                    # command=self.choice_x_legend_combo_callback)
        self.x_legend_combo.grid(row=1, column=2, padx=10, pady=(0,10), sticky="w")

        # 取得するyの凡例名
        y_legend_label = customtkinter.CTkLabel(master=self, text='Y Data:')
        y_legend_label.grid(row=1, column=3, padx=10, pady=(0,10), sticky="w")
        self.y_legend_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Y label", font=self.fonts)
        self.y_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["---Y Legend---"])
        self.y_legend_combo.grid(row=1, column=4, padx=10, pady=(0,10), sticky="w")
        
        # user name
        # user_label = customtkinter.CTkLabel(master=self, text='User:')
        # user_label.grid(row=1, column=5, padx=(10,10), pady=(0,10), sticky="w")
        # if USER!="":
        #     self.user_textbox = customtkinter.CTkEntry(master=self, placeholder_text=USER, font=self.fonts)
        #     self.user_textbox.insert(0, USER) #初期値
        # else:
        #     self.user_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Your name", font=self.fonts)
        # self.user_textbox.grid(row=1, column=6, padx=10, pady=(0,10), sticky="w")
        
        # loaded file
        loaded_file_path_label = customtkinter.CTkLabel(master=self, text='File Path:')
        loaded_file_path_label.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")

        self.loaded_file_path = customtkinter.CTkLabel(master=self, text="", wraplength=410)
        self.loaded_file_path.grid(row=2, column=1, columnspan=4, padx=10, pady=(0,10), sticky="ew")

        # 開くボタン 生成
        load_file_button = customtkinter.CTkButton(master=self, command=self.load_button_callback, text="Load", font=self.fonts)
        load_file_button.grid(row=1, column=5, padx=(15,10), pady=(0,10), sticky="ew")
        

    def open_file_button_callback(self):
        """
        開くボタンが押されたときのコールバック。
        """
        # FitSpectrumのインスタンスを作成
        # grobal変数にするのがカギ [他のclass(flame) でもspectrumインスタンスを使用でき、
        # インスタンス spectrum (= Spectrum) の関数 (method) やインスタンス変数を spectrum.xxx で呼び出せる] 
        self.spectrum.user = USER
        # self.spectrum.open_csv_file(idir=IDIR)
        self.spectrum.read_labels_from_file_auto(idir=IDIR)

        # 今開いたファイル名
        if self.loaded_file_path:
            self.loaded_file_path.destroy() # 初期化
        self.loaded_file_path = customtkinter.CTkLabel(master=self, text=self.spectrum.path, wraplength=600)
        self.loaded_file_path.grid(row=2, column=1, columnspan=5, padx=10, pady=(0,10), sticky="ew")

        # combo更新
        self.y_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                            values=self.spectrum.label_list)
        self.y_legend_combo.grid(row=1, column=4, padx=10, pady=(0,10), sticky="w")

        self.x_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                            values=self.spectrum.label_list)
        self.x_legend_combo.grid(row=1, column=2, padx=10, pady=(0,10), sticky="w")  

        try:
            # plot_data_frameを初期化
            self.destroy_widgets(self.master.plot_data_frame, 1)
        except AttributeError:
            pass

    # loadボタンを押したときにファイルを読み込む
    def load_button_callback(self, plot_spectrum=True):
        #  dataの読み込み
        # self.spectrum.load_data_from_csv_file(self.x_legend_combo.get(), self.y_legend_combo.get(), plot_spectrum=False)
        # plot_data_frameを使用しているときの処理
        if self.has_plot_data_frame:
            self.spectrum.load_xy_data_from_file_auto(self.x_legend_combo.get(), self.y_legend_combo.get(), plot_spectrum=False)
            # plot_data_frameを初期化
            self.destroy_widgets(self.master.plot_data_frame, 1)
            # 読み込んだスペクトルを表示
            self.master.plot_data_frame.plot_observed_spectrum(self.spectrum.x, self.spectrum.y)
        else:
            self.spectrum.load_xy_data_from_file_auto(self.x_legend_combo.get(), self.y_legend_combo.get(), plot_spectrum=True)
        # flagの初期化 (もっといい方法があるはず)
        global flag_peak_detection
        flag_peak_detection=False
        global flag_bg
        flag_bg=False

    def destroy_widgets(self, frame, row_number):
    # 配置されたウィジットの情報を取得
        children = frame.winfo_children()
        # row_number行目以下にウィジットがあるかどうかをチェック 
        for child in reversed(children): # reverseにすると時短。reverseしないと消すつもりの図が何度も描画され、時間がかかる。
            if child.grid_info()['row'] >= row_number:
                # 5行目以下にウィジットがある場合、削除する
                child.destroy()


# save data
class SaveDataFrame(customtkinter.CTkFrame): #GUI下部
    def __init__(self, spectrum, analysis, deconvoluted_spectrum=None, header_name="Save Data", **kwargs):
        super().__init__(**kwargs)

        self.header_name=header_name
        self.fonts = (FONT_TYPE, 15)
        # mainで行った解析データ
        self.spectrum = spectrum
        self.analysis = analysis
        # 追加で行った解析データ
        self.deconvoluted_spectrum = deconvoluted_spectrum
        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
    # フレームのラベルを表示
        self.label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        self.label.grid(row=0, column=0, padx=10, sticky="w")      
        # saveボタン生成
        save_button = customtkinter.CTkButton(master=self, command=self.button_save_callback, text="Save", font=self.fonts)
        save_button.grid(row=1, column=0, columnspan=1, padx=10, pady=(0,10), sticky="ew")
        saved_file_path_label = customtkinter.CTkLabel(master=self, text='Saved File:')
        saved_file_path_label.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
        
        note_label = customtkinter.CTkLabel(master=self, text='Comment:')
        note_label.grid(row=1, column=2, padx=10, pady=(0,10), sticky="ew")
        self.info_note_textbox = customtkinter.CTkEntry(master=self, placeholder_text="[Info]", width=120, font=self.fonts)
        self.info_note_textbox.grid(row=1, column=3, padx=10, pady=(0,10), sticky="ew")

        self.file_note_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Filename", width=120, font=self.fonts)
        self.file_note_textbox.grid(row=1, column=4, padx=10, pady=(0,10), sticky="ew")

        self.label_note_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Legend Name", width=120, font=self.fonts)
        self.label_note_textbox.grid(row=1, column=5, padx=(10,10), pady=(0,10), sticky="ew")

    def button_save_callback(self):
        #エントリーボックスから但し書きを得る
        info_note = self.info_note_textbox.get()
        if self.file_note_textbox.get()!="":
            path_note = f"_{self.file_note_textbox.get()}"
        else:
            path_note = ""
        if self.label_note_textbox.get()!="":
            legend_note = f"_{self.label_note_textbox.get()}"
        else:
            legend_note = ""

        # mainで行った結果を保存
        self.spectrum.save_results(self.analysis,
                                is_GUI = True, 
                                info_note = info_note, 
                                path_note = path_note,
                                legend_note = legend_note)

        # ピークエネルギー検出したとき追加で保存
        if self.deconvoluted_spectrum != None:
            self.deconvoluted_spectrum.save_results("peak_detection",
                                                    is_GUI = True, 
                                                    info_note = info_note, 
                                                    path_note = path_note,
                                                    legend_note = legend_note)


        saved_path_label = customtkinter.CTkLabel(master=self, text=self.spectrum.savefile_path, wraplength=580)
        saved_path_label.grid(row=2, column=1, columnspan=8, padx=10, pady=(0,10), sticky="ew")

    def update_deconvoluted_spectrum(self, new_spectrum):
        self.deconvoluted_spectrum = new_spectrum
        # 必要に応じて他の更新処理を追加

# image ##################


class LoadImageDataFrame(customtkinter.CTkFrame):
# image data
# load data frame
    def __init__(self, master=None, header_name="Load Data", has_plot_data_frame=None, **kwargs):
        super().__init__(master)

        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.master = master
        self.image = []
        self.spectrum = []
        self.import_mode = []
        self.fig_instance_lst=[]
        self.has_plot_data_frame=has_plot_data_frame
        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        label.grid(row=0, column=0, columnspan=1, padx=10, sticky="w")
        # title
        # load_data_label = customtkinter.CTkLabel(self, text='Load Data:', font=self.fonts, width=130)
        # load_data_label.grid(row=1, column=0, padx=10, pady=(10,5), sticky="ew")
         # loadボタン
        load_file_button = customtkinter.CTkButton(self, command=self.load_file_button_callback, text="Load", font=self.fonts)
        load_file_button.grid(row=1, column=0, padx=(10,10), pady=(0,5), sticky="w")

        self.file_type_combo = customtkinter.CTkComboBox(self, font=self.fonts, command=None, 
                                                    values=["Image (MBS; A-1)/General text",
                                                            "Spectrum (MBS; A-1)/General text",  
                                                            # "EDC(s) (csv or txt)"
                                                            ])
        self.file_type_combo.grid(row=1, column=1, padx=(0, 10), pady=(0,5), sticky="ew")

        # self.x_label_combo = customtkinter.CTkComboBox(self, font=self.fonts, command=None, 
        #                                             values=["---X Legend---", "First Column"], width=130)
        # self.x_label_combo.grid(row=0, column=2, padx=(0, 9), pady=(10,5), sticky="ew")
        # self.y_label_combo = customtkinter.CTkComboBox(self, font=self.fonts, command=None, 
        #                                             values=["---Y Legend---", "All"], width=130)
        # self.y_label_combo.grid(row=0, column=3, padx=(0, 9), pady=(10,5), sticky="ew")
         # openボタン
        # open_file_button = customtkinter.CTkButton(self, command=self.open_file_button_callback, text="Open", font=self.fonts, width=120)
        # open_file_button.grid(row=0, column=4, padx=(0,8), pady=(10,5), sticky="w")
        # パスを表示
        
        file = customtkinter.CTkLabel(self, text='Imported File:')
        file.grid(row=2, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        self.file_label=None


    def load_file_button_callback(self):
        # 初期化
        self.import_mode.clear()
        self.import_mode.append(self.file_type_combo.get())
        
        # photoemission intensity map インスタンス生成
        if self.import_mode[0]=="Spectrum (MBS; A-1)/General text" or self.file_type_combo.get()=="Image (MBS; A-1)/General text":
            self.image.clear()
            self.image.append(MBS_A1(idir=IDIR)) # imageに格納して、以下image[0]でインスタンスを指定する。
            if self.image[0].x_label=="Binding Energy (eV)":
                self.x=self.image[0].EF
            elif self.image[0].x_label=="Kinetic Energy (eV)" or 'X':
                self.x=self.image[0].x

            self.y=self.image[0].y
            # print(self.y)

            self.x_min=np.amin(self.x)
            self.x_max=np.amax(self.x)
            self.y_min=np.amin(self.y)
            self.y_max=np.amax(self.y)
            self.z_min=np.amin(self.image[0].z)
            self.z_max=np.amax(self.image[0].z)

        elif self.import_mode[0]=="csv file":
            self.image.clear()
            self.image.append(Spectrum(IDIR))

        # print(self.image[0].z)

        # pathのエントリーボックスを初期化して追記
        if self.file_label is not None:
            rpc.destroy_widget_by_variable(self, self.file_label)
        self.file_label = customtkinter.CTkLabel(master=self, text=self.image[0].filename)
        self.file_label.grid(row=2, column=1, padx=(0,10), pady=(0,5), sticky="ew", columnspan=2)            


        if self.import_mode[0]=="Spectrum (MBS; A-1)/General text":
            # インスタンス作製
            self.edcs_pltctrl = PlotControl(title=f"Imported EDC(s):\n{self.image[0].filename}", 
                                            plt_interaction=True, initialize_figs=False, figsize_w=4, figsize_h=3.5, fontsize=10,
                                            x_label=self.image[0].x_label, y_label="Intensity (cps)")
            # print(self.image[0].z_offset_edcs_lst)
            for i in range(len(self.image[0].z)):
                try:
                    z_offset=self.image[0].z_offset_edcs_lst[i] # offset量を計算
                except (TypeError, IndexError):
                    z_offset=0
                # plot
                self.edcs_pltctrl.add_spectrum(self.x, self.image[0].z[i]+z_offset, label=None, linewidth=1, scatter=False, color=SPECTRAL_COLOR)

            if self.image[0].x_label=="Binding Energy (eV)":
                self.edcs_pltctrl.ax.invert_xaxis()
            self.edcs_pltctrl.update_canvas()
            self.fig_instance_lst.append(self.edcs_pltctrl)

        elif self.import_mode[0]=="Image (MBS; A-1)/General text":
            # インスタンス作製
            self.image_pltctrl = ImagePlotControl(self.y, self.x, self.image[0].z.T, 
                                                  title=f"Imported Image:\n{self.image[0].filename}", plt_interaction=True, figsize_h=3.5, figsize_w=4,
                                                  x_label=self.image[0].y_label, y_label=self.image[0].x_label, z_label=self.image[0].z_label, 
                                                  colormap=COLORMAP,
                                                  slider=True
                                                  )
            if self.image[0].x_label=="Binding Energy (eV)":
                self.image_pltctrl.ax.invert_yaxis()
            self.fig_instance_lst.append(self.image_pltctrl)


    def close_figs_button_callback(self):
        """すべてのインスタンスの図を閉じる"""
        for instance in self.fig_instance_lst:  # リストをコピーしてイテレート
            if isinstance(instance, ImagePlotControl):
                instance.close_image()  # 各インスタンスのcloseメソッドを呼ぶ
            elif isinstance(instance, PlotControl):
                instance.clear_plot()  # 各インスタンスのcloseメソッドを呼ぶ
        print("All plots closed.")


class SaveDataFrame2(customtkinter.CTkFrame):
# load data frame
    def __init__(self, master=None, header_name="Save Data", has_plot_data_frame=None, image=None, spectrum=None, save_param_lst=[], save_data_lst=[], analysis=None, **kwargs):
        super().__init__(master)
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.master = master
        self.image = image
        self.spectrum = spectrum
        self.import_mode = []
        self.has_plot_data_frame=has_plot_data_frame
        self.save_param_lst=save_param_lst
        self.save_data_lst=save_data_lst
        self.analysis=analysis
        # setup
        self.setup_form()


    def setup_form(self):
        # title
        label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        label.grid(row=0, column=0, columnspan=1, padx=10, sticky="w")

         # loadボタン
        save_file_button = customtkinter.CTkButton(self, command=self.save_button_callback, text="Save", font=self.fonts, width=120)
        save_file_button.grid(row=1, column=0, padx=(0,10), pady=(0,10), sticky="w")

    def update_save_filename(self):
        if self.analysis=="second_derivative":
            self.filename_entry.insert(0, f"{self.image[0].filename}_2Der")
        if self.analysis=="1D (Energy)":
            self.filename_entry.insert(0, f"{self.image[0].filename}_1CuvX")
        if self.analysis=="2D":
            self.filename_entry.insert(0, f"{self.image[0].filename}_2Cuv")

    def save_button_callback(self):
        pass

# spinbox用 ########################################
# app = customtkinter.CTk()

# spinbox_1 = FloatSpinbox(app, width=150, step_size=3, callback=my_callback)
# spinbox_1.pack(padx=20, pady=20)

# spinbox_1.set(35)
# print(spinbox_1.get())

# app.mainloop()
###################################################