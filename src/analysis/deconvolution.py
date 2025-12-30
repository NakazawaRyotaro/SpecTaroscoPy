# Input dataをGaussian置換するのに取り組むも失敗。
import customtkinter
import numpy as np
import platform
import copy
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pathlib import Path
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
from RyoPy import defs_for_analysis as rpa
from RyoPy import defs_for_ctk as rpc
from RyoPy.PlotControl import PlotControl
from RyoPy.Spectrum import Spectrum
from RyoPy.Frame import LoadDataFrame, SaveDataFrame
from setting.setting import App as SettingApp

# srcのディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent
# print(CURRENT_PATH)
# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "deconvolution_setting.txt")

# ファイル選択するときの初期値
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
USER, has_USER = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type='str')
WINDOW_WIDTH, has_WINDOW_WIDTH = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "window_width_deconv")
WINDOW_height, has_WINDOW_height = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "window_height_deconv", type="str")
# font
FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")


# deconvoluted spectraを何本表示させるか listのindexではなくて、kの値(1から始まる)で指定する。
shown_deconvoluted_spectra_number = 60

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
            self.geometry("2050, 750")
        self.title("SpecTaroscoPy — Deconvolution. Please cite the following literature: R. Nakazawa et al., arXiv (2025). DOI: https://doi.org/10.48550/arXiv.2509.21246")

        #アイコン
        # try:
        #     if platform.system() == "Darwin":  # macOS
        #         img_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'deconv.png')
        #         if os.path.exists(img_path):
        #             icon_image = PhotoImage(file=img_path).subsample(2, 2)  # 2倍に縮小（調整可能）
        #             self.tk.call('wm', 'iconphoto', self._w, icon_image)
        #     elif platform.system() == "Windows":  # Windows
        #         ico_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'deconv.ico')
        #         if os.path.exists(ico_path):
        #             self.iconbitmap(ico_path)
        # except:
        #     pass

        columnspan=7
        # 1つ目のフレームの設定
        # stickyは拡大したときに広がる方向のこと。nsew で4方角で指定する。
        self.load_data_frame = LoadDataFrame(master=self, has_plot_data_frame=True)
        self.load_data_frame.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew", columnspan=columnspan)

        # 2つ目のフレーム設定
        self.preprocess_frame = PreprocessingFrame(master=self, spectrum=self.load_data_frame.spectrum) 
        self.preprocess_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew", columnspan=columnspan)

        # 3つ目のフレーム設定
        self.analyze_data_frame = AnalyzeDataFrame(master=self, spectrum=self.load_data_frame.spectrum,
                                                   update_callback=self.update_save_data_frame) # 対象オブジェクトは関数でもよい。
        self.analyze_data_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nsew", columnspan=columnspan)

        # 4つ目のフレーム設定
        self.save_data_frame = SaveDataFrame(master=self, analysis="deconvolution",
                                             spectrum=self.load_data_frame.spectrum,
                                             deconvoluted_spectrum=self.analyze_data_frame.deconvoluted_spectrum)
        self.save_data_frame.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nsew", columnspan=columnspan)

        # プロット用
        self.plot_data_frame = PlotDataFrame(master=self, spectrum=self.load_data_frame.spectrum)
        self.plot_data_frame.grid(row=0, column=columnspan, rowspan=4, padx=(0,10), pady=10, sticky="nsew", columnspan=columnspan)     


        # 行方向のマスのレイアウトを設定する。リサイズしたときに一緒に拡大したい行をweight 1に設定。
        self.grid_rowconfigure(2, weight=1)
        # 列方向のマスのレイアウトを設定する
        self.grid_columnconfigure(columnspan, weight=1) 


        # open manualボタン
        self.manual_button = customtkinter.CTkButton(master=self, text="Open Manual", font=self.fonts, command=self.open_manual_button_callback, width=120)
        self.manual_button.grid(row=100, column=0, padx=(20, 10), pady=(0,10), sticky="nw")

        # Settingボタン
        setting_button = customtkinter.CTkButton(
            self, command=self.open_setting, text="Setting", font=self.fonts)
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
        initial_tab = "Deconv"  # "Deconvolution" タブを初期表示
        app = SettingApp(initial_tab=initial_tab)
        app.resizable(True, True)
        app.mainloop()

    def update_save_data_frame(self, new_spectrum):
        self.save_data_frame.update_deconvoluted_spectrum(new_spectrum)

