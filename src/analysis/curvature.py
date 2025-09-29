import customtkinter
import platform

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
from setting.setting import App as SettingApp
from RyoPy import defs_for_analysis as rpa
from RyoPy.Frame import LoadImageDataFrame
from analysis.second_derivative import SecondDerivativeFrame

from pathlib import Path

# 現在のスクリプトの祖父母ディレクトリを取得
SRC_PATH = Path(__file__).resolve().parent.parent
print(SRC_PATH)
# ファイルパスを統一的に管理
default_setting_path = os.path.join(SRC_PATH, "setting", "default_setting.txt")
second_derivative_setting_path = os.path.join(SRC_PATH, "setting", "ARPES_image_setting.txt")
second_derivative_setting_path = os.path.join(SRC_PATH, "setting", "second_derivative_setting.txt")

# ファイル選択するときの初期値
IDIR, has_IDIR = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "folder_path", type="str")
USER, has_USER = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "user", type="str")
WINDOW_WIDTH, has_WINDOW_WIDTH = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "window_width_deconv")
WINDOW_height, has_WINDOW_height = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "window_height_deconv", type="str")
# font
FONT_TYPE = "Arial"  # デフォルト値
FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(default_setting_path, "font_type", type="str")

COLORMAP, has_COLORMAP = rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "colormap_photoemission_intensity_map", type="str")

COLORMAP = 'cividis'

# second derivativeのcolor map
# COLORMAP_SECOND_DERIVATIVE="bwr_r"
# COLORMAP_SECOND_DERIVATIVE="viridis"
# COLORMAP_SECOND_DERIVATIVE="cividis_r"
# COLORMAP_SECOND_DERIVATIVE='Blues_r'
COLORMAP_SECOND_DERIVATIVE=rpa.open_file_and_get_words_next_to_search_term(second_derivative_setting_path, "colormap_second_derivative", type="str")

'YlGnBu_r'


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
        self.title('SpecTaroscoPy — Curvature analysis')

        #アイコン
        # try:
        #     if platform.system() == "Darwin":  # macOS
        #         img_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'curvature.png')
        #         if os.path.exists(img_path):
        #             icon_image = PhotoImage(file=img_path).subsample(2, 2)  # 2倍に縮小（調整可能）
        #             self.tk.call('wm', 'iconphoto', self._w, icon_image)
        #     elif platform.system() == "Windows":  # Windows
        #         ico_path = os.path.join(CURRENT_PATH, 'img', 'icon', 'curvature.ico')
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
        self.curvature_frame = SecondDerivativeFrame(master=self, 
                                        header_name="Smoothing --> Curvature",
                                        spectrum=self.load_data_frame.spectrum, 
                                        image=self.load_data_frame.image,
                                        import_mode=self.load_data_frame.import_mode,
                                        imported_fig_instance_lst=self.load_data_frame.fig_instance_lst,
                                        second_derivative=False,
                                        curvature=True
                                        )
        self.curvature_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nse", columnspan=2)

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
        initial_tab = "2nd Div"  # タブを初期表示
        app = SettingApp(initial_tab=initial_tab)
        app.resizable(False, False)
        app.mainloop()
# 実行部
if __name__ == "__main__":
    app = App()
    app.resizable(True, True) # 横はpixel数を固定
    
    app.mainloop()