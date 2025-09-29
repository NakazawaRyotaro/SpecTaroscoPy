import customtkinter
# -------------------- モジュール読み込み --------------------
import sys
import os
import platform
from pathlib import Path

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


CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

DEFAULT_SETTING_PATH = os.path.join(CURRENT_PATH, "default_setting.txt")
ARPES_SETTING_PATH = os.path.join(CURRENT_PATH, "ARPES_image_setting.txt")
SECOND_DERIVATIVE_PATH = os.path.join(CURRENT_PATH, "second_derivative_setting.txt")
DECONV_SETTING_PATH = os.path.join(CURRENT_PATH, "deconvolution_setting.txt")
FITTING_SETTING_PATH = os.path.join(CURRENT_PATH, "fitting_setting.txt")

FONT_TYPE, has_FONT_TYPE = rpa.open_file_and_get_words_next_to_search_term(DEFAULT_SETTING_PATH, "font_type", type='str')

class App(customtkinter.CTk):
    def __init__(self, initial_tab='General'):  # 引数を追加
        super().__init__()
        self.fonts = (FONT_TYPE, 15)
        self.initial_tab = initial_tab  # 初期タブを設定
        self.setup_form()

    def setup_form(self):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        self.geometry("400x500")
        self.title("SpecTaroscoPy — Setting")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setting_frame = SettingFrame(master=self, header_name="Setting", initial_tab=self.initial_tab)
        self.setting_frame.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")

class SettingFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master=None, header_name="", initial_tab='General'):
        super().__init__(master=master)  # 親クラスのコンストラクタを呼び出し、masterを渡す
        self.fonts = (FONT_TYPE, 15)
        self.width = 120
        self.header_name = header_name
        self.initial_tab = initial_tab
        self.tab_view = customtkinter.CTkTabview(master=self, width=300, height=400)
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.font_tab = self.tab_view.add("General")
        self.font_tab_content = GeneralSettingTab(master=self.font_tab, fonts=self.fonts, width=self.width, setting_file_path=DEFAULT_SETTING_PATH)

        self.deconv_tab = self.tab_view.add("Fitting")
        self.deconv_tab_content = FittingSettingTab(master=self.deconv_tab, fonts=self.fonts, width=self.width, setting_file_path=FITTING_SETTING_PATH)

        self.deconv_tab = self.tab_view.add("Deconv")
        self.deconv_tab_content = DeconvolutionSettingTab(master=self.deconv_tab, fonts=self.fonts, width=self.width, setting_file_path=DECONV_SETTING_PATH)

        self.arpes_tab = self.tab_view.add("ARPES")
        self.arpes_tab_content = ARPESSettingTab(master=self.arpes_tab, fonts=self.fonts, width=self.width, setting_file_path=ARPES_SETTING_PATH)
    
        self.second_derivative_tab = self.tab_view.add("2nd Div")
        self.second_derivative_tab_content = SecondDerivativeSettingTab(master=self.second_derivative_tab, fonts=self.fonts, width=self.width, setting_file_path=SECOND_DERIVATIVE_PATH)

        # 初期表示するタブを設定
        self.tab_view.set(self.initial_tab)


