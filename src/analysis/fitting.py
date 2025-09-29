import customtkinter
import os
import numpy as np
import platform
import matplotlib.pyplot as plt
import tkinter.messagebox as messagebox
import csv
import datetime
from PIL import Image, ImageTk
from pathlib import Path

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
from RyoPy.Frame import LoadDataFrame, SaveDataFrame
from setting.setting import App as SettingApp

# srcディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent

# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
fitting_setting_path = os.path.join(SRC_PATH, "setting", "fitting_setting.txt")
# ファイル選択するときの初期値
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
USER, has_USER = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")
VERSION, has_version = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")
# font
FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")

WINDOW_WIDTH, has_WINDOW_WIDTH = rpa.open_file_and_get_words_next_to_search_term(fitting_setting_path, "window_width")
WINDOW_height, has_WINDOW_height = rpa.open_file_and_get_words_next_to_search_term(fitting_setting_path, "window_height")
print(f"WINDOW_WIDTH: {WINDOW_WIDTH}, WINDOW_height: {WINDOW_height}")
KEY_Y2_LABEL, hoge=rpa.open_file_and_get_words_next_to_search_term(fitting_setting_path, "key_y2_label", type='str')
KEY_Y2, hoge=rpa.open_file_and_get_words_next_to_search_term(fitting_setting_path, "key_y2", type='str')

# 大枠
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # メンバー変数の設定
        self.fonts = (FONT_TYPE, 15)
        self.csv_filepath = None

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
            self.geometry(f"850x800") # 横x縦
        
        # title
        self.title("SpecTaroscoPy — Fitting")

        # 行方向のマスのレイアウトを設定する。リサイズしたときに一緒に拡大したい行をweight 1に設定。
        self.grid_rowconfigure(1, weight=1)
        # 列方向のマスのレイアウトを設定する
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)

        #アイコン
        # try:
        #     if platform.system() == "Darwin":  # macOS
        #         img_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'fitting.png')
        #         if os.path.exists(img_path):
        #             icon_image = PhotoImage(file=img_path)
        #             self.tk.call('wm', 'iconphoto', self._w, icon_image)
        #     elif platform.system() == "Windows":  # Windows
        #         ico_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'fitting.ico')
        #         if os.path.exists(ico_path):
        #             self.iconbitmap(ico_path)
        # except:
        #     pass
        
        columnspan=6
        # 1つ目のフレームの設定
        # stickyは拡大したときに広がる方向のこと。nsew で4方角で指定する。
        self.load_data_frame = LoadDataFrame(master=self, has_plot_data_frame=False)
        self.load_data_frame.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew", columnspan=columnspan)

        # 2つ目のフレーム設定
        # self.analyze_data_frame = AnalyzeDataFrame(master=self, spectrum=self.load_data_frame.spectrum) 
        self.analyze_data_frame = AnalyzeDataFrame(master=self, spectrum=self.load_data_frame.spectrum, app=self)
        self.analyze_data_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew", columnspan=columnspan)

        # 3つ目のフレーム設定
        self.save_data_frame = SaveDataFrame(master=self, analysis="fitting", spectrum=self.load_data_frame.spectrum)
        self.save_data_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nsew", columnspan=columnspan)

        # open manualボタン
        self.manual_button = customtkinter.CTkButton(master=self, text="Open Manual", font=self.fonts, command=self.open_manual_button_callback, width=120)
        self.manual_button.grid(row=100, column=0, padx=(20, 10), pady=(0,10), sticky="nw")

        # Settingボタン
        setting_button = customtkinter.CTkButton(
            self, command=self.open_setting, text="Setting", font=self.fonts, width=120)
        setting_button.grid(row=100, column=1, padx=(0, 10), pady=(0, 10), sticky="nw")

        for i in range(columnspan-2):
            customtkinter.CTkLabel(master=self, text=' ', font=self.fonts, width=120).grid(row=100, column=i+2, columnspan=1, padx=(0,10), pady=(0,10), sticky="nw")

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
        initial_tab = "Fitting"  # タブを初期表示
        app = SettingApp(initial_tab=initial_tab)
        app.resizable(True, True)
        app.mainloop()

