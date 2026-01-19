import customtkinter
import copy
import numpy as np
import platform
from pathlib import Path
import subprocess
from tkinter import messagebox
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

from RyoPy import defs_for_analysis as rpa
from RyoPy import defs_for_ctk as rpc
from RyoPy.PlotControl import PlotControl, ImagePlotControl
from RyoPy.Frame import LoadImageDataFrame
from setting.setting import App as SettingApp 

# srcディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent
# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
second_derivative_setting_path = os.path.join(SRC_PATH, "setting", "second_derivative_setting.txt")

# ファイル選択するときの初期値
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
USER, has_USER = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")
WINDOW_WIDTH, has_WINDOW_WIDTH = rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "window_width_deconv")
WINDOW_height, has_WINDOW_height = rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "window_height_deconv", type="str")
# font
FONT_TYPE = "Arial"  # デフォルト値
FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")

COLORMAP, has_COLORMAP = rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "colormap_photoemission_intensity_map", type="str")
# COLORMAP = 'viridis'

# second derivativeのcolor map
# COLORMAP_SECOND_DERIVATIVE="bwr_r"
# COLORMAP_SECOND_DERIVATIVE="viridis"
# COLORMAP_SECOND_DERIVATIVE='YlGnBu_r'
# COLORMAP_SECOND_DERIVATIVE='Spectral_r'
COLORMAP_SECOND_DERIVATIVE_='Blues_r'

COLORMAP_SECOND_DERIVATIVE, has_SD_COLORMAP=rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "colormap_second_derivative", type="str")
if not has_SD_COLORMAP:
    COLORMAP_SECOND_DERIVATIVE = COLORMAP_SECOND_DERIVATIVE_
print(COLORMAP_SECOND_DERIVATIVE)

COLORMAP, has_COLORMAP = rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "colormap_photoemission_intensity_map", type="str")

# EDC(s)　plotのカラー
SPECTRAL_COLOR_='darkslateblue'
SPECTRAL_COLOR, has_SPECTRAL_COLOR = rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "color_edc", type="str")
if not has_SPECTRAL_COLOR:
    SPECTRAL_COLOR=SPECTRAL_COLOR_

VERSION_NUMBER, hoge=rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "version", type="str")
USER, hoge=rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")

has_CURVATURE_FRAME=False
has_SECOND_DERIVATIVE_FRAME=True

# 大枠
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # メンバー変数の設定
        self.fonts = (FONT_TYPE, 15)
        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # CustomTkinter のフォームデザイン設定
        customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
        customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

        # フォームサイズ設定
        if has_WINDOW_height and has_WINDOW_WIDTH:
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_height}")
        else:
            self.geometry("1750, 750")

        if has_SECOND_DERIVATIVE_FRAME:
            self.title('SpecTaroscoPy — Second Derivative')
        if has_CURVATURE_FRAME:
            self.title('SpecTaroscoPy — Curvature')

        #アイコン
        # try:
        #     if platform.system() == "Darwin":  # macOS
        #         img_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'second_derivative.png')
        #         if os.path.exists(img_path):
        #             icon_image = PhotoImage(file=img_path).subsample(2, 2)  # 2倍に縮小（調整可能）
        #             self.tk.call('wm', 'iconphoto', self._w, icon_image)
        #     elif platform.system() == "Windows":  # Windows
        #         ico_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'second_derivative.ico')
        #         if os.path.exists(ico_path):
        #             self.iconbitmap(ico_path)
        # except:
        #     pass

        # 行方向のマスのレイアウトを設定する。リサイズしたときに一緒に拡大したい行をweight 1に設定。
        self.grid_rowconfigure(2, weight=1)
        # 列方向のマスのレイアウトを設定する
        self.grid_columnconfigure(1, weight=1) 
        
        # 1つ目のフレームの設定
        # stickyは拡大したときに広がる方向のこと。nsew で4方角で指定する。
        self.load_data_frame = LoadImageDataFrame(master=self, colormap=COLORMAP)
        self.load_data_frame.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew", columnspan=2)

        # 2つ目のフレーム Second Derivative
        self.second_derivative_frame = SecondDerivativeFrame(master=self, 
                                                             spectrum=self.load_data_frame.spectrum, 
                                                             image=self.load_data_frame.image,
                                                             import_mode=self.load_data_frame.import_mode,
                                                             imported_fig_instance_lst=self.load_data_frame.fig_instance_lst,
                                                             ) 
        self.second_derivative_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew", columnspan=2)

        # open manualボタン
        self.manual_button = customtkinter.CTkButton(master=self, text="Open Manual", font=self.fonts, command=self.open_manual_button_callback)
        self.manual_button.grid(row=100, column=0, padx=(20, 10), pady=(0,10), sticky="esnw")

        # Settingボタン
        setting_button = customtkinter.CTkButton(self, command=self.open_setting, text="Setting", font=self.fonts)
        setting_button.grid(row=100, column=1, padx=(0, 20), pady=(0, 10), sticky="esnw")


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
        initial_tab = "2nd Div"  # タブを初期表示
        app = SettingApp(initial_tab=initial_tab)
        app.resizable(True, True)
        app.mainloop()