# plot data
class PlotDataFrame(customtkinter.CTkScrollableFrame): # GUI右部
    def __init__(self, spectrum, header_name="Plot spectra", **kwargs):
        super().__init__(**kwargs)
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.spectrum = spectrum
        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        label.grid(row=0, column=0, padx=10, sticky="nwns")             
        # label = customtkinter.CTkLabel(self, text=' ', font=(FONT_TYPE, 11), width=4000)
        # label.grid(row=0, column=2, columnspan=1, padx=10, sticky="nwns")   

    def plot_observed_spectrum(self, x, y):
        # plot機能をインポート
        self.pltctrl_observed_spectrum = PlotControl(initialize_figs=True)
        # plotを行う (この時点では表示されない)
        self.pltctrl_observed_spectrum.plot_spectrum(x, y, "Measured\nspectrum")
        # プロットをキャンバスに張り付ける
        label = customtkinter.CTkLabel(master=self, text="[Load Data]\nPATH: "+self.spectrum.path+"\nX: "+self.spectrum.x_legend+"\nY: "+self.spectrum.y_legend, font=self.fonts, wraplength=250)
        label.grid(row=1, column=0, padx=10, pady=(0,10), sticky="sew")
        self.pltctrl_observed_spectrum.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.pltctrl_observed_spectrum.fig, master=self)
        self.canvas.get_tk_widget().grid(row=2,column=0, padx=20, pady=10, sticky="new")

    def add_observed_spectrum_bg(self, x, y):
        # plotを行う (この時点では表示されない)
        self.pltctrl_observed_spectrum.add_spectrum(x, y, "Remove BG")
        # プロットをキャンバスに張り付ける
        self.pltctrl_observed_spectrum.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.pltctrl_observed_spectrum.fig, master=self)
        self.canvas.get_tk_widget().grid(row=2,column=0, padx=20, pady=10, sticky="new")     

    def plot_spread_function(self, x, y, function_type, path=None, x_legend=None, y_legend=None):
         # plot機能をインポート
        self.pltctrl_spread_function = PlotControl()
        # label = customtkinter.CTkLabel(master=self, text="------------------------------", font=self.fonts)
        # label.grid(row=3, column=0, padx=10, pady=(0,10), sticky="ewns")
        # gaussianのとき
        if function_type=="Gaussian":
            label = customtkinter.CTkLabel(master=self, text="[Instrumental Function]\nFunction: " + self.spectrum.s_function + "\nFWHM: "+str(self.spectrum.s_fwhm)+"eV", font=self.fonts)
            label.grid(row=1, column=1, padx=10, pady=(0,10), sticky="ewns")
            # plotを行う (この時点では表示されない)
            self.pltctrl_spread_function.plot_spectrum(x, y, "Instrumental\nfunction")
        # インポートするとき
        elif function_type=="Import":
            label = customtkinter.CTkLabel(master=self, text="[Instrumental Function]\nPATH: "+str(path)+"\nX: "+str(x_legend)+"\nY: "+str(y_legend), font=self.fonts, wraplength=250)
            label.grid(row=1, column=1, padx=10, pady=(0,10), sticky="ewns")
            # plotを行う (この時点では表示されない)
            self.pltctrl_spread_function.plot_spectrum(x, y, "Instrumental\nfunction")
        # プロットをキャンバスに張り付ける
        self.pltctrl_spread_function.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.pltctrl_spread_function.fig, master=self)
        self.canvas.get_tk_widget().grid(row=2,column=1, padx=20, pady=10, sticky="new")

    def plot_auto_cross_correlation(self, x, y):
        label = customtkinter.CTkLabel(master=self, text="------------------------------", font=self.fonts)
        label.grid(row=6, column=0, padx=10, pady=(0,10), sticky="ewns")
        label = customtkinter.CTkLabel(master=self, text="[Smoothing]", font=self.fonts)
        label.grid(row=7, column=0, padx=10, pady=(0,10), sticky="ews")
        # plot機能をインポート
        self.pltctrl_auto_correration = PlotControl(title='Auto correration')
        # plotを行う (この時点では表示されない)
        self.pltctrl_auto_correration.plot_spectrum(x, y, "Measured\nspectrum")
        self.pltctrl_auto_correration.add_spectrum(x, self.spectrum.i_ac, "Auto-correlation")
        # プロットをキャンバスに張り付ける
        self.pltctrl_auto_correration.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_auto_correration.fig, master=self)
        self.canvas.get_tk_widget().grid(row=8,column=0, padx=20, pady=10, sticky="new")    

        self.pltctrl_cross_correration = PlotControl(title='Cross correration')
        # plotを行う (この時点では表示されない)
        self.pltctrl_cross_correration.plot_spectrum(x, self.spectrum.s, "Instrumental\nfunction")
        self.pltctrl_cross_correration.add_spectrum(x, self.spectrum.s_cc, "Cross-correlation")
        # プロットをキャンバスに張り付ける
        self.pltctrl_cross_correration.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_cross_correration.fig, master=self)
        self.canvas.get_tk_widget().grid(row=8,column=1, padx=20, pady=10, sticky="new")    

    def plot_deconvoluted_spectra(self, x, y, iteration_number_lst):
        """
        x: スムージング前のxデータ
        y: スムージング前のyデータ
        iteration_number_lst: 表示するiterationのリスト"""
        label = customtkinter.CTkLabel(master=self, text="------------------------------", font=self.fonts)
        label.grid(row=10, column=0, padx=10, pady=(0,10), sticky="ewns")
        label = customtkinter.CTkLabel(master=self, text="[Deconvolution]\nMethod: " + self.spectrum.deconv_method, font=self.fonts)
        label.grid(row=11, column=0, padx=10, pady=(0,10), sticky="ews")
        
        # deconvolution spectra
        # fig作成 (この時点ではGUIに表示されない)
        self.pltctrl_deconvoluted_spectra = PlotControl("Deconvoluted spectra")
        # observed spectrum
        # self.pltctrl_deconvoluted_spectra.plot_spectrum(spectrum.x_bg, spectrum.y_bg, "Measured\nspectrum")
        # deconvoluted spectra
        self.pltctrl_deconvoluted_spectra.add_deconvoluted_spectra(self.spectrum.x_deconv, self.spectrum.o_deconv_lst, iteration_number_lst, colorbar=True)
        # プロットをキャンバスに張り付ける
        self.pltctrl_deconvoluted_spectra.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_deconvoluted_spectra.fig, master=self)
        self.canvas.get_tk_widget().grid(row=12,column=0, padx=20, pady=10, sticky="new") 

        # reconv
        self.pltctrl_reconvoluted_spectrum = PlotControl(title="Reconvoluted spectrum")
        self.pltctrl_reconvoluted_spectrum.plot_spectrum(x, y, "Measured\nspectrum")
        self.pltctrl_reconvoluted_spectrum.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_reconvoluted_spectrum.fig, master=self)
        self.canvas.get_tk_widget().grid(row=13,column=0, padx=20, pady=(0,10), sticky="new")

        # rmse
        self.pltctrl_rmse = PlotControl(title="RMSE")
        self.pltctrl_rmse.plot_rainbow_iteration_number(np.arange(0, self.spectrum.iteration_number-0.5, 1), self.spectrum.rmse_i_deconv)
        self.pltctrl_rmse.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_rmse.fig, master=self)
        self.canvas.get_tk_widget().grid(row=14,column=0, padx=20, pady=(0,10), sticky="new")  

        # d_rmse
        # self.pltctrl_d_rmse = PlotControl(title="ΔRMSE normarized by RMSE(k=1)", y_scale="log")
        # self.pltctrl_d_rmse.plot_rainbow_iteration_number(np.arange(1, self.spectrum.iteration_number+0.5, 1), self.spectrum.d_rmse_i_deconv/self.spectrum.rmse_i_deconv[0])
        # self.canvas = FigureCanvasTkAgg(self.pltctrl_d_rmse.fig, master=self)
        # self.canvas.get_tk_widget().grid(row=13,column=1, padx=20, pady=10, sticky="sew")

        # 特定のスペクトルを表示させるためのテキストボックス・ボタンを作る。
        self.shown_iteration_label = customtkinter.CTkLabel(master=self, text=f"Iteration Number:", font=self.fonts)
        self.shown_iteration_label.grid(row=15,column=0, padx=20, pady=(0,10), sticky="ewns")
        self.shown_iteration_entry = customtkinter.CTkEntry(master=self, placeholder_text='Iteration Number, k', width=120)
        
        self.shown_iteration_entry.grid(row=16,column=0, padx=20, pady=(10,0), sticky="ewns")
        self.shown_iteration_entry.insert(0, str(self.spectrum.iteration_number))
        self.shown_iteration_entry.bind("<Return>", self.iteration_number_entry_callback)
        
        # iteration slider
        self.iteration_slider = customtkinter.CTkSlider(master=self, from_=1, to=self.spectrum.iteration_number, command=self.iteration_number_slider_callback)
        self.iteration_slider.set(self.spectrum.iteration_number)
        self.iteration_slider.grid(row=17,column=0, padx=20, pady=(10,0), sticky="ewn")


        # label = customtkinter.CTkLabel(master=self, text="This button displays all figures.\nYou can save them.", font=self.fonts)
        # label.grid(row=14,column=1, padx=20, pady=10,rowspan=2, sticky="ews")
        
        show_fig_button = customtkinter.CTkButton(master=self, text="Show All Figures", command=self.show_all_figures_button_callback, font=self.fonts)
        show_fig_button.grid(row=18,column=0, padx=20, pady=(10,10), sticky="ewn") 

    def iteration_number_entry_callback(self, event=None):
        value = int(self.shown_iteration_entry.get())
        self.iteration_slider.set(value)
        self.iteration_number_slider_callback(value)

    def iteration_number_slider_callback(self, value):
        # sliderもこの関数を使用する
        # 初期化
        value= int(value)
        # entry更新
        self.shown_iteration_entry.delete(0, customtkinter.END)
        self.shown_iteration_entry.insert(0, value)

        rpc.destroy_widget_by_variable(self, self.shown_iteration_label)
        self.shown_iteration_label = customtkinter.CTkLabel(master=self, text=f"Iteration Number:", font=self.fonts)
        self.shown_iteration_label.grid(row=14,column=0, padx=20, pady=10, sticky="ewns")

        try:# プロットされているspectrum, pointがあれば削除
            self.pltctrl_rmse.remove_scatter_spectrum()
            # self.pltctrl_d_rmse.remove_scatter_spectrum()
            self.pltctrl_deconvoluted_spectra.remove_line_spectrum()

            # reconvoluted spectraは完全初期化
            if self.pltctrl_reconvoluted_spectrum.line!=[]:
                self.pltctrl_reconvoluted_spectrum.remove_line_spectrum(-1)
                self.pltctrl_reconvoluted_spectrum.remove_line_spectrum(-1)
        except AttributeError:
            pass

        print(str(value))  
        # deconvoluted spectrum
        self.pltctrl_deconvoluted_spectra.add_spectrum(self.spectrum.x_deconv, self.spectrum.o_deconv_lst[value-1], "Deconv,\nk="+str(value), color="black", scatter=False, linewidth=2)
        self.pltctrl_deconvoluted_spectra.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_deconvoluted_spectra.fig, master=self)
        self.canvas.get_tk_widget().grid(row=12,column=0, padx=20, pady=(10, 10), sticky="new") 

        # reconvoluted spectrum
        self.pltctrl_reconvoluted_spectrum.add_spectrum(self.spectrum.x_deconv, self.spectrum.d_i_and_reconv_lst[value-1], "Residual, k="+str(value), color=(0/255, 160/255, 233/255), scatter=False, linewidth=2)
        self.pltctrl_reconvoluted_spectrum.add_spectrum(self.spectrum.x_deconv, self.spectrum.i_reconv_lst[value-1], "Reconv, k="+str(value), color="black", scatter=False, linewidth=2)
        self.pltctrl_reconvoluted_spectrum.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_reconvoluted_spectrum.fig, master=self)
        self.canvas.get_tk_widget().grid(row=13,column=0, padx=20, pady=(0, 10), sticky="new") 

        # rmse
        self.pltctrl_rmse.add_spectrum(value, self.spectrum.rmse_i_deconv[int(value)-1], "RMSE, k="+str(value), color="black")
        self.pltctrl_rmse.fig.tight_layout() # layout調整
        self.canvas = FigureCanvasTkAgg(self.pltctrl_rmse.fig, master=self)
        self.canvas.get_tk_widget().grid(row=14,column=0, padx=20, pady=(0, 10), sticky="new")          

        # Δrmse
        # self.pltctrl_d_rmse.add_spectrum(value, self.spectrum.d_rmse_i_deconv[int(value)-1]/self.spectrum.rmse_i_deconv[0], "ΔRMSE, k="+str(int(value)), color="black")
        # self.canvas = FigureCanvasTkAgg(self.pltctrl_d_rmse.fig, master=self)
        # self.canvas.get_tk_widget().grid(row=13, column=1, padx=20, pady=10, sticky="new")

    def show_all_figures_button_callback(self):
        self.pltctrl_rmse.show_figures()        