class AnalyzeDataFrame(customtkinter.CTkScrollableFrame): # GUI中部
    """
    # fitting analysis (パラメータの設定とfittingの実行)
    # 関数を追加したいときは、
    # (1)
    # a. image_info 
    # b. self.fitting_params_label_lst...の条件分岐
    # c. self.fitting_func_combo
    # を更新してください。
    # (2)
    # Spectrum.pyの
    # a. def fit_spectrum_coreのfunc_dictと
    # b. def fit_spectrumのself.y_fitting, self.y_fitting_full
    # を更新してください。
    """
    def __init__(self, *args, header_name="Fitting", spectrum, app=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.spectrum = spectrum
        self.app = app

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        self.label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        self.label.grid(row=0, column=0, padx=10, sticky="w")
        # プルダウンメニューの作成 (Fitting funcの選択)
        x_set_param_label = customtkinter.CTkLabel(master=self, text='Function', font=self.fonts)
        x_set_param_label.grid(row=1, column=0, columnspan=1, padx=10, pady=(0,10), sticky="ew")
        self.fitting_func_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["Fermi-edge", 
                                                            "Polylogarithm", 
                                                            "Polylog + Gauss", 
                                                            "Single Gaussian", 
                                                            "Double Gaussian",
                                                            "Triple Gaussian"
                                                            ],
                                                    command=self.choice_fitting_func_combo_callback)
        self.fitting_func_combo.grid(row=1, column=1, padx=10, pady=(0,10), sticky="ew")
        self.has_chosed_fitting_func = True
        # paramsのラベルとテキストボックス
        
        # Range
        customtkinter.CTkLabel(master=self, text='X Range', font=self.fonts).grid(row=2, column=0, columnspan=1, padx=10, pady=(0,10), sticky="ew")
        # x_min
        customtkinter.CTkLabel(master=self, text='X Min').grid(row=3, column=0, padx=10, pady=(0,5), sticky="ew")
        self.x_min_entry = customtkinter.CTkEntry(master=self, placeholder_text="Min X", width=120, font=self.fonts)
        self.x_min_entry.grid(row=3, column=1, padx=10, pady=(0,5), sticky="ew")

        # x_max
        customtkinter.CTkLabel(master=self, text='X Max').grid(row=4, column=0, padx=10, pady=(0,5), sticky="ew")
        self.x_max_entry = customtkinter.CTkEntry(master=self, placeholder_text="Max X", width=120, font=self.fonts)
        self.x_max_entry.grid(row=4, column=1, padx=10, pady=(0,5), sticky="ew")

        customtkinter.CTkLabel(master=self, text='', font=self.fonts).grid(row=4, column=2, padx=10, pady=(0,5), sticky="ew")
        customtkinter.CTkLabel(master=self, text='', font=self.fonts, width=500).grid(row=4, column=3, columnspan=4, padx=10, pady=(0,5), sticky="ew")
    
        # --- CTkTabview を追加 ---
        self.coefficient_tabview = customtkinter.CTkTabview(master=self)
        self.coefficient_tabview.grid(row=5, column=0, columnspan=10, padx=(10,10), pady=(10,10), sticky="nw")
        self.coefficient_tabview.add("Coefficients")
        self.coefficient_tabview.add("EDCs Fitting")


        # --- Coefficients タブ ---
        self.coefficient_frame = self.coefficient_tabview.tab("Coefficients")
        self.coefficient_frame.configure(fg_color='gray20', corner_radius=10)

        customtkinter.CTkLabel(master=self.coefficient_frame, text='Symbol', width=80).grid(row=1, column=0, columnspan=1, padx=(10, 5), pady=(10,10), sticky="ew")
        customtkinter.CTkLabel(master=self.coefficient_frame, text='Initial Value', width=100).grid(row=1, column=1, columnspan=1, padx=(5,5), pady=(10,10), sticky="ew")
        customtkinter.CTkLabel(master=self.coefficient_frame, text='Fix', width=15).grid(row=1, column=2, padx=0, pady=(10,10), sticky="w")
        customtkinter.CTkLabel(master=self.coefficient_frame, text='Min', width=100).grid(row=1, column=3, columnspan=1, padx=5, pady=(10,10), sticky="ew")
        customtkinter.CTkLabel(master=self.coefficient_frame, text='Max', width=100).grid(row=1, column=5, columnspan=1, padx=5, pady=(10,10), sticky="ew")
        customtkinter.CTkLabel(master=self.coefficient_frame, text='Fit Result', width=100).grid(row=1, column=6, columnspan=1, padx=(5,10), pady=(10,10), sticky="we")

        columnspan=5
        # --- EDCs Fitting タブ ---
        self.fit_edcs_frame = self.coefficient_tabview.tab("EDCs Fitting")
        self.fit_edcs_frame.configure(fg_color='gray20', corner_radius=10)

        # import button
        customtkinter.CTkLabel(master=self.fit_edcs_frame, text='New Axis Info', width=120).grid(row=0, column=0, columnspan=1, padx=10, pady=(15,5), sticky="we")
        self.button_imort_x_axis_info_for_edcs_fit = customtkinter.CTkButton(self.fit_edcs_frame, command=self.import_x_axis_info_for_edcs_fit_callback, text="Import", font=self.fonts, width=120)
        self.button_imort_x_axis_info_for_edcs_fit.grid(row=0, column=1, columnspan=1, padx=(10,10), pady=(15,5), sticky="ew")
        # x label
        customtkinter.CTkLabel(master=self.fit_edcs_frame, text='New Axis Label', width=120).grid(row=1, column=0, columnspan=1, padx=10, pady=(0,5), sticky="we")
        self.entry_fit_edcs_x_label = customtkinter.CTkEntry(master=self.fit_edcs_frame, placeholder_text='Label Name', width=120, font=self.fonts)
        self.entry_fit_edcs_x_label.insert(0, 'Data Number')
        self.entry_fit_edcs_x_label.grid(row=1, column=1, padx=10, pady=(0,5), sticky="ew", columnspan=2)
        # x list
        customtkinter.CTkLabel(master=self.fit_edcs_frame, text='New Axis Values', width=120).grid(row=2, column=0, columnspan=1, padx=10, pady=(0,15), sticky="we")
        self.entry_fit_edcs_x_lst = customtkinter.CTkEntry(master=self.fit_edcs_frame, placeholder_text='Values Separated by Single Spaces', font=self.fonts, width=595)
        self.entry_fit_edcs_x_lst.grid(row=2, column=1, padx=10, pady=(0,15), sticky="ew", columnspan=columnspan, rowspan=1)

        # switch
        switch_value_edcs_fit = customtkinter.BooleanVar() # チェックボックスの変数を作成し、初期値をTrueに設定
        switch_value_edcs_fit.set(False)
        self.switch_edcs_fit = customtkinter.CTkSwitch(self.fit_edcs_frame, text=f"Fit EDCs", variable=switch_value_edcs_fit, width=120)
        self.switch_edcs_fit.grid(row=4, column=0,columnspan=1, padx=(15,10), pady=(0,5), sticky="ew")

        switch_value_edcs_fit_peaks = customtkinter.BooleanVar()
        switch_value_edcs_fit_peaks.set(False)
        self.swich_plot_edcs_peaks = customtkinter.CTkSwitch(self.fit_edcs_frame, text="Plot Peak X", variable=switch_value_edcs_fit_peaks, width=120)
        self.swich_plot_edcs_peaks.grid(row=5, column=0, columnspan=1, padx=(15,10), pady=(0,5), sticky="ew")

        switch_value_edcs_fit_x_axis_reverse = customtkinter.BooleanVar()
        switch_value_edcs_fit_x_axis_reverse.set(False)
        self.switch_edcs_fit_x_axis_reverse = customtkinter.CTkSwitch(self.fit_edcs_frame, text="Reverse X", variable=switch_value_edcs_fit_x_axis_reverse, width=120)
        self.switch_edcs_fit_x_axis_reverse.grid(row=6, column=0, columnspan=1, padx=(15,10), pady=(0,15), sticky="ew")

        # save button
        self.filename_fit_edcs = customtkinter.CTkEntry(master=self.fit_edcs_frame, placeholder_text='Output Filename', font=self.fonts)
        self.filename_fit_edcs.grid(row=10, column=0, padx=(10,10), pady=(0,15), sticky="ew", columnspan=2)
        self.button_save_fit_edcs = customtkinter.CTkButton(self.fit_edcs_frame, command=self.save_fit_edcs_button_callback, text="Save (EDCs Fit)", font=self.fonts)
        self.button_save_fit_edcs.grid(row=10, column=2, padx=(0,10), pady=(0,15), sticky="ew")

        for i in range(int(columnspan-2)):
            customtkinter.CTkLabel(master=self.fit_edcs_frame, text='', width=120).grid(row=0, column=2+i, columnspan=1, padx=10, pady=(15,5), sticky="we")

        # --- 初期設定 ----
        self.choice_fitting_func_combo_callback(self.fitting_func_combo.get())
        self.create_buttons()

    def import_x_axis_info_for_edcs_fit_callback(self):
        # X label
        self.entry_fit_edcs_x_label.delete(0, customtkinter.END)
        self.entry_fit_edcs_x_label.insert(0, rpa.open_file_and_get_words_next_to_search_term(self.spectrum.path, KEY_Y2_LABEL, type='str')[0])
        # X list
        self.entry_fit_edcs_x_lst.delete(0, customtkinter.END)
        self.entry_fit_edcs_x_lst.insert(0, rpa.open_file_and_get_words_next_to_search_term(self.spectrum.path, KEY_Y2, type='str')[0])

    def save_fit_edcs_button_callback(self):
        print('*** Save EDCs fitting results ***')
        foldername='SpectrumAnalyzer_Fitting'
        savefilename=self.filename_fit_edcs.get()
        rpa.create_folder_at_current_path(self.spectrum.path, foldername)
        self.savefile_path = self.spectrum.path.replace(self.spectrum.filename, os.path.join(foldername, savefilename))
        # print(self.savefile_path)
        # print(self.popt_lst)

        def save():
            with open(self.spectrum.path, encoding='utf-8', errors='replace') as f:
                l = [s.strip() for s in f.readlines()]
            data_index = l.index('DATA:') + 1

            # 追加するヘッダー
            added_header=[]
            added_header.append('')
            added_header.append('[Spectrum Analyzer: Fitting]')

            added_header.append('Author: R Nakazawa')
            added_header.append('Contact: https://www.researchgate.net/profile/Ryotaro-Nakazawa')
            added_header.append(f"Version: {VERSION}")
            added_header.append("--- Info ---")
            added_header.append(f"User\t{USER}")

            date = datetime.datetime.now()  # 現在時刻
            added_header.append(f"Date\t{date}")

            added_header.append(f"Load File Path\t{self.spectrum.path}")
            added_header.append(f"Save File Path\t{self.savefile_path}")
            # added_header.append([f"{self.x_legend}\t{' '.join(map(str, self.x))}"])
            # added_header.append([f"{self.y_legend}\t{' '.join(map(str, self.y))}"])
            # added_header.append([f"Comment\t{info_note}"])
                
                # fitting解析の時の処理
            added_header.append("--- Fitting initial parameters ---")
            added_header.append(f'EDCs fitting\t{self.switch_edcs_fit.get()}')
            added_header.append(f'New Axis Values\t{self.entry_fit_edcs_x_lst.get()}')
            added_header.append(f'New Axis Label\t{self.entry_fit_edcs_x_label.get()}')
            added_header.append(f"Function\t{self.fitting_func}")
            if self.fitting_func == "polylogarithm":
                added_header.append("Reference: D. Menzel, et al., ACS Appl. Mater. and Interfaces 13, 43540 (2021)")
            elif self.fitting_func == "lincom_of_polylog_and_gauss":
                added_header.append("Reference: D. Menzel, et al., ACS Appl. Mater. and Interfaces 13, 43540 (2021)")

            added_header.append(f"Initial Params for first Y data\t{' '.join(map(str, self.p0_edcs_fit))}")
            added_header.append(f"Fixed Paramrs\t{' '.join(map(str, self.spectrum.fixed_params_mask))}")
            added_header.append(f"Lower Limit\t{' '.join(map(str, self.spectrum.bound[0]))}")
            added_header.append(f"Upper Limit\t{' '.join(map(str, self.spectrum.bound[1]))}")
            added_header.append(f"X Min FitRegion\t{self.x_fitting_min}")
            added_header.append(f"X Max FitRegion\t{self.x_fitting_max}")

            added_header.append('') #空行
            added_header.append("DATA:")
            
            # データ行を作成
            data = []

            # パラメータ数に応じたラベル生成
            num_params = len(self.popt_lst_T)
            labels = [f"{self.fitting_params_label_lst[i]}_{savefilename.replace('.txt', '')}" for i in range(num_params)]

            # 先頭列に y_peak_lst 用のラベルを追加
            axis_label = f"ax_fit_{savefilename.replace('.txt', '')}_all"
            labels.insert(0, axis_label)

            # ヘッダー行追加
            data.append("\t".join(labels))

            # 各行のデータ（y_peak + 各パラメータ）を結合
            for row in zip(self.y_lst, *self.popt_lst_T):
                row_str = "\t".join([f"{val:.8e}" if isinstance(val, float) else str(val) for val in row])
                data.append(row_str)

            # 既存ヘッダーやデータと結合して出力
            output_lines = l[:data_index-2] + added_header + data
            with open(self.savefile_path, 'w', errors='replace', encoding='utf-8') as f:
                for line in output_lines:
                    f.write(line + '\n')

        if not os.path.isfile(self.savefile_path): # saveファイルが重複しない場合はsave
            save()
        else: # saveファイルが存在する場合、上書きするか確認する
            overwrite = rpa.ask_me("Confirmation of save", "Do you want to overwrite existing file? (y/n)") # popup
            if overwrite == 'y': # yesを選択すればsave
                save()
            else: # noを選択すれば保存しない
                print('Aborted.')


    def create_buttons(self):
        # Graph nowボタン生成
        self.graph_now_button = customtkinter.CTkButton(master=self, command=self.graph_now_button_callback, text="Graph Now", font=self.fonts)
        self.graph_now_button.grid(row=20, column=0, columnspan=1, padx=10, pady=(5,10), sticky="ew")

        # fittingボタン生成
        self.button_do_it = customtkinter.CTkButton(master=self, command=self.do_it_button_callback, text="Do It", font=self.fonts)
        self.button_do_it.grid(row=20, column=1, columnspan=1, padx=(0,10), pady=(5,10), sticky="ew")

        # close figures button
        self.button_close_figs = customtkinter.CTkButton(master=self, command=self.close_figs_button_callback, text="Close Figures", font=self.fonts)
        self.button_close_figs.grid(row=20, column=2, columnspan=1, padx=(0,10), pady=(5,10), sticky="ew")


    def display_image(self):  # fittingモデルの数式を表示する

        # ラベルがあれば削除
        if hasattr(self, "image_label"):
            self.image_label.destroy()
        if hasattr(self, "equation_label"):
            self.equation_label.destroy()

        # fitting_funcごとの設定
        image_info = {
            "Polylogarithm": {
                "path": "polylogarithm_function.png",
                "size": (280, 50),
                "text": r"Reference: D. Menzel et al., ACS Appl. Mater. Interfaces 13, 43540 (2021)",
            },
            "Polylog + Gauss": {
                "path": "linearcombination_of_polylogarithm_and_gaussian.png",
                "size": (440, 55),
                "text": r"Reference: D. Menzel et al., ACS Appl. Mater. Interfaces 13, 43540 (2021)",
            },
            "Fermi-edge": {
                "path": "Fermi_edge_function.png",
                "size": (360, 65),
                "text": "NOTE: Horizontal axis is kinetic energy.",
            },
            "Single Gaussian": {
                "path": "gaussian.png",
                "size": (270, 45),
                "text": "N = 1",
            },
            "Double Gaussian": {
                "path": "gaussian.png",
                "size": (270, 45),
                "text": "N = 2",
            },
            "Triple Gaussian": {
                "path": "gaussian.png",
                "size": (270, 45),
                "text": "N = 3",
            }
        }

        # 情報が定義されていない fitting_func の場合は処理を抜ける
        if self.fitting_func not in image_info:
            return

        info = image_info[self.fitting_func]
        print('src_path: ', SRC_PATH)
        image_path = os.path.join(SRC_PATH, "img", "fitting", info["path"])
        print(f"image_path: {image_path}")

        image = Image.open(image_path)
        image = image.resize(info["size"], Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        # 数式画像の表示
        self.image_label = customtkinter.CTkLabel(self, image=photo, text="")
        self.image_label.image = photo
        self.image_label.grid(row=1, column=2, columnspan=4, rowspan=2, padx=(0, 0), pady=(0, 0), sticky="ew")

        # コメント・参考文献ラベル
        self.equation_label = customtkinter.CTkLabel(master=self, text=info["text"], wraplength=450)
        self.equation_label.grid(row=3, column=2, columnspan=4, rowspan=2,
                                padx=(0, 0), pady=(0, 0), sticky="new")

    def get_input_values_in_widgets(self, frame):
        # AnaluzerDataFrame内のウィジットをすべて取得
        input_values = []
        strain_lst= []
        children = frame.winfo_children()

        # entryに入力した値を取得
        for child in children:
            if isinstance(child, customtkinter.CTkEntry):
                value = child.get()
                input_values.append(value)

        # checkboxの入力を取得
        checkbox_states = []
        for child in children:
            if isinstance(child, customtkinter.CTkCheckBox):
                state = child.get()
                checkbox_states.append(state)
        return input_values, checkbox_states

    def destroy_params(self, frame, upper_limit_row=7):
    # 配置されたウィジットの情報を取得
        children = frame.winfo_children()
    # 5行目以下にウィジットがあるかどうかをチェック
        for child in children:
            if child.grid_info()['row'] >= upper_limit_row:
                # 5行目以下にウィジットがある場合、削除する
                child.destroy()

    def choice_fitting_func_combo_callback(self, selected_value):
        # プルダウンメニューで選択された値を取得
        self.fitting_func = self.fitting_func_combo.get()  

        # polylogarithmのパラメータ
        if self.fitting_func == "Polylogarithm":
            # polylogarithmを選択した場合の処理
            print("polylogarithm functionを選択しました。")

            self.fitting_params_label_lst = ["Ev", "Et", "a0", "bg"] # label name
            self.fitting_params_text_lst = ["VBM energy", 
                                            "Inverse slope of tail states", 
                                            "Intensity",
                                            "Background (Constant)"] # 説明文
            self.fitting_params_initial_val_lst = [None, None, None, "0"] # 初期値
            self.fixs_params_initial_val_lst = [False, False, False, True] # 初期値で固定するか？

        # polylogarithmのパラメータ
        if self.fitting_func == "Polylog + Gauss":
            # Spectrum.pyで使用される変数名に書き換え

            # polylogarithmを選択した場合の処理
            print("polylogarithm functionとGaussianの線形結合を選択しました。")

            self.fitting_params_label_lst = ["Ev", "Et", "a0", "E0", "FWHM", "a1", "bg"] # label name
            self.fitting_params_text_lst = ["VBM energy of polylogarithm", 
                                            "Inverse slope of tail states of polylogarithm", 
                                            "Intensity of polylogarithm",
                                            "Energy at center of Gaussian",
                                            "FWHM of Gaussian",
                                            "Peak intensity of Gaussian",
                                            "Background (Constant)"
                                            ] # 説明文
            self.fitting_params_initial_val_lst = [None, None, None, None, None, None, "0"] # 初期値
            self.fixs_params_initial_val_lst = [False, False, False, False, False, False, True] # 初期値で固定するか？

        
        if self.fitting_func == "Fermi-edge":
            print("Fermi-edge functionを選択しました。")

            self.fitting_params_label_lst = ["T", "EF", "FWHM", "a0", "bg"] # label name
            self.fitting_params_text_lst = ["Temparature (K)", 
                                            "Fermi Level", 
                                            "FWHM of Instrumental Function", 
                                            "Intensity", 
                                            "Background (Constant)"] # 説明文
            self.fitting_params_initial_val_lst = [300, None, None, None, "0"] # 初期値
            self.fixs_params_initial_val_lst = [True, False, False, False, True] # 初期値で固定するか？

        # polylogarithmのパラメータ
        if self.fitting_func == "Single Gaussian":
            # Spectrum.pyで使用される変数名に書き換え

            # polylogarithmを選択した場合の処理
            print("Gaussianを選択しました。")

            self.fitting_params_label_lst = ["E1", "FWHM1", "a1", "bg"] # label name
            self.fitting_params_text_lst = ["Center Energy",
                                            "FWHM",
                                            "Peak Intensity",
                                            "Background (Constant)"
                                            ] # 説明文
            self.fitting_params_initial_val_lst = [None, None, None, "0"] # 初期値
            self.fixs_params_initial_val_lst = [False, False, False, True] # 初期値で固定するか？
    
        # polylogarithmのパラメータ
        if self.fitting_func == "Double Gaussian":
            # Spectrum.pyで使用される変数名に書き換え

            # polylogarithmを選択した場合の処理
            print("Gaussianを選択しました。")

            self.fitting_params_label_lst = ["E1", "FWHM1", "a1", "E2", "FWHM2", "a2", "bg"] # label name
            self.fitting_params_text_lst = ["Center X, 1",
                                            "FWHM, 1",
                                            "Peak Y, 1",
                                            "Center X, 2",
                                            "FWHM, 2",
                                            "Peak Y, 2",
                                            "Background (Constant)"
                                            ] # 説明文
            self.fitting_params_initial_val_lst = [None, None, None, None, None, None, "0"] # 初期値
            self.fixs_params_initial_val_lst = [False, False, False, False, False, False, True] # 初期値で固定するか？

        # polylogarithmのパラメータ
        if self.fitting_func == "Triple Gaussian":
            # Spectrum.pyで使用される変数名に書き換え

            # polylogarithmを選択した場合の処理
            print("Gaussianを選択しました。")

            self.fitting_params_label_lst = ["E1", "FWHM1", "a1", "E2", "FWHM2", "a2", "E3", "FWHM3", "a3", "bg"] # label name
            self.fitting_params_text_lst = ["Center X, 1",
                                            "FWHM, 1",
                                            "Peak Y, 1",
                                            "Center X, 2",
                                            "FWHM, 2",
                                            "Peak Y, 2",
                                            "Center X, 3",
                                            "FWHM, 3",
                                            "Peak Y, 3",
                                            "Background (Constant)"
                                            ] # 説明文
            self.fitting_params_initial_val_lst = [None, None, None, None, None, None, None, None, None, "0"] # 初期値
            self.fixs_params_initial_val_lst = [False, False, False, False, False, False, False, False, False, True] # 初期値で固定するか？
        
        self._create_coefficient_entries()

    def _create_coefficient_entries(self):
        # widgetsの初期化
        self.destroy_params(self.coefficient_frame, upper_limit_row=2)

        # EntryやCheckBoxを格納するリスト
        self.param_entry_list = []
        self.param_min_list = []
        self.param_max_list = []
        self.param_fix_check_list = []

        for i in range(len(self.fitting_params_label_lst)):
            symbol = self.fitting_params_label_lst[i]
            desc = self.fitting_params_text_lst[i]
            initial_val = self.fitting_params_initial_val_lst[i]
            is_fixed = self.fixs_params_initial_val_lst[i]

            # ラベル
            customtkinter.CTkLabel(master=self.coefficient_frame, text=symbol, width=80).grid(row=2+i, column=0, padx=(10, 5), pady=(0,5), sticky="ew")

            # Entry
            entry = customtkinter.CTkEntry(master=self.coefficient_frame, placeholder_text=desc, width=120, font=self.fonts)
            entry.grid(row=2+i, column=1, padx=5, pady=(0,5), sticky="ew")
            if initial_val is not None:
                entry.insert(0, initial_val)
            self.param_entry_list.append(entry) 

            # 固定
            T_var = customtkinter.BooleanVar(value=is_fixed)
            checkbox = customtkinter.CTkCheckBox(master=self.coefficient_frame, text="", variable=T_var, width=25)
            checkbox.grid(row=2+i, column=2, padx=(5,0), pady=(0, 5), sticky="ewsn")
            self.param_fix_check_list.append(checkbox)

            # 最小値
            minbox = customtkinter.CTkEntry(master=self.coefficient_frame, placeholder_text="", width=120, font=self.fonts)
            minbox.grid(row=2+i, column=3, padx=(5,0), pady=(0,5), sticky="ew")
            self.param_min_list.append(minbox)

            # ラベル
            limit_label = customtkinter.CTkLabel(master=self.coefficient_frame, text=f"<={symbol}<=", width=80)
            limit_label.grid(row=2+i, column=4, padx=0, pady=(0,5), sticky="ew")

            # 最大値
            maxbox = customtkinter.CTkEntry(master=self.coefficient_frame, placeholder_text="", width=120, font=self.fonts)
            maxbox.grid(row=2+i, column=5, padx=(0,10), pady=(0,5), sticky="ew")
            self.param_max_list.append(maxbox)

        # function form
        self.display_image()

        customtkinter.CTkLabel(master=self.coefficient_frame, text="", width=120, font=self.fonts).grid(row=3+i, column=4, padx=10, pady=(0,5), sticky="ew")
  
    def close_figs_button_callback(self):
        plt.close('all')
        print("All matplotlib figures closed.")

    def graph_now_button_callback(self):
        """
        Graph Nowボタンが押されたときの処理
        1. fittingボタン(Do it)を生成
        2. Graph Nowボタン上のテキストボックスで入力したcoefficientを使ってGraph化
        """

        p0=[]

        #インプットした値を抽出
        input_values, _ = self.get_input_values_in_widgets(self.coefficient_frame)
        # print(input_values)
        
        # 初期条件を抽出
        for i in range(len(self.fitting_params_label_lst)):
            p0.append(float(input_values[3*i]))
        print("Parameters:", p0)

        # energy rangeをテキストボックスから取得してインスタンス変数にする
        x_fitting_min = float(self.x_min_entry.get())
        x_fitting_max = float(self.x_max_entry.get())

        # coefficient (fittingの初期値) をテキストボックスから取得して、手動fittingを行う
        self.spectrum.fit_spectrum_manually(self.fitting_func, 
                                        x_fitting_min, 
                                        x_fitting_max,
                                        p0)

    def do_it_button_callback(self):
        if self.switch_edcs_fit.get():
            self.fit_edcs()
        else:
            self.fit_spectrum()
        
    def fit_spectrum(self):
        # resultsの初期化
        if hasattr(self, "results_value_labels"):
            for label in self.results_value_labels:
                label.destroy()
        self.results_value_labels = []
        # その他パラメータの初期化
        p0=[]
        bounds_max=[]
        bounds_min=[]
        fixed_params_mask=[]

        #全てのエントリーにインプットした値を抽出
        input_values, checkbox_states = self.get_input_values_in_widgets(self.coefficient_frame)
        print(input_values)

        # energy rangeをテキストボックスから取得してインスタンス変数にする
        try:
            self.x_fitting_min = float(self.x_min_entry.get())
            self.x_fitting_max = float(self.x_max_entry.get())
        except:
            messagebox.showwarning(f'ValueError!','Please enter Min X and Max X.')

        # 初期条件を抽出
        for i in range(len(self.fitting_params_label_lst)):
            p0.append(float(input_values[3*i]))

        # 束縛条件の前処理 (input_valuesの更新)
        for i in range(len(self.fitting_params_label_lst)):
            # チェックボックスにチェックが無ければ、束縛範囲を指定。
            # 束縛範囲のテキストボックスが未記入なら束縛なし(np.inf or -np.inf)。
                if input_values[3*i+1] == "": # 最小値
                    input_values[3*i+1] = -np.inf
                else:
                    input_values[3*i+1] = float(input_values[3*i+1])
                if input_values[3*i+2] == "": # 最大値
                    input_values[3*i+2] = np.inf
                else:
                    input_values[3*i+2] = float(input_values[3*i+2])

        # 束縛条件が決定
        for i in range(len(self.fitting_params_label_lst)):
            bounds_min.append(input_values[3*i+1])
            bounds_max.append(input_values[3*i+2])
        bounds= (bounds_min, bounds_max)

        # 束縛条件の前処理 (input_valuesの更新)
        for i in range(len(self.fitting_params_label_lst)):
            if checkbox_states[i]: 
                fixed_params_mask.append(True)
            else:
                fixed_params_mask.append(False)

        print("***Fitting analysis***")
        print("Initial parameters:", p0)
        print("Bound conditions:", bounds)
        print("Fixed parameters:", fixed_params_mask)
        # fittingを実行
        self.spectrum.fit_spectrum(self.x_fitting_min, self.x_fitting_max, self.fitting_func, p0, bounds, fixed_params_mask)

        # print(self.spectrum.popt)
        # resultsを表示
        for i in range(len(p0)):
            try:
                results_value_label = customtkinter.CTkLabel(master=self.coefficient_frame, text=str(rpa.decimalRound(self.spectrum.popt[i],sig=4)), width=120)
            except ValueError:
                results_value_label = customtkinter.CTkLabel(master=self.coefficient_frame, text=str(p0[-1]), width=120)
            results_value_label.grid(row=2+i, column=6, padx=(10,10), pady=(0,5), sticky="we")
            self.results_value_labels.append(results_value_label)

    def fit_edcs(self):

        # LoadDataFrameのインスタンスにアクセス（App経由）
        load_data_frame = self.app.load_data_frame
        combo = load_data_frame.y_legend_combo
        current_value = combo.get()
        values = combo._values

        self.y_fitting_full_lst=[] # X全域のfit spectrum
        self.y_fitting_lst=[] # fitting使用した定義域だけのfit spectrum
        self.popt_lst=[] # params
        self.x_peak_lst=[] # energy
        self.y_peak_lst=[] # y (e.g., k//, data number, and angle)
        j_lst=[]
        success_fit_flag=True

        try:
            current_index = values.index(current_value)
            print(current_index)
        except ValueError:
            print(f"現在の値 {current_value} は ComboBox に存在しません。")
            return

        # --- peak energyと対応するy dataの抽出 ---       
        # y2 data (EDCsで言うところのyを切り出したリスト) の取得
        # y_lst, _ =rpa.open_file_and_get_list_next_to_tab(self.spectrum.path, KEY_Y2)
        self.y_lst=np.fromstring(self.entry_fit_edcs_x_lst.get(), sep=" ") # entry boxから取得する。

        # EDC更新とfitting
        for i in range(current_index, len(values)):
            j=int(i - current_index) # countor
            # --- data loading ---
            if j != 0: # 2回目以降
                self._select_next_item_in_combobox(combo)  # YラベルComboBoxの今の値を取得して、次のlabelに更新する
            load_data_frame.load_button_callback(plot_spectrum=False) # Loadボタンを押す
            
            # --- fit data ---
            try:
                self.fit_spectrum()
                
                if j==0:
                    self.p0_edcs_fit=self.spectrum.p0
                    length_fit_spectrum_full=len(self.spectrum.y_fitting_full)
                    length_fit_spectrum=len(self.spectrum.y_fitting)
                    length_popt=len(self.spectrum.popt)

                # fitting結果をリストに収納
                self.y_fitting_full_lst.append(self.spectrum.y_fitting_full)
                self.y_fitting_lst.append(self.spectrum.y_fitting)
                self.popt_lst.append(np.array(self.spectrum.popt)) # parametersすべて
                # --- analyze_data_frameのinitial valueを更新する ---
                self._update_coefficient_entries()
            except:
                success_fit_flag=False
                self.y_fitting_full_lst.append(np.full(length_fit_spectrum_full, None, dtype=object))
                self.y_fitting_lst.append(np.full(length_fit_spectrum, None, dtype=object))
                self.popt_lst.append(np.full(length_popt, None, dtype=object))
                self.y_lst[j]=None
                j_lst.append(j)
                print(f'新しい軸のリストのうち{j}番目のfittingに失敗しました。{str(None)}に置きかわります。')

            
        # comboboxをもとに戻す
        combo.set(current_value)
        load_data_frame.load_button_callback(plot_spectrum=False)

        # --- peak energy plot ---
        if self.swich_plot_edcs_peaks.get():

            # popt配列にまとめて転置
            self.popt_lst_T = np.array(self.popt_lst).T

            # y軸データ数が一致しているかチェック
            is_y_valid = len(self.popt_lst) == len(self.y_lst)

            # plot
            if is_y_valid:
                new_ax_label=self.entry_fit_edcs_x_label.get()
            else:
                if self.entry_fit_edcs_x_lst.get()!='': 
                    print('エラー: New Axis Listの要素数とFitting解析したspectrum数が合いません。')
                new_ax_label='Data Number'
                self.y_lst=np.arange(len(self.popt_lst_T[0]))+1

            print(len(self.y_lst),len(self.popt_lst_T[0]))

            fig, ax = plt.subplots(1, 1, figsize=(4, 3))
            if self.fitting_func == 'Double Gaussian':
                ax.scatter(self.y_lst, self.popt_lst_T[0], label="Gaussian peaks", color="tab:blue", s=20)
                ax.scatter(self.y_lst, self.popt_lst_T[3], label="", color="tab:blue", s=20)
            elif self.fitting_func == 'Triple Gaussian':
                ax.scatter(self.y_lst, self.popt_lst_T[0], label="Gaussian peaks", color="tab:blue", s=20)
                ax.scatter(self.y_lst, self.popt_lst_T[3], color="tab:blue", s=20)
                ax.scatter(self.y_lst, self.popt_lst_T[6], color="tab:blue", s=20)
            elif self.fitting_func == 'Single Gaussian':
                ax.scatter(self.y_lst, self.popt_lst_T[0], label="Gaussian peaks", color="tab:blue", s=20)
            
            ax.set_ylabel("Energy (eV)")
            ax.set_xlabel(new_ax_label) # labelがあれば追加。

            ax.set_title(f'Peak Energy Plots\nFilename: {self.spectrum.filename}') 

            if self.switch_edcs_fit_x_axis_reverse.get():
                ax.invert_yaxis()
            plt.tight_layout()

        print('***EDCs Fitting Results***')
        if success_fit_flag==True:
            print('すべてのFittingが成功しました！')
        else:
            print(f'{j_lst}番目のFittingが失敗しました。')
        print(f'New Axis Value:\n{self.y_lst}')
        for i in range(len(self.popt_lst_T)):
            print(f'Params {i}: {self.fitting_params_text_lst[i]}\n{self.popt_lst_T[i]}')

        
        # --- entry boxの更新 ---
        self.filename_fit_edcs.delete(0, customtkinter.END)
        self.filename_fit_edcs.insert(0, f"fit_{self.spectrum.filename.replace('.txt', '_all.txt')}")

    def _select_next_item_in_combobox(self, combobox):
        current = combobox.get()
        options = combobox.cget("values")

        try:
            current_index = options.index(current)
            next_index = (current_index + 1) % len(options)
            combobox.set(options[next_index])
        except ValueError:
            print("現在の選択が options に含まれていません")

    def _update_coefficient_entries(self):
        # parameterの数だけ表示する
        for i, val in enumerate(self.spectrum.popt):
            if i < len(self.param_entry_list):
                self.param_entry_list[i].delete(0, "end")
                self.param_entry_list[i].insert(0, str(val))
            
            # 固定するかどうか
            if self.fixs_params_initial_val_lst[i]:
                T_var = customtkinter.BooleanVar(value=True)
            else:
                T_var = customtkinter.BooleanVar(value=False)
            self.fitting_param_checkbox = customtkinter.CTkCheckBox(master=self.coefficient_frame, text="", variable=T_var, width=30)

# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(True, True) # 横はpixel数を固定
    app.mainloop()