# 共通のベースクラス
class BaseSettingTab(customtkinter.CTkFrame):
    def __init__(self, master, fonts, width, setting_file_path):
        super().__init__(master)
        self.fonts = fonts
        self.width = width
        self.grid(row=0, column=0, sticky="nsew")
        self.file_path = setting_file_path

        self.entries = {}
        self.define_settings()
        for row, (label_text, config_key) in enumerate(self.settings, start=1):
            self._create_label_entry_pair(row, label_text, config_key)

        save_button = customtkinter.CTkButton(self, text="Save", font=self.fonts, command=self.save_settings, width=self.width)
        save_button.grid(row=len(self.settings) + 1, column=1, padx=10, pady=(10, 10), sticky="w")

    def define_settings(self):
        """サブクラスでオーバーライドして設定内容を定義"""
        self.settings = []

    def _create_label_entry_pair(self, row, label_text, config_key):
        pady_label_entry = (0, 5)

        # 小見出し
        if config_key == "":
            label = customtkinter.CTkLabel(self, text=label_text, font=self.fonts, width=self.width)
            label.grid(row=row, column=0, columnspan=4, padx=10, pady=(15 if row == 1 else 8, 5), sticky="w")
            return
        
        # LabelとEntrybox
        label = customtkinter.CTkLabel(self, text=label_text, width=self.width)
        label.grid(row=row, column=0, padx=10, pady=pady_label_entry, sticky="w")
        try:
            value, has_value = rpa.open_file_and_get_words_next_to_search_term(self.file_path, config_key)
        except:
            value, has_value = rpa.open_file_and_get_words_next_to_search_term(self.file_path, config_key, type='str')
        if has_value != 1:
            value, has_value = rpa.open_file_and_get_words_next_to_search_term(self.file_path, str(config_key), type='str')

        entry = customtkinter.CTkEntry(self, placeholder_text="", font=self.fonts, width=self.width)
        entry.grid(row=row, column=1, padx=10, pady=pady_label_entry, sticky="w")

        if has_value:
            entry.insert(0, value)

        self.entries[config_key] = entry

    def save_settings(self):
        for config_key, entry in self.entries.items():
            rpa.write_name(self.file_path, config_key, entry.get())

# 各タブの定義（設定項目のみ上書き）
class GeneralSettingTab(BaseSettingTab):
    def define_settings(self):
        version = rpa.open_file_and_get_words_next_to_search_term(self.file_path, 'version', type='str')[0]
        self.settings = [
            (f"SpecTaroscoPy ver. {version}", ""),
            
            ("Username:", "user"),
            ("Default Folder Path:", "folder_path"),
            ('Font Type:', 'font_type'),
        ]

class DeconvolutionSettingTab(BaseSettingTab):
    def define_settings(self):
        self.settings = [
            ("Window Settings", ""),
            ("height:", "window_height_deconv"),
            ("Width:", "window_width_deconv"),
        ]

class FittingSettingTab(BaseSettingTab):
    def define_settings(self):
        self.settings = [
            ("Window Settings", ""),
            ("height:", "window_height"),
            ("Width:", "window_width"),
            ("Fit EDCs Settings", ""),
            ("Keyword of Y2:", "key_y2"),
            ("Keyword of Y2 Label:", "key_y2_label"),
        ]

class SecondDerivativeSettingTab(BaseSettingTab):
    def define_settings(self):
        self.settings = [
            ('Color Settings',''),
            ("Colormap\n(Input Image):", "colormap_photoemission_intensity_map"),
            ("Colormap\n(Output Image):", "colormap_second_derivative"),
        ]