# スペクトルの前処理
class PreprocessingFrame(customtkinter.CTkFrame): # GUI中部
    def __init__(self, *args, header_name="Preprocess", spectrum, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.spectrum = spectrum
        global flag_bg
        flag_bg=False

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        label.grid(row=0, column=0, columnspan=1, padx=10, sticky="w")

        # プルダウンメニューの作成 (methodの選択)
        background_label = customtkinter.CTkLabel(master=self, text='Method')
        background_label.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        self.background_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["None","Constant BG", "Constant BG + Gaussian"],
                                                    command=self.choice_background_combo_callback)
        self.background_combo.grid(row=1, column=1, padx=(0,10), pady=(0,10), sticky="ew")

        # Do itボタン生成
        bg_do_it_button = customtkinter.CTkButton(master=self, command=self.bg_do_it_button_callback, text="Do it", font=self.fonts)
        bg_do_it_button.grid(row=10, column=1, padx=(0,10), pady=(10, 10), sticky="ew")
        # Resetボタン生成
        bg_do_it_button = customtkinter.CTkButton(master=self, command=self.reset_button_callback, text="Reset", font=self.fonts)
        bg_do_it_button.grid(row=10, column=0, padx=10, pady=(10, 10), sticky="ew")

    def get_input_values_in_widgets(self):
        # AnaluzerDataFrame内のウィジットをすべて取得
        input_values = []
        strain_lst= []
        children = self.winfo_children()

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

    def destroy_params(self, row_number):
    # 配置されたウィジットの情報を取得
        children = self.winfo_children()
    # 2行目以下にウィジットがあるかどうかをチェック
        for child in children:
            if child.grid_info()['row'] >= row_number:
                # 5行目以下にウィジットがある場合、削除する
                child.destroy()

    def choice_background_combo_callback(self, selected_value):
        # widgetsの初期化
        self.destroy_params(2)

        # プルダウンメニューで選択された値(bg処理の方法)を取得し、GUIを作成
        if self.background_combo.get() == "Constant BG":
            print("一定のバックグラウンドを仮定し、spectrumから除算します。")
            
            # BG Region
            x_bg_min_label = customtkinter.CTkLabel(master=self, text='BG Region:')
            x_bg_min_label.grid(row=2, column=0, padx=(0,10), pady=(0,5), sticky="ew")
            self.x_bg_min_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Min X", font=self.fonts)
            self.x_bg_min_textbox.grid(row=2, column=1, padx=(0,10), pady=(0,5), sticky="ew")
            # x_max
            self.x_bg_max_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Max X", font=self.fonts)
            self.x_bg_max_textbox.grid(row=2, column=2, padx=(0,10), pady=(0,5), sticky="ew")

        # プルダウンメニューで選択された値(bg処理の方法)を取得し、GUIを作成
        if self.background_combo.get() == "Constant BG + Gaussian":
            print("一定のバックグラウンドを仮定し、spectrumから除算します。さらに片方のスペクトル端をGaussianでfittingしてもとのスペクトルに接続。")
            
            # BG Region
            x_bg_min_label = customtkinter.CTkLabel(master=self, text='BG Region:')
            x_bg_min_label.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")
            self.x_bg_min_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Min X", font=self.fonts)
            self.x_bg_min_textbox.grid(row=2, column=1, padx=(0,10), pady=(0,5), sticky="ew")
            self.x_bg_max_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Max X", font=self.fonts)
            self.x_bg_max_textbox.grid(row=2, column=2, padx=(0,10), pady=(0,5), sticky="ew")

            # Fitting Region
            x_gauss_min_label = customtkinter.CTkLabel(master=self, text='Fitting Region:')
            x_gauss_min_label.grid(row=4, column=0, padx=10, pady=(0,5), sticky="ew")
            self.x_gauss_min_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Min X", font=self.fonts)
            self.x_gauss_min_textbox.grid(row=4, column=1, padx=(0,10), pady=(0,5), sticky="ew")
            self.x_gauss_max_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Max X", font=self.fonts)
            self.x_gauss_max_textbox.grid(row=4, column=2, padx=(0,10), pady=(0,5), sticky="ew")

            # checkbox (片方だけ選べるラジオボタン)
            # チェック状態を管理する共通の変数を定義（文字列型）
            self.fit_x_side_var = customtkinter.StringVar(value="high")  # 初期値は "high"
            # ラベルなどはそのまま
            x_gauss_min_label = customtkinter.CTkLabel(master=self, text='Fitting Region:')
            x_gauss_min_label.grid(row=4, column=0, padx=(0,10), pady=(0,5), sticky="ew")

            self.x_gauss_min_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Min X", font=self.fonts)
            self.x_gauss_min_textbox.grid(row=4, column=1, padx=(0,10), pady=(0,5), sticky="ew")
            self.x_gauss_max_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Max X", font=self.fonts)
            self.x_gauss_max_textbox.grid(row=4, column=2, padx=(0,10), pady=(0,5), sticky="ew")
            # ラジオボタンで一方だけ選べるようにする
            self.fit_x_low_radio = customtkinter.CTkRadioButton(master=self, text="Low X Side", variable=self.fit_x_side_var, value="low")
            self.fit_x_low_radio.grid(row=4, column=3, padx=(0, 10), pady=(0, 5), sticky="w")
            self.fit_x_high_radio = customtkinter.CTkRadioButton(master=self, text="High X Side", variable=self.fit_x_side_var, value="high")
            self.fit_x_high_radio.grid(row=4, column=4, padx=(0, 10), pady=(0, 5), sticky="w")

            # fitting params
            label_params = customtkinter.CTkLabel(self, text="Fitting Params:")
            label_params.grid(row=6, column=0, padx=10, pady=(0,5), sticky="ew")      
            self.fit_gauss_a_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Peak Intensity", font=self.fonts)
            self.fit_gauss_a_textbox.grid(row=6, column=1, padx=(0,10), pady=(0,5), sticky="ew")
            self.fit_gauss_x0_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Center X", font=self.fonts)
            self.fit_gauss_x0_textbox.grid(row=6, column=2, padx=(0,10), pady=(0,5), sticky="ew")
            self.fit_gauss_fwhm_textbox = customtkinter.CTkEntry(master=self, placeholder_text="FWHM (=2.35 sigma)", font=self.fonts)
            self.fit_gauss_fwhm_textbox.grid(row=6, column=3, padx=(0,10), pady=(0,5), sticky="ew")     

            # グラフナウボタン生成
            graph_now_button = customtkinter.CTkButton(master=self, command=self.graph_now_button_callback, text="Graph Now", font=self.fonts)
            graph_now_button.grid(row=10, column=2, padx=(0,10), pady=(5, 10), sticky="ew")

        # Do itボタン生成
        bg_do_it_button = customtkinter.CTkButton(master=self, command=self.bg_do_it_button_callback, text="Do it", font=self.fonts)
        bg_do_it_button.grid(row=10, column=1, padx=(0,10), pady=(5, 10), sticky="ew")
        # Resetボタン生成
        bg_do_it_button = customtkinter.CTkButton(master=self, command=self.reset_button_callback, text="Cancel", font=self.fonts)
        bg_do_it_button.grid(row=10, column=0, padx=10, pady=(5, 10), sticky="ew")

    def bg_do_it_button_callback(self):
        # flagを設けている理由を忘れた
        global flag_bg
        flag_bg=True

        if self.background_combo.get() == "Constant BG":
            x_bg_min = float(self.x_bg_min_textbox.get())
            x_bg_max = float(self.x_bg_max_textbox.get())
            self.spectrum.subtract_constant_background(x_bg_min=x_bg_min, x_bg_max=x_bg_max)
            # plotを行う指令をAppに出す。plot_data_frameが呼び出される。
            self.master.plot_data_frame.add_observed_spectrum_bg(self.spectrum.x_bg, self.spectrum.y_bg)

        elif self.background_combo.get() == "None":
            self.reset_button_callback() # background処理しない

        elif self.background_combo.get() == "Constant BG + Gaussian":
            x_bg_min = float(self.x_bg_min_textbox.get())
            x_bg_max = float(self.x_bg_max_textbox.get())
            x_fit_min= float(self.x_gauss_min_textbox.get())
            x_fit_max= float(self.x_gauss_max_textbox.get())

            # background強度を計算する
            p0_gauss=[
                float(self.fit_gauss_x0_textbox.get()),
                float(self.fit_gauss_fwhm_textbox.get()),
                float(self.fit_gauss_a_textbox.get()),
                0 # ダミー (後で置換されるため)
                ]
            print(self.fit_x_side_var.get())
            self.spectrum.subtract_const_gauss_background(
                                            x_bg_min=x_bg_min, x_bg_max=x_bg_max, 
                                            x_fit_min=x_fit_min, x_fit_max=x_fit_max,
                                            p0=p0_gauss, 
                                            bounds=None,
                                            fixed_params_mask=[False, False, False, True],
                                            gauss_x_side=self.fit_x_side_var.get()
                                            )

            # plotを行う指令をAppに出す。plot_data_frameが呼び出される。
            # すでにbackground処理していた場合、削除
            if self.master.plot_data_frame.pltctrl_observed_spectrum.line!=[]:
                self.master.plot_data_frame.pltctrl_observed_spectrum.remove_line_spectrum()
                self.master.plot_data_frame.pltctrl_observed_spectrum.remove_scatter_spectrum()
            self.master.plot_data_frame.pltctrl_observed_spectrum.add_spectrum(self.spectrum.x, self.spectrum.y_fitting_full, 
                                                                           label='Fitting', color='black', 
                                                                           linewidth=1, linestyle='-', scatter=False, zorder=0)
            self.master.plot_data_frame.pltctrl_observed_spectrum.add_spectrum(self.spectrum.x_bg, self.spectrum.y_bg, label='Removed BG', s=5)
            self.master.plot_data_frame.pltctrl_observed_spectrum.ax.autoscale()

    def graph_now_button_callback(self):
        if self.background_combo.get() == "Constant BG + Gaussian":
            x_fit_min= float(self.x_gauss_min_textbox.get())
            x_fit_max= float(self.x_gauss_max_textbox.get())

            x_bg_min = float(self.x_bg_min_textbox.get())
            x_bg_max = float(self.x_bg_max_textbox.get())

            x_bg_min = x_bg_min
            x_bg_max = x_bg_max
            BG = np.average(self.spectrum.y[rpa.get_idx_of_the_nearest(self.spectrum.x,x_bg_min):
                                        rpa.get_idx_of_the_nearest(self.spectrum.x,x_bg_max)])

            # background強度を計算する
            p0_gauss=[
                float(self.fit_gauss_x0_textbox.get()),
                float(self.fit_gauss_fwhm_textbox.get()),
                float(self.fit_gauss_a_textbox.get()),
                BG
                ]
            
            # fitting
            self.spectrum.fit_spectrum_manually('Single Gaussian', x_fit_min, x_fit_max, p0=p0_gauss)

    def reset_button_callback(self):
        self.spectrum.x_bg_max=None
        self.spectrum.x_bg_min=None
        self.spectrum.y_bg=[]
        self.spectrum.x_bg=[]
        flag_bg=False
        self.spectrum.bg_method='None'
        self.master.plot_data_frame.pltctrl_observed_spectrum.remove_scatter_spectrum(-1)
        self.master.plot_data_frame.pltctrl_observed_spectrum.remove_line_spectrum()
        self.master.plot_data_frame.pltctrl_observed_spectrum.ax.autoscale()
        self.master.plot_data_frame.pltctrl_observed_spectrum.ax.legend(loc='best')
        self.master.plot_data_frame.pltctrl_observed_spectrum.fig.tight_layout()
        
