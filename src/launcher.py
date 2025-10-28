import customtkinter
import subprocess
import platform
from pathlib import Path
from tkinter import PhotoImage

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

from RyoPy import defs_for_analysis as rpa

# srcディレクトリを取得
SRC_DIRECTORY = Path(__file__).resolve().parent
# print(CURRENT_PATH)
# ファイルパスを統一的に管理
DEFAULT_SETTING_PATH = os.path.join(SRC_DIRECTORY, "setting", "default_setting.txt")
print(f"Default setting path: {DEFAULT_SETTING_PATH}")

FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(DEFAULT_SETTING_PATH, "font_type", type='str')
if not has_FONT_TYPE:
    FONT_TYPE = 'meiryo'
VERSION, has_VERSION = rpa.open_file_and_get_words_next_to_search_term(DEFAULT_SETTING_PATH, 'version', type='str')

WINDOW_WIDTH = 615
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

        #アイコン
        try:
            if platform.system() == "Darwin":  # macOS
                img_path = os.path.join(SRC_DIRECTORY, 'img', 'icon', 'SpecTaroscoPy.png')
                if os.path.exists(img_path):
                    icon_image = PhotoImage(file=img_path).subsample(1, 1)  # 2倍に縮小（調整可能）
                    self.tk.call('wm', 'iconphoto', self._w, icon_image)
            elif platform.system() == "Windows":  # Windows
                ico_path = os.path.join(SRC_DIRECTORY, 'img', 'icon', 'SpecTaroscoPy.ico')
                if os.path.exists(ico_path):
                    self.iconbitmap(ico_path)
        except:
            pass

        # フォームサイズ設定
        self.geometry(f"{WINDOW_WIDTH}x400")
        self.title(f"SpecTaroscoPy – ver. {VERSION}")

        # 行方向のマスのレイアウトを設定する。リサイズしたときに一緒に拡大したい行をweight 1に設定。
        self.grid_rowconfigure(2, weight=1) # 2+1のフレームが広がる
        # 列方向のマスのレイアウトを設定する
        self.grid_columnconfigure(0, weight=1)

        # 1つ目のフレームの設定
        # stickyは拡大したときに広がる方向のこと。nsew で4方角で指定する。
        self.Intro_frame = IntroFrame(master=self, header_name="Introduction")
        self.Intro_frame.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")

        # 2つ目のフレーム設定
        self.set_default_frame = SetDefaultFrame(master=self, header_name="Default") 
        self.set_default_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")

        # 3つ目のフレーム設定
        self.chose_analysis_frame = ChoseAnalysisFrame(master=self, header_name="Analysis") 
        self.chose_analysis_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nsew")

        # 4つ目のフレーム設定
        self.chose_analysis_frame = OthersFrame(master=self, header_name="Others") 
        self.chose_analysis_frame.grid(row=3, column=0, padx=10, pady=(0,10), sticky="nsew")

# introduction
class IntroFrame(customtkinter.CTkFrame): # GUI上部
    def __init__(self, *args, header_name="ReadFileFrame", **kwargs):
        super().__init__(*args, **kwargs)

        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # 行方向のマスのレイアウトを設定する。リサイズしたときに一緒に拡大したい行をweight 1に設定。
        self.introduction_label = customtkinter.CTkLabel(master=self, text="Welcome to \"SpecTaroscoPy\" — a spectroscopy analysis tool.\nPlease select a module from the options below. If you encounter any errors\n(or if the results are incorrect), please contact Ryotaro Nakazawa at\n\"nakazawa@ims.ac.jp\".", 
                                                        font=self.fonts, width=WINDOW_WIDTH-40)
        self.introduction_label.grid(row=1, column=0, padx=(0,0), pady=(10,10), sticky="ewns")