class ARPESSettingTab(BaseSettingTab):
    def define_settings(self):
        self.settings = [
            ("Window Settings", ""),
            ("Width:", "window_width_photoemission_intensity_map"),
            ("Height:", "window_height_photoemission_intensity_map"),
            ("Figure Settings", ""),
            ("Colormap\n(Image):", "colormap_photoemission_intensity_map"),
            ("Color\n(EDC):", "color_edc"),
            ("Figure Width:", 'image_width_photoemission_intensity_map'),
            ("Figure Height:",'image_height_photoemission_intensity_map'),

            ("EF Settings (MBS A-1, Kera G)", ""),
            ("XeIa, PE02:", "EF_XeIa_Ep02_MBSA1_KeraG"),
            ("XeIa, PE05:", "EF_XeIa_Ep05_MBSA1_KeraG"),
            ("XeIa, PE10:", "EF_XeIa_Ep10_MBSA1_KeraG"),
            ("XeIa, PE20:", "EF_XeIa_Ep20_MBSA1_KeraG"),
            
            ("HeIa, PE02:", "EF_HeIa_Ep02_MBSA1_KeraG"),
            ("HeIa, PE05:", "EF_HeIa_Ep05_MBSA1_KeraG"),
            ("HeIa, PE10:", "EF_HeIa_Ep10_MBSA1_KeraG"),
            ("HeIa, PE20:", "EF_HeIa_Ep20_MBSA1_KeraG"),

            ("HeIIa, PE02:", "EF_HeIIa_Ep02_MBSA1_KeraG"),
            ("HeIIa, PE05:", "EF_HeIIa_Ep05_MBSA1_KeraG"),
            ("HeIIa, PE10:", "EF_HeIIa_Ep10_MBSA1_KeraG"),
            ("HeIIa, PE20:", "EF_HeIIa_Ep20_MBSA1_KeraG"),

            ("AlKa, PE100:", "EF_AlKa_Ep100_MBSA1_KeraG"),
            ("MgKa, PE100:", "EF_MgKa_Ep100_MBSA1_KeraG"),

            ("EF Settings (MBS A-1, G1, BL7U, UVSOR)", ""),
            ("hn, PE02:", "hn_variable_hn_Ep02_G1_MBSA1_BL7U"),
            ("EF, PE02:", "EF_variable_hn_Ep02_G1_MBSA1_BL7U"),
            ("hn, PE05:", "hn_variable_hn_Ep05_G1_MBSA1_BL7U"),
            ("EF, PE05:", "EF_variable_hn_Ep05_G1_MBSA1_BL7U"),
            ("hn, PE10:", "hn_variable_hn_Ep10_G1_MBSA1_BL7U"),
            ("EF, PE10:", "EF_variable_hn_Ep10_G1_MBSA1_BL7U"),
            ("hn, PE20:", "hn_variable_hn_Ep20_G1_MBSA1_BL7U"),
            ("EF, PE20:", "EF_variable_hn_Ep20_G1_MBSA1_BL7U"),

            ("EF Settings (MBS A-1, G2, BL7U, UVSOR)", ""),
            ("hn, PE02:", "hn_variable_hn_Ep02_G2_MBSA1_BL7U"),
            ("EF, PE02:", "EF_variable_hn_Ep02_G2_MBSA1_BL7U"),
            ("hn, PE05:", "hn_variable_hn_Ep05_G2_MBSA1_BL7U"),
            ("EF, PE05:", "EF_variable_hn_Ep05_G2_MBSA1_BL7U"),
            ("hn, PE10:", "hn_variable_hn_Ep10_G2_MBSA1_BL7U"),
            ("EF, PE10:", "EF_variable_hn_Ep10_G2_MBSA1_BL7U"),
            ("hn, PE20:", "hn_variable_hn_Ep20_G2_MBSA1_BL7U"),
            ("EF, PE20:", "EF_variable_hn_Ep20_G2_MBSA1_BL7U"),

            ("EF Settings (MBS A-1, G3, BL7U, UVSOR)", ""),
            ("hn, PE02:", "hn_variable_hn_Ep02_G3_MBSA1_BL7U"),
            ("EF, PE02:", "EF_variable_hn_Ep02_G3_MBSA1_BL7U"),
            ("hn, PE05:", "hn_variable_hn_Ep05_G3_MBSA1_BL7U"),
            ("EF, PE05:", "EF_variable_hn_Ep05_G3_MBSA1_BL7U"),
            ("hn, PE10:", "hn_variable_hn_Ep10_G3_MBSA1_BL7U"),
            ("EF, PE10:", "EF_variable_hn_Ep10_G3_MBSA1_BL7U"),
            ("hn, PE20:", "hn_variable_hn_Ep20_G3_MBSA1_BL7U"),
            ("EF, PE20:", "EF_variable_hn_Ep20_G3_MBSA1_BL7U")
        ]

# 実行
if __name__ == "__main__":
    app = App()
    app.resizable(True, True)
    app.mainloop()