# deconvolution analysis (パラメータの設定とfittingの実行)
class AnalyzeDataFrame(customtkinter.CTkFrame): # GUI中部
# class AnalyzeDataFrame(customtkinter.CTkScrollableFrame): # GUI中部
    def __init__(self, spectrum, header_name="Deconvolution", update_callback=None, **kwargs):
        super().__init__(**kwargs)
        
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name
        self.spectrum = spectrum
        self.s_spectrum = None
        self.update_callback = update_callback  # コールバック関数を保持する
        self.deconvoluted_spectrum = None
        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        label.grid(row=0, column=0, columnspan=1, padx=10, sticky="w")

        # プルダウンメニューの作成 (装置関数の選択)
        spread_label = customtkinter.CTkLabel(master=self, text='Instrumental Function:', )
        spread_label.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        self.spread_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["Gaussian", "Import"],
                                                    command=self.choice_spread_function_combo_callback)
        self.spread_combo.grid(row=1, column=1, padx=(0,10), pady=(0,10), sticky="ew")

        fwhm_s_label = customtkinter.CTkLabel(master=self, text='Params:') #, justify="center")
        fwhm_s_label.grid(row=1, column=2, columnspan=1, padx=10, pady=(0,10), sticky="ew")
        self.fwhm_s_textbox = customtkinter.CTkEntry(master=self, placeholder_text="FWHM", font=self.fonts)
        self.fwhm_s_textbox.grid(row=1, column=3, padx=(0,10), pady=(0,10), sticky="ew")

        # プルダウンメニューの作成 (prefilteringの選択)
        smoothing_label = customtkinter.CTkLabel(master=self, text='Smoothing:', )
        smoothing_label.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
        self.smoothing_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["Auto-/Cross-correlation", "None"],
                                                    command=self.choice_smoothing_combo_callback)
        self.smoothing_combo.grid(row=2, column=1, padx=(0,10), pady=(0,10), sticky="ew")

        # プルダウンメニューの作成 (deconv methodの選択)
        deconv_method_label = customtkinter.CTkLabel(master=self, text='Deconvoluiton:')
        deconv_method_label.grid(row=3, column=0, columnspan=1, padx=10, pady=(0,5), sticky="ew")
        self.deconv_method_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                                    values=["Jansson's method", "Gold's ratio method"],
                                                    command=self.choice_deconv_method_combo_callback)
        self.deconv_method_combo.grid(row=3, column=1, padx=(0,10), pady=(0,5), sticky="ew")

        deconv_iteration_label = customtkinter.CTkLabel(master=self, text='Iteration Number:') #, justify="center")
        deconv_iteration_label.grid(row=4, column=0, columnspan=1, padx=10, pady=(0,10), sticky="ew")
        self.deconv_iteration_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Positive Integer, k", font=self.fonts)
        self.deconv_iteration_textbox.grid(row=4, column=1, padx=(0,10), pady=(0,10), sticky="ew")

        # Range
        # x_min
        x_rmse_min_label = customtkinter.CTkLabel(master=self, text='RMSE Region:')
        x_rmse_min_label.grid(row=6, column=0, padx=10, pady=(0,5), sticky="ew")
        self.x_rmse_min_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Min X", font=self.fonts)
        self.x_rmse_min_textbox.grid(row=6, column=1, padx=(0,10), pady=(0,5), sticky="ew")
        # チェックボックスの変数を作成し、初期値をTrueに設定
        checkbox_value_min = customtkinter.BooleanVar()
        checkbox_value_min.set(True)
        self.x_rmse_min_checkbox = customtkinter.CTkCheckBox(master=self, text="Edge (Min X)?", variable=checkbox_value_min)
        self.x_rmse_min_checkbox.grid(row=6, column=3, padx=(0,10), pady=(0, 5), sticky="w")

        # Max
        self.x_rmse_max_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Max X", font=self.fonts)
        self.x_rmse_max_textbox.grid(row=6, column=2, padx=(0,10), pady=(0,5), sticky="ew")
        # チェックボックスの変数を作成し、初期値をTrueに設定
        checkbox_value_max = customtkinter.BooleanVar()
        checkbox_value_max.set(True)
        self.x_rmse_max_checkbox = customtkinter.CTkCheckBox(master=self, text="Edge (Max X)?", variable=checkbox_value_max)
        self.x_rmse_max_checkbox.grid(row=6, column=4, padx=(0,10), pady=(0, 5), sticky="w")

        # Deconv ボタン生成
        deconvolute_button = customtkinter.CTkButton(master=self, command=self.deconvolute_button_callback, text="Deconvolute", font=self.fonts)
        deconvolute_button.grid(row=9, column=0, padx=(10,10), pady=(5,10), sticky="ew")
        # ピーク検出 ボタン生成
        detect_peak_button = customtkinter.CTkButton(master=self, command=self.detect_peak_button_callback, text="Detect peaks", font=self.fonts)
        detect_peak_button.grid(row=9, column=1, padx=(0,10), pady=(5,10), sticky="ew")

        # close figures button
        self.button_close_figs = customtkinter.CTkButton(master=self, command=self.close_figs_button_callback, text="Close figures", font=self.fonts)
        self.button_close_figs.grid(row=9, column=2, columnspan=1, padx=(0,10), pady=(5,10), sticky="ew")

        self.choice_deconv_method_combo_callback(hoge=None)

    def close_figs_button_callback(self):
        import matplotlib.pyplot as plt
        plt.close('all')
        print("All matplotlib figures closed.")


    def get_input_values_in_widgets_at_a_row(self):
        # AnaluzerDataFrame内のウィジットをすべて取得
        input_values = []
        strain_lst= []
        children = self.winfo_children()
        # for child in children:
        #     print(child)

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

    def destroy_widgets(self, fix_row, column_low):
    # 配置されたウィジットの情報を取得
        children = self.winfo_children()
    # fix_rowにウィジットがあるかどうかをチェック
        for child in children:
            if child.grid_info()['row'] == fix_row:
                if child.grid_info()['column'] >= column_low:
                    # column_low以上にウィジットがある場合、削除する
                    child.destroy()

    def choice_spread_function_combo_callback(self, hoge):
        self.destroy_widgets(1, 2)
        if self.spread_combo.get()=="Gaussian": 
            fwhm_s_label = customtkinter.CTkLabel(master=self, text='params:') #, justify="center")
            fwhm_s_label.grid(row=1, column=2, columnspan=1, padx=5, pady=(0,10), sticky="ew")
            self.fwhm_s_textbox = customtkinter.CTkEntry(master=self, placeholder_text="FWHM", width=120, font=self.fonts)
            self.fwhm_s_textbox.grid(row=1, column=3, padx=5, pady=(0,10), sticky="ew")

        if self.spread_combo.get()=="Import":
            # loadボタン
            load_s_button = customtkinter.CTkButton(master=self, command=self.open_file_s_button_callback, text="Open File", font=self.fonts)
            load_s_button.grid(row=1, column=2, padx=5, pady=(0,10), sticky="ew")           
            
            self.x_s_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts, values=["---X Label---"])
            self.x_s_legend_combo.grid(row=1, column=3, padx=5, pady=(0,10), sticky="w")
            
            self.y_s_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts, values=["---Y Label---"])
            self.y_s_legend_combo.grid(row=1, column=4, padx=5, pady=(0,10), sticky="w")

            # 開くボタン 生成
            load_s_button = customtkinter.CTkButton(master=self, command=self.load_s_button_callback, text="Load", font=self.fonts)
            load_s_button.grid(row=1, column=5, padx=(5,10), pady=(0,10), sticky="ew")

    def open_file_s_button_callback(self):
        """
        開くボタンが押されたときのコールバック。
        """
        # FitSpectrumのインスタンスを作成
        # grobal変数にするのがカギ [他のclass(flame) でもspectrumインスタンスを使用でき、
        # インスタンス spectrum (= spectrum) の関数 (method) やインスタンス変数を spectrum.xxx で呼び出せる] 
        self.s_spectrum = Spectrum()
        # s_spectrum.open_csv_file(idir=IDIR)
        self.s_spectrum.read_labels_from_file_auto(idir=IDIR)
    
        # combo更新
        self.x_s_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                            values=self.s_spectrum.label_list)
        self.x_s_legend_combo.grid(row=1, column=3, padx=5, pady=(0,10), sticky="w")

        self.y_s_legend_combo = customtkinter.CTkComboBox(master=self, font=self.fonts,
                                            values=self.s_spectrum.label_list)
        self.y_s_legend_combo.grid(row=1, column=4, padx=5, pady=(0,10), sticky="w")  

    def load_s_button_callback(self):
        # spectrum dataの読み込み
        print(self.x_s_legend_combo.get(), self.y_s_legend_combo.get())
        self.s_spectrum.load_xy_data_from_file_auto(self.x_s_legend_combo.get(), self.y_s_legend_combo.get(), plot_spectrum=False)
        
        # plot_data_frameを初期化
        # self.destroy_widgets(self.master.plot_data_frame, 3)
        # 読み込んだスペクトルを表示
        self.master.plot_data_frame.plot_spread_function(self.s_spectrum.x, self.s_spectrum.y, self.spread_combo.get(),
                                                         self.s_spectrum.path, self.x_s_legend_combo.get(), self.y_s_legend_combo.get())


    def choice_smoothing_combo_callback(self, hoge):
        self.destroy_widgets(2, 2)
        if self.smoothing_combo.get()=="Savitzky-Goley":
            label_params = customtkinter.CTkLabel(self, text="params:")
            label_params.grid(row=2, column=2, padx=10, pady=(0,10), sticky="ew")
            self.sg_iteration_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Iteration number", font=self.fonts)
            self.sg_iteration_textbox.grid(row=2, column=3, padx=10, pady=(0,10), sticky="ew")
            self.sg_iteration_textbox.insert(0, 4)        
            self.sg_poly_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Degree of polynomial",  font=self.fonts)
            self.sg_poly_textbox.grid(row=2, column=4, padx=10, pady=(0,10), sticky="ew")
            self.sg_poly_textbox.insert(0, 2) 
            self.sg_point_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Point number", font=self.fonts)
            self.sg_point_textbox.grid(row=2, column=5, padx=(10,10), pady=(0,10), sticky="ew")

    def choice_deconv_method_combo_callback(self, hoge):
        self.destroy_widgets(3, 2)
        if self.deconv_method_combo.get()=="Jansson's method":
            self.deconv_method = "Jansson"
            label_params = customtkinter.CTkLabel(self, text="Params:")
            label_params.grid(row=3, column=2, padx=10, pady=(0,5), sticky="ew")      
            self.jansson_a_textbox = customtkinter.CTkEntry(master=self, placeholder_text="a", font=self.fonts)
            self.jansson_a_textbox.grid(row=3, column=3, padx=(0,10), pady=(0,5), sticky="ew")
            self.jansson_a_textbox.insert(0, 0)
            self.jansson_b_textbox = customtkinter.CTkEntry(master=self, placeholder_text="x: b=x*i",font=self.fonts)
            self.jansson_b_textbox.insert(0, 10)
            self.jansson_b_textbox.grid(row=3, column=4, padx=(0,10), pady=(0,5), sticky="ew")
            self.jansson_r0_textbox = customtkinter.CTkEntry(master=self, placeholder_text="y: r_0=y*b",font=self.fonts)
            self.jansson_r0_textbox.grid(row=3, column=5, padx=(0,10), pady=(0,5), sticky="ew")     
            self.jansson_r0_textbox.insert(0, 0.8)
        if self.deconv_method_combo.get()=="Gold's ratio method":
            self.deconv_method = "Gold"

        self.display_image()

    def display_image(self): # deconvolutionの数式を表示する
        # 画像ファイルのパスを選択された値に応じて決定する
        # 実行された.pyファイルのディレクトリパスを取得
        current_dir = os.path.dirname(__file__) #現在の実行ファイルのpath
        
        # 画像を表示するためのラベルを作成し、既存のラベルがあれば削除する 
        if hasattr(self, "image_label"):
            self.image_label.destroy()
        if hasattr(self, "equation_label"):
            self.equation_label.destroy() # 初期化

        if self.deconv_method_combo.get() == "Jansson's method":
            path=os.path.join(SRC_PATH, "img", "deconvolution", "Janssons_method.png")
            image = Image.open(path)

            image = image.resize((340, 90), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            # 表示
            self.image_label = customtkinter.CTkLabel(self, image=photo, text="")
            self.image_label.image = photo
            self.image_label.grid(row=11, column=0, columnspan=3, rowspan=10, padx=(10,0), pady=(0,10), sticky="ewns")
            # reference
            self.equation_label = customtkinter.CTkLabel(master=self, text=r"Reference: P. A. Jansson, Deconvolution of Images and Spectra (Courier Corporation, 2014).", wraplength=230)
            self.equation_label.grid(row=11, column=3, columnspan=2, rowspan=10, padx=(0,0), pady=(0, 10), sticky="ewns")
        elif self.deconv_method_combo.get() == "Gold's ratio method":
            path=os.path.join(SRC_PATH, "img", "deconvolution", "Golds_ratio_method.png")
            image = Image.open(path)
            image = image.resize((340, 50), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            # 表示
            self.image_label = customtkinter.CTkLabel(self, image=photo, text="")
            self.image_label.image = photo
            self.image_label.grid(row=11, column=0, columnspan=3, rowspan=10, padx=(10,0), pady=(0,10), sticky="ewns")
            # reference
            self.equation_label = customtkinter.CTkLabel(master=self, text=r"Reference: P. A. Jansson, Deconvolution of Images and Spectra (Courier Corporation, 2014).", wraplength=230)
            self.equation_label.grid(row=11, column=3, columnspan=2, rowspan=10, padx=(0,0), pady=(0, 10), sticky="ewns")
 
    def update_deconvoluted_spectrum(self, new_deconvoluted_spectrum):
        self.deconvoluted_spectrum = new_deconvoluted_spectrum
        if self.update_callback:
            self.update_callback(new_deconvoluted_spectrum)  # コールバックを呼び出す

    def deconvolute_button_callback(self):
        # deconvoluted_spectrum 初期化
        self.deconvoluted_spectrum=None
        self.update_deconvoluted_spectrum(self.deconvoluted_spectrum)

        # bg処理していないときは、bg_method="None"でsubtract_backgroundを実行
        if not flag_bg:
            x=copy.deepcopy(self.spectrum.x)
            y=copy.deepcopy(self.spectrum.y)
        else:
            x=copy.deepcopy(self.spectrum.x_bg)
            y=copy.deepcopy(self.spectrum.y_bg)        
        
        # Instrumental Function 生成 (spectrum.x_bg, spectrum.y_bg, spectrum.sがそれぞれx, i, sである。)
        if self.spread_combo.get()=="Gaussian":
            # spread func生成
            try:
                self.spectrum.generate_spread_function_for_deconvolution(x, self.spread_combo.get(), float(self.fwhm_s_textbox.get()))
            except ValueError:
                messagebox.showwarning('ValueError!','Please enter the parameters for the instrument function.')
            # plotを指令
            self.master.plot_data_frame.plot_spread_function(self.spectrum.x_s, self.spectrum.s, self.spread_combo.get())
        elif self.spread_combo.get()=="Import":
            # plotを指令 (すでにspread funcは生成済み)
            self.spectrum.generate_spread_function_for_deconvolution(x, self.spread_combo.get(), self.s_spectrum.y)
        
        # filtering
        if self.smoothing_combo.get()=="Auto-/Cross-correlation":
            self.spectrum.smooth_spectrum_with_auto_cross_colleration(y, self.spectrum.s)
            print(len(x),len(self.spectrum.i_ac))
            self.master.plot_data_frame.plot_auto_cross_correlation(x, y)

        elif self.smoothing_combo.get()=="None":
            self.spectrum.i_ac = copy.deepcopy(y)
            self.spectrum.s_cc = copy.deepcopy(self.spectrum.s)

        # rmseの範囲を決定
        if self.x_rmse_min_checkbox.get():
            x_rmse_min=np.amin(x)
        else:
            x_rmse_min=float(self.x_rmse_min_textbox.get())

        if self.x_rmse_max_checkbox.get():
            x_rmse_max=np.amax(x)
        else:
            x_rmse_max=float(self.x_rmse_max_textbox.get())
        
        # deconvolution 実行 ################################
        try:
            iteration_number=int(self.deconv_iteration_textbox.get())
        except ValueError:
            messagebox.showwarning('ValueError!','Please enter the maximum iteration number.')

        if self.deconv_method_combo.get()=="Jansson's method":
            self.spectrum.deconvolute_spectrum(x, y, self.spectrum.i_ac, self.spectrum.s_cc, iteration_number, x_rmse_min, x_rmse_max, 
                                          self.deconv_method_combo.get(), float(self.jansson_a_textbox.get()), float(self.jansson_b_textbox.get()), float(self.jansson_r0_textbox.get()))
        if self.deconv_method_combo.get()=="Gold's ratio method":
            self.spectrum.deconvolute_spectrum(x, y, self.spectrum.i_ac, self.spectrum.s_cc, iteration_number, x_rmse_min, x_rmse_max, self.deconv_method_combo.get())
        print("The spectrum was deconvoluted.")
        
        # deconvoluted spectraを何本表示させるか listのindexではなくて、kの値(1から始まる)で指定する。
        if self.spectrum.iteration_number > shown_deconvoluted_spectra_number: # iterationのほうが大きいときは、要素数をshow_timesとした等差数列を作成 (int型)
            iteration_number_to_show_deconvoluted_spectra = np.linspace(1, self.spectrum.iteration_number, shown_deconvoluted_spectra_number).astype(int)
        else: # iterationのほうが小さいときは、iterationのすべて表示 (int型)
            iteration_number_to_show_deconvoluted_spectra = np.arange(1, self.spectrum.iteration_number+0.5, 1).astype(int)
        # print(iteration_number_to_show_deconvoluted_spectra)

        # plotの指令を出す。
        self.master.plot_data_frame.plot_deconvoluted_spectra(x, y, iteration_number_to_show_deconvoluted_spectra)

    def detect_peak_button_callback(self):
        # deconvoluted_spectraのピーク検出をするため、新しいインスタンスを作る
        # data saveを同じファイルで行うため、pathなどをインスタンスspectrumと共通にする。
        self.deconvoluted_spectrum = Spectrum(USER, 
                                             x=self.spectrum.x_deconv, y_lst=self.spectrum.o_deconv_lst, 
                                             path=self.spectrum.path,
                                             x_legend=self.spectrum.x_legend, y_legend=self.spectrum.y_legend,
                                             filename=self.spectrum.filename)
        # deconvoluted spectrumの更新を通知
        self.update_deconvoluted_spectrum(self.deconvoluted_spectrum)

        # ピーク検出
        self.deconvoluted_spectrum.detect_peak_of_spectrum_lst(self.deconvoluted_spectrum.x, self.deconvoluted_spectrum.y_lst)
        print("The peak energies of deconvoluted spectra were detected.")

        # ピークエネルギーのiteration依存性をプロット (ポップアップ)
        pltctrl_peak_plots_of_deconvoluted_spectra = PlotControl("The peak plot of deconvoluted spectra",    
                                                                figsize_w=9, figsize_h=4, 
                                                                initialize_figs=True)
        pltctrl_peak_plots_of_deconvoluted_spectra.plot_rainbow_peak_plot(self.deconvoluted_spectrum.idx_y_peak_lst, 
                                                                    self.deconvoluted_spectrum.x_y_peak_lst,
                                                                    z=self.deconvoluted_spectrum.y_peak_lst)


# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(True, True) # 横はpixel数を固定
    app.mainloop()
    