class SecondDerivativeFrame(customtkinter.CTkFrame): # GUI中部
    def __init__(self, *args, header_name="", spectrum=None, image=None, import_mode=None, imported_fig_instance_lst=[],
                second_derivative=True, curvature=False, **kwargs):
        super().__init__(*args, **kwargs)
                
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.image = image
        self.spectrum = spectrum
        self.import_mode = import_mode
        self.imported_fig_instance_lst=imported_fig_instance_lst
        self.fig_instance_lst=[]
        self.has_second_derivative_frame=second_derivative
        self.has_curvature_frame=curvature
        self.save_param_lst=[]
        self.save_data_lst=[]
        self.image_curvature_pltctrl=None

        self.y_2der_offset = []
        self.order_detect_peak=None
        
        # if curvature==False:
        #     self.z_curvature=None

        # rowを指定
        self.ROW_START_FITTING_PARAMS = 2 # parameter行は2-48行
        self.ROW_START_CURVATURE_PARAMS = 50 # curvature paramは50-89行
        # peak detectは90-100行
        self.ROW_DO_IT_BUTTONS = 100 # do it buttonなど
        # save buttonは200行目

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        label = customtkinter.CTkLabel(self, text='--- Smoothing ---', font=(FONT_TYPE, 11))
        label.grid(row=0, column=0, columnspan=1, padx=10, sticky="w")

        file_label = customtkinter.CTkLabel(self, text='Method', width=120)
        file_label.grid(row=self.ROW_START_FITTING_PARAMS-1, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        # スムージング方法を選ぶコンボボックス
        self.smoothing_method_combo = customtkinter.CTkComboBox(self, font=self.fonts, command=self.choice_smoothing_method_combo_callback, 
                                                                values=[
                                                                    "Savitzky-Golay", 
                                                                    "Binomial",
                                                                    "None"
                                                                    ], 
                                                                    width=120)
        self.smoothing_method_combo.grid(row=self.ROW_START_FITTING_PARAMS-1, column=1, padx=(0, 10), pady=(0,5), sticky="ew")
        self.choice_smoothing_method_combo_callback(0)

        # EDC(s)のときのY offset value
        y_offset_label = customtkinter.CTkLabel(master=self, text="Y Offset")
        y_offset_label.grid(row=20, column=0, padx=10, pady=(0,5), sticky="ew")
        self.y_offset_entry = customtkinter.CTkEntry(master=self, placeholder_text="強度", width=120, font=self.fonts) # 入力
        self.y_offset_entry.grid(row=20, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.y_offset_entry.insert(0, 0)

        # SmoothingしたときのRMSE計算
        # label = customtkinter.CTkLabel(master=self, text="RMSE (Only EDC Mode)")
        # label.grid(row=40, column=0, padx=10, pady=(0,10), sticky="ew")
        # rmse_checkbox_value = customtkinter.BooleanVar() # チェックボックスの変数を作成し、初期値をTrueに設定
        # rmse_checkbox_value.set(False)
        # self.rmse_checkbox = customtkinter.CTkCheckBox(master=self, text="", variable=rmse_checkbox_value, width=20)
        # self.rmse_checkbox.grid(row=40, column=1, padx=(0,0), pady=(0,10), sticky="ew")    

        # フレームのラベルを表示
        if self.has_second_derivative_frame:
            label = customtkinter.CTkLabel(self, text="--- Second Derivative ---", font=(FONT_TYPE, 11))
        elif self.has_curvature_frame:
            label = customtkinter.CTkLabel(self, text="--- Curvature ---", font=(FONT_TYPE, 11))
        label.grid(row=48, column=0, columnspan=1, padx=10, pady=(10,5), sticky="w")

        # curvature method
        if self.has_curvature_frame==True:
            curvature_label = customtkinter.CTkLabel(master=self, text="Method")
            curvature_label.grid(row=self.ROW_START_CURVATURE_PARAMS-1, column=0, padx=10, pady=(5,5), sticky="ew")        
            # curvature methodを選ぶコンボボックス
            self.curvature_method_combo = customtkinter.CTkComboBox(self, font=self.fonts, command=self.choice_curvature_method_combo_callback, 
                                            values=[
                                                "1D (Energy)",
                                                "2D"
                                                ], 
                                                width=120)
            self.curvature_method_combo.grid(row=self.ROW_START_CURVATURE_PARAMS-1, column=1, padx=(0, 10), pady=(5,5), sticky="ew")   

            # parameter配置
            self.choice_curvature_method_combo_callback(0)

        # DetectPeak
        customtkinter.CTkLabel(master=self, text="Detect Peaks").grid(row=91, column=0, padx=10, pady=(0,5), sticky="ew")
        detect_peak_checkbox_value = customtkinter.BooleanVar() # チェックボックスの変数を作成し、初期値をTrueに設定
        detect_peak_checkbox_value.set(True)
        self.detect_peak_checkbox = customtkinter.CTkCheckBox(master=self, text="", variable=detect_peak_checkbox_value, width=20)
        self.detect_peak_checkbox.grid(row=91, column=1, padx=(0,0), pady=(0,5), sticky="ew")

        # EDC(s)のときのY offset value
        customtkinter.CTkLabel(master=self, text="Sensitivity\n(Smaller is more sensitive.)").grid(row=92, column=0, padx=10, pady=(0,5), sticky="ew")
        self.order_entry = customtkinter.CTkEntry(master=self, placeholder_text="ピーク検出感度 (正数で小さいほうが高感度)", width=120, font=self.fonts) # 入力
        self.order_entry.grid(row=92, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        self.order_entry.insert(0, 1)

        # X範囲指定
        customtkinter.CTkLabel(master=self, text="Min X").grid(row=93, column=0, padx=10, pady=(0,5), sticky="ew")
        self.x_min_entry = customtkinter.CTkEntry(master=self, placeholder_text="最小エネルギー (eV)", width=120, font=self.fonts) # 入力
        self.x_min_entry.grid(row=93, column=1, padx=(0,10), pady=(0,5), sticky="ew") 

        # X範囲指定
        customtkinter.CTkLabel(master=self, text="Max X").grid(row=94, column=0, padx=10, pady=(0,5), sticky="ew")
        self.x_max_entry = customtkinter.CTkEntry(master=self, placeholder_text="最大エネルギー (eV)", width=120, font=self.fonts) # 入力
        self.x_max_entry.grid(row=94, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        # do it ボタン作成
        do_it_button = customtkinter.CTkButton(master=self, command=self.do_it_button_callback, text="Do It", font=self.fonts)
        do_it_button.grid(row=100, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        #Close ボタン生成
        close_button = customtkinter.CTkButton(master=self, command=self.close_figs_button_callback, text="Close Figures", font=self.fonts)
        close_button.grid(row=100, column=0, padx=(10,10), pady=(0,5), sticky="ew")
        

        # data save部分
        customtkinter.CTkLabel(self, text="--- Save Data ---", font=(FONT_TYPE, 11)).grid(row=198, column=0, columnspan=1, padx=10, pady=(10,5), sticky="w")
        customtkinter.CTkLabel(master=self, text="Output Filename", font=self.fonts).grid(row=199, column=0, padx=10, pady=(0,5), sticky="ew")
        self.savefile_entry = customtkinter.CTkEntry(master=self, placeholder_text="Filename", width=120, font=self.fonts) # 入力
        self.savefile_entry.grid(row=199, column=1, padx=(0,10), pady=(0,5), sticky="ew")  
        #Save ボタン生成
        close_button = customtkinter.CTkButton(master=self, command=self.save_button_callback, text="Save", font=self.fonts)
        close_button.grid(row=200, column=1, padx=(0,10), pady=(0,10), sticky="ew")


    def choice_smoothing_method_combo_callback(self, _): # 2から49行目までを使用できる。
        # widgetsの初期化
        rpc.destroy_widget_by_row(self, self.ROW_START_FITTING_PARAMS, upper_row_limit=19)
        
        # プルダウンメニューで選択された値を取得
        self.smoothing_method = self.smoothing_method_combo.get()  

        self.smoothing_params={
            "Savitzky-Golay":   {
                                "labels": ("Order Number", "Window Size", "Iteration Number"),
                                "placeholders": ("正数", "次数以上の「奇数」", "正数"),
                                "defaults": (2, False, False)
                                },
            "Binomial": {
                        "labels": ("Order Number", "Iteration Number"),
                        "placeholders": ("正数", "正数"),
                        "defaults": (False, False)
                        },
            "None": {
                    "labels": [],
                    "placeholders": [],
                    "defaults": []
                    }
            }

        # parameterの数だけ表示する
        if self.smoothing_method in self.smoothing_params:
            print(f"You chosed {self.smoothing_method}.")
            params = self.smoothing_params[self.smoothing_method]
            for i, (label, placeholder, default) in enumerate(zip(params["labels"], params["placeholders"], params["defaults"])):
                smoothing_param_label = customtkinter.CTkLabel(master=self, text=label)
                smoothing_param_label.grid(row=self.ROW_START_FITTING_PARAMS+i, column=0, padx=10, pady=(0,5), sticky="ew")
                smoothing_param_entry = customtkinter.CTkEntry(master=self, placeholder_text=placeholder, width=120, font=self.fonts)
                smoothing_param_entry.grid(row=self.ROW_START_FITTING_PARAMS+i, column=1, padx=(0,10), pady=(0,5), sticky="ew")
                if default is not False:  # 初期値が指定されている場合のみ
                    smoothing_param_entry.insert(0, default)

    def choice_curvature_method_combo_callback(self, _):
        # widgetsの初期化
        rpc.destroy_widget_by_row(self, self.ROW_START_CURVATURE_PARAMS, upper_row_limit=70)

        # プルダウンメニューで選択された値を取得
        self.curvature_method = self.curvature_method_combo.get()

        # 曲率メソッドごとのパラメータ設定
        self.curvature_params = {
                "1D (Energy)":   {
                        "labels": ("a0",),
                        "placeholders": ("正数",),
                        "defaults": (0.0005,)
                        },
                "2D":   {
                        "labels": ("準備中",),
                        "placeholders": ("正数",),
                        "defaults": (False,)
                        }
                }

        # 選択されたメソッドに対応するパラメータを取得
        if self.curvature_method in self.curvature_params:
            params = self.curvature_params[self.curvature_method]
            # パラメータに基づいてUIを生成
            for i, (label, placeholder, default) in enumerate(zip(params["labels"], params["placeholders"], params["defaults"])):
                # ラベル作成
                curvature_param_label = customtkinter.CTkLabel(master=self, text=label)
                curvature_param_label.grid(row=self.ROW_START_CURVATURE_PARAMS + i, column=0, padx=10, pady=(0, 5), sticky="ew")
                # エントリー作成
                curvature_param_entry = customtkinter.CTkEntry(master=self, placeholder_text=placeholder, width=120, font=self.fonts)
                curvature_param_entry.grid(row=self.ROW_START_CURVATURE_PARAMS + i, column=1, padx=(0, 10), pady=(0, 5), sticky="ew")
                # 初期値が指定されていれば設定
                if default is not False:
                    curvature_param_entry.insert(0, default)

    def close_figs_button_callback(self):
        """すべてのインスタンスの図を閉じる"""
        # SecondDerivativeFrameで生成したfigureを消す
        for instance in self.fig_instance_lst:  # リストをコピーしてイテレート
            instance.close_figure()

        # LoadDataFrame2で生成したfigureを消す
        for instance in self.imported_fig_instance_lst:
            instance.close_figure()
        
        print("All plots closed.")


    def smooth_data(self):
        """
        選択されたスムージング方法に基づき、データをスムージングする。
        """
        # 入力されたスムージングパラメータ値を格納する
        self.smoothing_param_values = []

        # パラメータの抽出
        try:
            row_start = self.ROW_START_FITTING_PARAMS
            params = self.smoothing_params[self.smoothing_method]  # 辞書型から取得
            for i, label in enumerate(params["labels"]):
                value, _ = rpc.get_input_values_in_widgets_by_row_column(self, row_start + i, 1)
                if value == "":
                    raise ValueError(f"'{label}' パラメータが未入力です。")
                self.smoothing_param_values.append(float(value))  # 数値に変換
        except ValueError as e:
            print(f"パラメータエラー: {e}")
            return
        except KeyError:
            print(f"無効なスムージング方法: {self.smoothing_method}")
            return

        # RMSEを計算するかどうかのチェック
        flag_calc_RMSE = False
        try:
            if hasattr(self, "rmse_checkbox") and self.rmse_checkbox.get():
                flag_calc_RMSE = True
        except AttributeError:
            pass

        # スムージング処理
        # print(self.image[0].z)
        if self.smoothing_method == "Savitzky-Golay":
            order, window_size, iterations = self.smoothing_param_values
            print(f"スムージングパラメータ - 次数: {order}, 点数: {window_size}, 繰り返し数: {iterations}")
            if window_size % 2 == 0:
                messagebox.showerror("Parameter Error", "Window Size must be an odd number.")
                return
            self.z_smoothed = self.image[0].smooth_image_SG(
                                                            self.image[0].z, 
                                                            order, window_size, iterations
                                                            )
            # print(self.z_smoothed)
        elif self.smoothing_method == "Binomial":
            order, iterations = self.smoothing_param_values
            print(f"スムージングパラメータ - 次数: {order}, 繰り返し数: {iterations}")
            self.z_smoothed = self.image[0].smooth_image_binomial(
                                self.image[0].z, abs(self.x[0] - self.x[1]), 
                                order, iterations
                                )
        elif self.smoothing_method == "None":
            print("スムージングなしを選択しました。")
            self.z_smoothed = self.image[0].z

        # ログと結果の出力
        print("スムージング完了。")
    
        # 二次微分結果をplot
        title=f'Input Filename: {self.image[0].filename}'
        if self.smoothing_method=='Savitzky-Golay' and self.has_curvature_frame==False:
            title=f'Input Filename: {self.image[0].filename}\nSG params: Order {int(self.smoothing_param_values[0])}, {int(self.smoothing_param_values[1])} point(s), {int(self.smoothing_param_values[2])} iteration(s)'
        elif self.smoothing_method=='Binomial' and self.has_curvature_frame==False:
            title=f'Input Filename: {self.image[0].filename}\nSG params: Order {int(self.smoothing_param_values[0])}, {int(self.smoothing_param_values[1])} iteration(s)'
        # スムージング結果をplot
        if self.import_mode[0]=="Image (MBS, A-1)/General text":
            self.smoothed_image_pltctrl=ImagePlotControl(self.image[0].y, self.x, self.z_smoothed.T, 
                                                title=f'[Smoothing]\n{title}',
                                                plt_interaction=True, figsize_h=3.5, figsize_w=4,
                                                x_label=self.image[0].y_label, y_label=self.image[0].x_label, z_label=self.image[0].z_label, 
                                                colormap=COLORMAP,
                                                slider=True
                                                )
            # figureの画面上の位置を制御
            # self.smoothed_image_pltctrl.show_figure_at_position(800, 100)
            # 軸の向き変更
            if self.image[0].x_label=="Binding Energy (eV)":
                self.smoothed_image_pltctrl.ax.invert_yaxis()
            # インスタンスを管理するリスト
            self.fig_instance_lst.append(self.smoothed_image_pltctrl)

        if self.import_mode[0]=="Spectra (MBS, A-1)/General text":
            self.smoothed_edcs_pltctrl = PlotControl(title=f'[Smoothing]\n{title}', plt_interaction=True, initialize_figs=False, figsize_w=3.5, figsize_h=5.5, fontsize=10,
                                            x_label=self.image[0].x_label, y_label="Intensity (cps)")
            # figureの画面上の位置を制御

            # plot追加
            self.y_edc_offset=np.zeros(len(self.z_smoothed))
            for i in range(len(self.z_smoothed)):
                try:
                    if self.image[0].z_offset_edcs_lst is not None:
                        self.y_edc_offset[i]=self.image[0].z_offset_edcs_lst[i]
                except:
                    print('offset valueが得られません。')
                self.smoothed_edcs_pltctrl.add_spectrum(self.x, self.image[0].z[i]+self.y_edc_offset[i], label="", linewidth=1, scatter=False, color=SPECTRAL_COLOR)
                self.smoothed_edcs_pltctrl.add_spectrum(self.x, self.z_smoothed[i]+self.y_edc_offset[i], label="", linewidth=1, scatter=False, color='tab:orange')
            if self.image[0].x_label=="Binding Energy (eV)":
                self.smoothed_edcs_pltctrl.ax.invert_xaxis()
            self.smoothed_edcs_pltctrl.update_canvas()
            self.fig_instance_lst.append(self.smoothed_edcs_pltctrl)
            
        # RMSE計算をplot
        if flag_calc_RMSE:
            ###
            # RMSEの計算
            # ...
            ###
            self.rmse_pltctrl = PlotControl(title=f"RMSE of Smoothing Image\n{self.image[0].filename}", plt_interaction=True, initialize_figs=False, figsize_w=4, figsize_h=2.75, fontsize=10,
                                            x_label="Point Number", y_label="RMSE (cps)")
            self.rmse_pltctrl.add_spectrum(self.x_rmse, self.rmse, 
                                              label="", linewidth=1, scatter=True)
            # figureの出現位置を制御
            # self.rmse_pltctrl.show_figure_at_position(1000, 100)
            self.rmse_pltctrl.fig.tight_layout()
            self.fig_instance_lst.append(self.rmse_pltctrl)


    def do_curvature_button_callback(self):
        """
        Curvature ボタンが押された際の処理。
        スムージングを実行し、その後に曲率解析を行う。
        """
        self.peak_energy_lst=[]
        self.ddy_peak_intensity_lst=[]
        self.edcs_peak_intensity_lst=[]
        if self.image[0].EF is not None:
            self.x=self.image[0].EF
        else:
            self.x=self.image[0].x

        try:
            # スムージングを実行
            self.smooth_data()

            # 曲率パラメータを取得
            self.curvature_param_values = []
            params = self.curvature_params.get(self.curvature_method, {})
            row_start = self.ROW_START_CURVATURE_PARAMS
            for i, label in enumerate(params["labels"]):
                value, _ = rpc.get_input_values_in_widgets_by_row_column(self, row_start + i, 1)
                if value == "":
                    raise ValueError(f"'{label}' パラメータが未入力です。")
                self.curvature_param_values.append(float(value))  # 数値に変換

            # 曲率解析の実行
            if self.curvature_method == "1D (Energy)":
                a0 = self.curvature_param_values[0]
                print(f"Curvature Analysis パラメータ\ta0: {a0}")
                self.z_curvature = self.image[0].curvature_analysis(
                                        self.z_smoothed, axis=0, a0=a0, dimention=1
                                    )
                
                print("1D curvature解析が完了しました。")

            elif self.curvature_method == "2D":
                print("2D curvature解析は現在準備中です。")
                # 必要に応じて処理を追加

            else:
                raise ValueError(f"無効なcurvature解析方法: {self.curvature_method}")

        except ValueError as e:
            print(f"入力エラー: {e}")
        except KeyError:
            print(f"無効な曲率解析メソッド: {self.curvature_method}")
        except AttributeError as e:
            print(f"データロードエラー: {e}")
        except Exception as e:
            print(f"予期しないエラー: {e}")


        # peak detect
        if self.detect_peak_checkbox.get():
            self.detect_peak(mode="curvature")

        # ---- plot (common) ----
        self._plot_analysis_result_common(
                                        self.z_curvature,
                                        title=f"Curvature Analysis:\n{self.image[0].filename}",
                                        image_window_pos=(400, 200)  # curvatureで位置指定したいなら
                                        )     


    def _plot_analysis_result_common(self, z_result, title, *, image_window_pos=None):
        """
        2nd-derivative と curvature の描画を完全共通化する。

        Parameters
        ----------
        z_result : np.ndarray
            Spectrum mode: shape = (n_edc, n_points)
            Image mode:    shape = (n_x, n_y) or (n_y, n_x) いずれもOK（現状に合わせて .T を描画に使用）
        title : str
            Figure title
        image_window_pos : tuple[int,int] | None
            (x, y) を渡したら show_figure_at_position(x,y) を呼ぶ
        """

        # --- Image (MBS, A-1)/General text ---
        if self.import_mode[0] == "Image (MBS, A-1)/General text":
            pltctrl = ImagePlotControl(
                self.image[0].y, self.x, z_result.T,
                colormap=COLORMAP_SECOND_DERIVATIVE,
                title=title,
                plt_interaction=True, figsize_h=3.5, figsize_w=4,
                x_label=self.image[0].y_label, y_label=self.image[0].x_label, z_label=self.image[0].z_label,
                slider=True
            )

            if image_window_pos is not None:
                pltctrl.show_figure_at_position(*image_window_pos)

            if self.image[0].x_label == "Binding Energy (eV)":
                pltctrl.ax.invert_yaxis()

            self.fig_instance_lst.append(pltctrl)
            return

        # EDC stack plot
        ddy_edc_ctrl = PlotControl(
            title=f'[Second derivative]\n{title}', plt_interaction=True, initialize_figs=False,
            figsize_w=3.5, figsize_h=5.5, fontsize=10,
            x_label=self.image[0].x_label, y_label="Intensity (arb. units)"
        )

        # offset は一度だけ
        y_off = np.arange(len(z_result)) * float(self.y_offset_entry.get()) * -1

        edc_stack_ctrl = None
        if self.detect_peak_checkbox.get():
            edc_stack_ctrl = PlotControl(
                title=f"[EDCs stacking]\n{title}",
                plt_interaction=True, initialize_figs=False,
                figsize_w=3.5, figsize_h=5.5, fontsize=10,
                x_label=self.image[0].x_label, y_label="Intensity (cps)"
            )

        for i in range(len(z_result)):
            # 解析結果（2der / curvature 共通）
            ddy_edc_ctrl.add_spectrum(
                self.x, z_result[i] + y_off[i],
                label="", linewidth=1, scatter=False, color=SPECTRAL_COLOR
            )

            # 元スペクトル 
            edc_stack_ctrl.add_spectrum(
                self.x, self.image[0].z[i] + self.y_edc_offset[i],
                label="", linewidth=1, scatter=False, color=SPECTRAL_COLOR
            )

            if self.detect_peak_checkbox.get():

                # 2次微分/curvature上のピーク
                ddy_edc_ctrl.add_spectrum(
                    self.peak_energy_lst[i],
                    [p + y_off[i] for p in self.ddy_peak_intensity_lst[i]],
                    label="", linewidth=1.5, scatter=True,
                    color="none", edgecolor="tab:orange", linestyle="|", s=25, alpha=1
                )

                # 元スペクトル上のピーク
                edc_stack_ctrl.add_spectrum(
                    self.peak_energy_lst[i],
                    np.array(self.edcs_peak_intensity_lst[i]) + self.y_edc_offset[i],
                    label="", linewidth=1.5, scatter=True,
                    color="none", edgecolor="tab:orange", linestyle="|", s=25, alpha=1
                )
            

        # BE軸なら反転
        if self.image[0].x_label == "Binding Energy (eV)":
            ddy_edc_ctrl.ax.invert_xaxis()
            ddy_edc_ctrl.update_canvas()

            if edc_stack_ctrl:
                edc_stack_ctrl.ax.invert_xaxis()
                edc_stack_ctrl.update_canvas()

        self.fig_instance_lst.append(ddy_edc_ctrl)
        if edc_stack_ctrl:
            self.fig_instance_lst.append(edc_stack_ctrl)

        # band dispersion plot (E vs k//)
        # --- Spectra (MBS, A-1)/General text ---
        if self.import_mode[0] == "Spectra (MBS, A-1)/General text":
            if self.detect_peak_checkbox.get():
                # peak 波数プロット
                self.band_dispersion_pltctrl = PlotControl(title=f'[Peak plot]\n{title}', plt_interaction=True, initialize_figs=False, figsize_w=3, figsize_h=3.5, fontsize=10,
                                                x_label=self.image[0].y_label, y_label=self.image[0].x_label)
                
                # plot追加
                for i in range(len(self.peak_energy_lst)):
                    for j in range(len(self.peak_energy_lst[i])):
                        self.band_dispersion_pltctrl.add_spectrum(self.image[0].y_slice_center_edcs[i], self.peak_energy_lst[i][j], 
                                                                label=None, color='tab:orange')
                
            if self.image[0].x_label=="Binding Energy (eV)":
                self.band_dispersion_pltctrl.ax.invert_yaxis()
            self.fig_instance_lst.append(self.band_dispersion_pltctrl)

    def do_it_button_callback(self):
        # 二次微分 or curvature 解析を実行. plot
        if self.has_second_derivative_frame:
            self.do_second_derivative_button_callback()
        elif self.has_curvature_frame:
            self.do_curvature_button_callback()
        
        # loadしたfilename 更新
        filename=self.image[0].filename
        
        # 二次微分のときの処理
        if self.has_second_derivative_frame:
            savefile_path = filename.replace(".txt", "_2Der.txt")
        # 曲率解析のときの処理
        elif self.has_curvature_frame and self.curvature_method=="1D (Energy)":
            savefile_path = filename.replace(".txt", "_CurX.txt") # セーブファイル名
        elif self.has_curvature_frame and self.curvature_method=="2D":
            savefile_path = filename.replace(".txt", "_CurXY.txt") # セーブファイル名
        # Entryに表示
        self.savefile_entry.delete(0, customtkinter.END)
        self.savefile_entry.insert(0, savefile_path)

    def do_second_derivative_button_callback(self):
        if self.image[0].EF is not None:
            self.x = self.image[0].EF
        else:
            self.x = self.image[0].x

        self.peak_energy_lst = []
        self.ddy_peak_intensity_lst = []
        self.edcs_peak_intensity_lst = []

        # smoothing
        self.smooth_data()
        
        # 二次微分
        self.z_second_derivative = self.image[0].second_derivative(self.z_smoothed, axis=0)
        print("Second derivative is finished.")

        # ピーク検出
        if self.detect_peak_checkbox.get():
            if self.smoothing_method == 'None':
                self.detect_peak(mode='raw_data')
            else:
                self.detect_peak(mode="second_derivative")

        # title
        title = f'Peak Plot: {self.image[0].filename}'
        if self.smoothing_method == 'Savitzky-Golay' and self.has_curvature_frame == False:
            title = (
                f'Input Filename: {self.image[0].filename}\n'
                f'SG params: Order {int(self.smoothing_param_values[0])}, {int(self.smoothing_param_values[1])} point(s), {int(self.smoothing_param_values[2])} iteration(s)'
            )
        elif self.smoothing_method == 'Binomial' and self.has_curvature_frame == False:
            title = (
                f'Input Filename: {self.image[0].filename}\n'
                f'Binomial params: Order {int(self.smoothing_param_values[0])}, {int(self.smoothing_param_values[1])} iteration(s)'
            )

        self._plot_analysis_result_common(self.z_second_derivative, title)


    def detect_peak(self, mode):
        another_z=None # 初期化
        if mode == "second_derivative":
            z = copy.deepcopy(self.z_second_derivative)
            # print("a")
        elif mode == "curvature":
            z = copy.deepcopy(self.z_curvature)
        elif mode == 'raw_data':
            z = copy.deepcopy(-self.z_smoothed)

        if self.x_max_entry.get() != "" and self.x_min_entry.get() != "":
            x_max = float(self.x_max_entry.get())
            x_min = float(self.x_min_entry.get())

            # x をスライス
            idx_min = rpa.get_idx_of_the_nearest(self.x, x_min)
            idx_max = rpa.get_idx_of_the_nearest(self.x, x_max)
            
            # スライス順序を保証
            if idx_min > idx_max:
                idx_min, idx_max = idx_max, idx_min

            x = self.x[idx_min:idx_max]
            # z をサブリストごとにスライス
            z = [sublist[idx_min:idx_max] for sublist in z] # 二次微分やcurvature
            
            another_z = [sublist[idx_min:idx_max] for sublist in self.image[0].z]
        
        else:
            x = self.x
            another_z = self.image[0].z


        self.order_detect_peak=self.order_entry.get()
        self.peak_energy_lst, self.ddy_peak_intensity_lst, self.edcs_peak_intensity_lst = self.image[0].detect_peaks_in_nested_list(x, z, order=self.order_detect_peak, z2_lst=another_z)
        

    def save_button_callback(self):
        directory_path = os.path.dirname(self.image[0].path) # ディレクトリパスを取得
        
        # 二次微分のときの処理
        if self.has_second_derivative_frame:
            # folder作成
            foldername=f"STPy_SecondDerivative"
            foldername=foldername.replace('.','_')
            rpa.create_folder_at_current_path(self.image[0].path, foldername)
            
            # filepath 作成
            savefile_path = os.path.join(directory_path, foldername, self.savefile_entry.get())

            # 二次微分スペクトル ファイル作成
            self.save_data(savefile_path, self.savefile_entry.get(), mode='2der', save_peaks=False)

            # peak detect file 作成
            if self.detect_peak_checkbox.get():
                if self.import_mode[0]!="Image (MBS, A-1)/General text":
                    self.save_data(savefile_path, self.savefile_entry.get(), mode='2der', save_peaks=True)

        # 曲率解析のときの処理
        elif self.has_curvature_frame and self.curvature_method=="1D (Energy)":
            foldername=f"STPy_1DCurvatureX"
            foldername=foldername.replace('.','_')
            rpa.create_folder_at_current_path(self.image[0].path, foldername) # フォルダ作成
            savefile_path = os.path.join(directory_path, foldername, self.savefile_entry.get()) # セーブファイルのパス作成
            self.save_data(savefile_path, self.savefile_entry.get(), mode='curX')
            # peak detect file 作成
            if self.detect_peak_checkbox.get():
                if self.import_mode[0]!="Image (MBS, A-1)/General text":
                    self.save_data(savefile_path, self.savefile_entry.get(), mode='curX', save_peaks=True)

        elif self.has_curvature_frame and self.curvature_method=="2D":
            foldername=f"STPy_2DCurvature" 
            foldername=foldername.replace('.','_')
            rpa.create_folder_at_current_path(self.image[0].path, foldername)
            savefile_path = os.path.join(directory_path, foldername, self.savefile_entry.get())
            self.save_data(savefile_path, self.savefile_entry.get(), mode='curXY')
            # peak detect file 作成
            if self.detect_peak_checkbox.get():
                if self.import_mode[0]!="Image (MBS, A-1)/General text":
                    savefile_path = savefile_path.replace(".txt", "Peak.txt")
                    self.save_data(savefile_path, self.savefile_entry.get(), mode='curXY', save_peaks=True)


    def save_data(self, savefile_path, base_legendname, mode, save_peaks=False):
        # txt fileの中身
        filename=base_legendname.replace(".txt","")

        def save(savefile_path, filename=filename):
            # DATA: 以降の行を取得
            data_index = self.image[0].l.index('DATA:') + 1
            # print(data_index)
            data_lines = self.image[0].l[data_index:]

            # ヘッダー作成
            added_header=[] #テキストファイルに出力する実験条件などを格納する変数

            added_header.append('')
            # title
            if mode=='2der':
                added_header.append("[SpecTaroscoPy — Second Derivative]")
            elif mode=='curX' or mode=='curXY':
                added_header.append("[SpecTaroscoPy — Curvature]")
            # info
            added_header.append('Author\tR Nakazawa')
            added_header.append('Contact\tnakazawa@ims.ac.jp')
            added_header.append(f"Version\t{VERSION_NUMBER}")
            added_header.append("--- info ---")
            added_header.append(f"User\t{USER}")
            added_header.append(f'File\t{self.image[0].filename}')     
            added_header.append(f"Smoothing Method\t{self.smoothing_method}")
            added_header.append("Smoothing Params\t" + ' '.join(map(str, self.smoothing_param_values)))
            added_header.append("Intensity Offset\t" + ' '.join(map(str, self.y_2der_offset)))
            # curvature
            if mode=='curX' or mode=='curXY':
                added_header.append(f'Curvature Method\t{self.curvature_method}')
                added_header.append('Curvature Parameters\t' + ' '.join(map(str, self.curvature_param_values)))

            # paek detectした時
            if save_peaks:
                added_header.append(f"Detect Peak\t{self.detect_peak_checkbox.get()}")
                added_header.append(f"Order (Detect Peak)\t{self.order_detect_peak}")
                added_header.append(f"X Min\t{self.x_min_entry.get()}")
                added_header.append(f"X Max\t{self.x_max_entry.get()}")
            
            added_header.append("")
            added_header.append("DATA:")

            # saveする数値データ作成
            data = [] # テキストファイルに出力する数値データを格納するリスト

            # ラベル追加
            # 数値データにラベルがあるか確認。ラベル付きの場合はラベルの末尾に2Der追記する。
            # DATA: の次の1行を取得
            next_DATA_line = self.image[0].l[data_index].strip().split()
            label=[]
            if not all(element.replace('.', '', 1).isdigit() for element in next_DATA_line):
                label_ = []
                label_.append(next_DATA_line)
                # 各要素の末尾に文字列を追記
                if mode=='2der' and save_peaks==False: #二次微分解析の場合
                    label_ = [[f"{element}2Der" for element in label] for label in label_]
                # print("Labels:", label_)
                elif mode=='curX' and save_peaks==False: #Curvature解析の場合
                    label_ = [[f"{element}CurX" for element in label] for label in label_]
                label="\t".join(label_[0]) if label_ else ""
            else:
                pass

            # データ追加
            # peak detect dataのsave
            if save_peaks:
                data.append(f'yc_{filename}_Peak\tx_{filename}_Peak\t{filename}_Peak\t{filename}_PeakOffset')
                for i in range(len(self.peak_energy_lst)):
                    for j in range(len(self.peak_energy_lst[i])):
                        y_slice_center=1
                        if self.image[0].y_slice_center_edcs!=[]:
                            y_slice_center=self.image[0].y_slice_center_edcs[i]
                        data.append(f'{y_slice_center}\t{self.peak_energy_lst[i][j]}\t{self.edcs_peak_intensity_lst[i][j]}\t{self.edcs_peak_intensity_lst[i][j]+self.y_edc_offset[i]}')
            
            else:
                # 二次微分解析の場合
                if mode=='2der':
                    z=self.z_second_derivative
                elif mode=='curX':
                    z=self.z_curvature
                
                # save
                if label != []:
                    data.append(label) # ラベル追加
                for i in range(len(z[0])):
                    data_lst = [f"{self.x[i]}"]
                    for j in range(len(z)):
                        data_lst.append(f"{z[j][i]}")
                    # data_lstを適切にフォーマットして文字列に変換
                    data.append("\t".join(data_lst))
            
            # output file全体
            output_lines= self.image[0].l[:data_index-2] + added_header + data

            with open(savefile_path, 'w', errors='replace', encoding='utf-8') as f:
                for line in output_lines:
                    # print(line)
                    f.write(line + '\n')

        # save
        if not os.path.isfile(savefile_path): # saveファイルが重複しない場合はsave
            save(savefile_path)
            print("Data was saved.")
        else: # saveファイルが存在する場合、上書きするか確認する
            overwrite = rpa.ask_me("Confirmation of save", "Do you want to overwrite existing file? (y/n)") # popup
            if overwrite == 'y': # yesを選択すればsave
                save(savefile_path)
                print("Data was saved.")
            else: # noを選択すれば保存しない
                print('Aborted.')    


# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(False, True) # 横はpixel数を固定
    app.mainloop()