# set default
class SetDefaultFrame(customtkinter.CTkFrame): # GUI中部
    def __init__(self, *args, header_name="", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        self.label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        self.label.grid(row=0, column=0, padx=10, sticky="w")

        # user name
        user_label = customtkinter.CTkLabel(master=self, text='User Name:', width=60)
        user_label.grid(row=1, column=0, padx=(20,10), pady=(0,15), sticky="ew") 
        USER, has_your_name = rpa.open_file_and_get_words_next_to_search_term(DEFAULT_SETTING_PATH, "user", type="str")
        self.user_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Your Name", width=120, font=self.fonts)
        self.user_textbox.grid(row=1, column=1, padx=(0,10), pady=(0,15), sticky="w")
        if has_your_name:
            self.user_textbox.insert(0, USER) #初期値

        # folder file
        folder_path_label = customtkinter.CTkLabel(master=self, text='Folder Path:', width=60)
        folder_path_label.grid(row=1, column=2, padx=10, pady=(0,15), sticky="ew")
        IDIR, has_default_folder = rpa.get_words_next_to_search_term(DEFAULT_SETTING_PATH, "folder_path", type="str")
        self.folder_path_textbox = customtkinter.CTkEntry(master=self, placeholder_text="Absolute Path", width=120, font=self.fonts)
        self.folder_path_textbox.grid(row=1, column=3, columnspan=1, padx=(0, 10), pady=(0,15), sticky="we")
        if has_default_folder:
            self.folder_path_textbox.insert(0, IDIR) #初期値

        # Saveボタン生成
        self.graph_now_button = customtkinter.CTkButton(master=self, command=self.save_button_callback, text="Save", font=self.fonts, width=120)
        self.graph_now_button.grid(row=1, column=4, padx=(0, 20), pady=(0,15), sticky="ew")

    def save_button_callback(self):
        """
        開くボタンが押されたときのコールバック。入力した文字をテキストに書き込む
        """
        rpa.write_name(DEFAULT_SETTING_PATH, "user", self.user_textbox.get())
        rpa.write_name(DEFAULT_SETTING_PATH, "folder_path", self.folder_path_textbox.get())


# open analysis program
class ChoseAnalysisFrame(customtkinter.CTkFrame): # GUI下部
    def __init__(self, *args, header_name="", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11)).grid(row=0, column=0, padx=10, sticky="w")

        fitting_button = customtkinter.CTkButton(master=self, text="Fitting", font=self.fonts, command=lambda: self.analysis_button_callback(0))
        fitting_button.grid(row=1, column=0, padx=(10, 0), pady=(0,5), sticky="ew")

        deconvolution_button = customtkinter.CTkButton(master=self, text="Deconvolution", font=self.fonts, command=lambda: self.analysis_button_callback(1))
        deconvolution_button.grid(row=1, column=1, padx=(5, 0), pady=(0,5), sticky="ew")

        pes_intensity_map_button = customtkinter.CTkButton(master=self, text="PES Image", font=self.fonts, command=lambda: self.analysis_button_callback(3))
        pes_intensity_map_button.grid(row=1, column=3, padx=(5, 0), pady=(0,5), sticky="ew")

        deflector_map_button = customtkinter.CTkButton(master=self, text="(D)Deflector Map", font=self.fonts, command=lambda: self.analysis_button_callback(5))
        deflector_map_button.grid(row=1, column=4, padx=(5, 10), pady=(0,5), sticky="ew")

        second_derivative_button = customtkinter.CTkButton(master=self, text="Second Derivative", font=self.fonts, command=lambda: self.analysis_button_callback(2))
        second_derivative_button.grid(row=2, column=0, padx=(10, 0), pady=(0,10), sticky="ew")

        curvature_button = customtkinter.CTkButton(master=self, text="Curvature", font=self.fonts, command=lambda: self.analysis_button_callback(4))
        curvature_button.grid(row=2, column=1, padx=(5, 0), pady=(0,10), sticky="ew")

    def analysis_button_callback(self, button_id):
        if button_id == 0:
            print("Fitting Analysis")
            app_path = os.path.join(SRC_DIRECTORY, 'analysis', 'fitting.py')
        
        elif button_id == 1:
            print("Deconvolution Analysis")
            app_path = os.path.join(SRC_DIRECTORY, 'analysis', 'deconvolution.py')
            
        elif button_id == 2:
            print("Second Derivative Analysis")
            app_path = os.path.join(SRC_DIRECTORY, 'analysis', 'second_derivative.py')

        elif button_id == 3:
            print("Image Data Analysis")
            app_path = os.path.join(SRC_DIRECTORY, 'analysis', 'arpes_image.py')

        elif button_id == 4:
            print("Curvature Analysis")
            app_path = os.path.join(SRC_DIRECTORY, 'analysis', 'curvature.py')

        elif button_id == 5:
            print("Deflector Map Analysis")
            # app_path = os.path.join(PARENT_DIRECTORY, 'deflector_map.py')

        # app起動
        subprocess.Popen(['python', app_path], start_new_session=True)

# open analysis program
class OthersFrame(customtkinter.CTkFrame): # GUI下部
    def __init__(self, *args, header_name="OthersFrame", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fonts = (FONT_TYPE, 15)
        self.header_name = header_name

        # フォームのセットアップをする
        self.setup_form()

    def setup_form(self):
        # フレームのラベルを表示
        self.label = customtkinter.CTkLabel(self, text=self.header_name, font=(FONT_TYPE, 11))
        self.label.grid(row=0, column=0, padx=10, sticky="w")

        self.manual_button = customtkinter.CTkButton(master=self, text="Manual", font=self.fonts, command=self.open_manual_button_callback)
        self.manual_button.grid(row=1, column=0, padx=(10, 0), pady=(0,10), sticky="ew")

        self.setting_button = customtkinter.CTkButton(master=self, text="Setting", font=self.fonts, command=self.setting_button_callback)
        self.setting_button.grid(row=1, column=1, padx=(5, 0), pady=(0,10), sticky="ew")

    def open_manual_button_callback(self):
        # 現在のスクリプトの親ディレクトリを取得
        parent_directory = os.path.dirname(os.path.abspath(__file__))
        # 親ディレクトリにあるmanual.pdfのパスを作成
        pdf_path = os.path.join(parent_directory, '..', 'manual.pdf')
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

    def setting_button_callback(self):
        # subproseccでアプリを起動
        app_path = os.path.join(SRC_DIRECTORY,'setting', 'setting.py')
        # 起動
        subprocess.Popen(['python', app_path], start_new_session=True)

# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(False, False)  # 幅と高さの変更を無効にする
    app.mainloop()