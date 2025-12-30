import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.widgets import Slider
from matplotlib.ticker import ScalarFormatter

class PlotControl:
    """
    matplotlib でプロットを行う
    """
    def __init__(self, title="", y_scale="linear", figsize_w=3, figsize_h=2, initialize_figs=False, fontsize=7, fonttype="Arial", x_label="X", y_label="Y", plt_interaction=False):
        if plt_interaction:
            plt.ion()
        else:
            plt.ioff()  # インタラクティブモードを無効化
        if initialize_figs:
            plt.close('all')  # 以前のすべての図を閉じる
        self.figsize_w=figsize_w # horizontal
        self.figsize_h=figsize_h # vertical
        self.fontsize=fontsize
        self.x_label=x_label
        self.y_label=y_label
        self.title=title
        self.ax_right=None
        self.line0=[]
        self.scatter0=[]
        self.line=[]
        self.scatter=[]
        self.fontsize=fontsize
        plt.rcParams.update({'font.size': self.fontsize})  # フォントサイズを設定
        plt.rcParams['font.family'] = fonttype
        self.y_scale=y_scale
        self.fig = plt.figure(figsize=(self.figsize_w, self.figsize_h), constrained_layout=True)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        if not title=="":
            self.ax.set_title(self.title, fontdict={"fontsize": self.fontsize*0.8})
        self.ax.set_yscale(self.y_scale)
        
        self.ax.autoscale()
        self.fig.canvas.draw_idle()

    # xとyでscatterプロット (初回)
    def plot_spectrum(self, x, y, label, new_x_label=None, new_y_label=None, new_title=None, color="tab:gray", 
                      scatter=True, scientific_yscale=True, linewidth=2):
        self.color=color
        if scatter:
            self.scatter0.append(self.ax.scatter(x, y, label=label, color=self.color, s=10, zorder=0.5))
        else:
            self.line0.append(self.ax.plot(x, y, label=label, color=self.color, linewidth=linewidth))
        self.ax.legend(loc="best")
        if new_x_label is not None:
            self.x_label=new_x_label
        self.ax.set_xlabel(self.x_label)
        if new_y_label is not None:
            self.y_label=new_y_label
        self.ax.set_ylabel(self.y_label)
        if new_title is not None:
            self.title=new_title
        self.ax.set_title(self.title, fontdict={"fontsize": self.fontsize})
        try:
            self.ax.set_yscale(self.y_scale)
        except:
            pass
        
        # Y軸を指数表記に設定 (標準機能)
        if scientific_yscale:
            self.ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))  # フォーマッタをScalarFormatterに設定
            self.ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))  # scilimits=(0,0)で強制的に指数表記にする

        self.ax.autoscale()      
        self.fig.canvas.draw_idle()       

    # スペクトルを追加する
    def add_spectrum(self, x, y, label, new_title=None, new_x_label=None, new_y_label=None, color=None, alpha=1, 
                     scatter=True, linewidth=3, linestyle="-", scientific_yscale=True, zorder=1, s=10, edgecolor="default"):
        if edgecolor=="default":
            edgecolor=color
        if scatter:
            self.scatter.append(self.ax.scatter(x, y, label=label, s=s, facecolor=color, edgecolor=edgecolor, alpha=alpha, zorder=zorder))
        else:
            self.line.append(self.ax.plot(x, y, label=label, color=color, alpha=alpha, zorder=zorder, linewidth=linewidth, linestyle=linestyle))
        
        if new_title is not None:
            self.title=new_title
            self.ax.set_title(self.title, fontdict={"fontsize": self.fontsize*0.8})
        if new_x_label is not None:
            self.x_label=new_x_label
        self.ax.set_xlabel(self.x_label)
        if new_y_label is not None:
            self.y_label=new_y_label
        self.ax.set_ylabel(self.y_label)
        if label!=None and label!="":
            self.ax.legend(loc="best")

        # Y軸を指数表記に設定 (標準機能)
        if scientific_yscale:
            self.ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))  # フォーマッタをScalarFormatterに設定
            self.ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))  # scilimits=(0,0)で強制的に指数表記にする

        self.ax.autoscale()
        self.fig.canvas.draw_idle()

    # scatterを消す
    def remove_scatter_spectrum(self, num=0):
        try:
            # scatterの場合（PathCollectionオブジェクト）
            scatter_to_remove = self.scatter[num]
            scatter_to_remove.remove()

            # リストから削除したscatterを削除
            del self.scatter[num]

            # グラフの再描画
            self.ax.figure.canvas.draw()

        except IndexError:
            print(f"Error: No scatter exists at index {num}")
        except Exception as e:
            print(f"Error while removing scatter: {e}")
        self.fig.canvas.draw_idle()

    # lineを消す
    def remove_line_spectrum(self, num=0):
        try:
            # インデックスが範囲内であることを確認
            if num >= len(self.line):
                print(f"Error: No line exists at index {num}")
                return
            
            # 指定されたインデックスのラインを取得
            lines_to_remove = self.line[num]
            
            # もし取得したものがリストであれば、全てのラインを削除
            if isinstance(lines_to_remove, list):
                for line in lines_to_remove:
                    line.remove()
            # もし取得したものが単一のラインであれば、そのラインを削除
            elif isinstance(lines_to_remove, plt.lines.Line2D):
                lines_to_remove.remove()
            else:
                print(f"Error: Unexpected type at index {num}")
                return
            
            # リストから削除したラインを削除
            del self.line[num]
            
        except IndexError:
            print(f"Error: No line exists at index {num}")
        except Exception as e:
            print(f"Error while removing line: {e}")
        self.fig.canvas.draw_idle()

    def update_canvas(self):
        try:
            self.fig.tight_layout()
        except ValueError:
            # tight_layoutが失敗した場合は、単に再描画する
            pass    
        self.fig.canvas.draw_idle()

    def clear_plot(self):
        # 左軸（メインのax）をクリア
        self.ax.clear()
        if hasattr(self, 'ax_right') and self.ax_right is not None:
            self.ax_right.lines.clear()
        # カラーバーが存在する場合は削除
        if hasattr(self, 'cbar') and self.cbar is not None:
            self.cbar.remove()
        # グラフの再描画
        self.fig.canvas.draw_idle()

    def show_figures(self):
        # plt show()でたまってた分をすべて表示する。
        plt.show()
        # グラフの再描画
        self.fig.canvas.draw_idle()

    def adjust_layout_for_left_align(self, offset=0.1):        
        # タイトレイアウトで初期的な余白を調整
        self.fig.tight_layout()

        # Axesの位置を取得
        box = self.ax.get_position()
        # 現在の左余白を取得して、左寄せするためのオフセットを調整
        offset = 0.1  # 左寄せの度合いを指定
        new_left = offset
        new_width = box.width * (1 - offset)  # グラフの幅を調整
        
        # 位置を左寄せして更新
        self.ax.set_position([new_left, box.y0, new_width, box.height])

        # 再描画
        self.fig.canvas.draw_idle()
    
    def add_deconvoluted_spectra(self, x, y_lst, iteration_number_lst, 
                                 new_x_label=None, new_y_label=None, new_c_label=None, colorbar=True, linecolor="tab:blue"):
        #カラーバー作成
        cmap = plt.cm.hsv
        norm = plt.Normalize(vmin=1, vmax=max(iteration_number_lst))
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])  # カラーマップにデータを関連付けない（ダミーデータを設定）

        for i in range(len(iteration_number_lst)):
            if colorbar:
                color = cmap(norm(i)/0.9) #カラーバーの変数
                # plot
                self.ax.plot(x, y_lst[iteration_number_lst[i]-1],
                            color=color, 
                            alpha=0.5,
                            linewidth=2,
                            zorder=0,
                            # label="k="+str(i),
                            )

            else: # colorbarを使用せず単色 (linecolor)
                if new_c_label is not None:
                    c_label=new_c_label
                else:
                    c_label="Iteration Number"

                self.ax.plot(x, y_lst[i-1], linewidth=1.5, color=linecolor, label=f"{str(iteration_number_lst[i])} {c_label}")
                self.ax.legend(loc="best")
        
        plt.tight_layout()        
    
        if colorbar:
            # カラーバーを設定
            cbar = plt.colorbar(sm, ax=self.ax, format='%d')
            cbar.ax.tick_params()  # カラーバーの文字の大きさを設定
            cbar.set_label("Iteration Number")
            
            if new_c_label is not None:
                if colorbar:
                    cbar.set_label(new_c_label)
        
        # labelの更新
        if new_x_label is not None:
            self.ax.set_xlabel(new_x_label)
        if new_y_label is not None:
            self.ax.set_ylabel(new_y_label)

        # レイアウト、軸再調整
        self.ax.autoscale()

    def plot_rainbow_iteration_number(self, x, y, plotsize=5):
        #カラーバー作成
        cmap = plt.cm.hsv
        norm = plt.Normalize(vmin=1, vmax=max(x))
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])  # カラーマップにデータを関連付けない（ダミーデータを設定）

        for i in range(len(x)):
            color = cmap(norm(i)/0.9) #カラーバーの変数

            self.ax.scatter(x[i], y[i], 
                            color=color,
                            alpha=0.5,
                            linewidth=2,
                            zorder=0,
                            s=plotsize) 
        plt.tight_layout()
        # カラーバーを設定
        cbar = plt.colorbar(sm, ax=self.ax, format='%d')
        cbar.ax.tick_params()  # カラーバーの文字の大きさを設定
        cbar.set_label("Iteration Number")
        self.ax.set_xlabel("Iteration Number")
        self.ax.set_ylabel("Y")
        # レイアウト、軸再調整
        self.ax.autoscale()
        self.fig.canvas.draw_idle()

    def change_legend_position(self, mode, bbox_x=1, bbox_y=0.5, fontsize='small', labelspacing=0.25, ncol=1):
        if mode=="edcs":
            self.ax.legend(loc="center left", bbox_to_anchor=(bbox_x, bbox_y), fontsize=fontsize, labelspacing=labelspacing, ncol=ncol)
        elif mode=="best":
            self.ax.legend(loc="best", fontsize=fontsize, labelspacing=labelspacing)
        elif mode==None:
            self.ax.legend(loc="best", fontsize=fontsize, labelspacing=labelspacing) # error回避のため一度legendを作る
            self.ax.get_legend().remove()
        # レイアウト、軸再調整
        plt.tight_layout()
        self.fig.canvas.draw_idle()

    def plot_rainbow_peak_plot(self, x_lst, y_lst, z=[], plotsize=20):
        # 強度情報zがあれば、プロットの大きさとして表現する。
        #カラーバー作成
        cmap = plt.cm.hsv
        
        if not z==[]:
            # 最大値を見つける
            max_value = max(max(sublist) for sublist in z)
            # 各要素を最大値で割る
            z = [[element / max_value for element in sublist] for sublist in z]

        norm = plt.Normalize(vmin=1, vmax=x_lst[-1][0])
        sm = ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])  # カラーマップにデータを関連付けない（ダミーデータを設定）

        for i in range(len(x_lst)):
            color = cmap(norm(i)/0.9) #カラーバーの変数
            for j in range(len(x_lst[i])):
                if z == []:
                    self.ax.scatter(x_lst[i][j]+1, y_lst[i][j], 
                                    color=color,
                                    alpha=0.5,
                                    zorder=0,
                                    s=plotsize)
                    
                else:
                    self.ax.scatter(x_lst[i][j]+1, y_lst[i][j], 
                                    color=color,
                                    alpha=0.5,
                                    zorder=0,
                                    s=plotsize*z[i][j])
                            
        # カラーバーを設定
        cbar = plt.colorbar(sm, ax=self.ax, format='%d')
        cbar.ax.tick_params()  # カラーバーの文字の大きさを設定
        cbar.set_label("Iteration Number")
        self.ax.set_xlabel("Iteration Number")
        self.ax.set_ylabel("X")
        plt.minorticks_on()
        plt.grid(which = "minor", axis="y", linestyle="--")
        plt.grid(which = "major", axis="y", linestyle="-")
        # レイアウト、軸再調整
        self.ax.autoscale()
        # plt.tight_layout() # run time error回避のためコメントアウト
        plt.show() 
        self.fig.canvas.draw_idle()

    def change_yscale(self):
        if self.y_scale=="linear":
            self.y_scale="log"
        elif self.y_scale=="log":
            self.y_scale="linear"
        self.ax.set_yscale(self.y_scale)
        # self.ax.autoscale()
        self.fig.canvas.draw_idle()

    def set_range(self, x_lim_min=None, x_lim_max=None, y_lim_min=None, y_lim_max=None):
        # 新しくlimitationをセット
        if y_lim_min!=None and y_lim_max!=None:
            # self.ax.set_ylim(y_lim_min, y_lim_max)

            # データ範囲
            data_range = y_lim_max - y_lim_min
            # 余白の割合を設定 (例: 10%)
            margin_ratio = 0.05
            # 余白を考慮した新しい範囲を設定
            new_min = y_lim_min - data_range * margin_ratio
            new_max = y_lim_max + data_range * margin_ratio
            # グラフのY軸範囲を設定
            self.ax.set_ylim(new_min, new_max)
            
        if x_lim_min!=None and x_lim_max!=None:
            # self.ax.set_xlim(x_lim_min, x_lim_max)

            # データ範囲
            data_range = x_lim_max - x_lim_min
            # 余白の割合を設定 (例: 10%)
            margin_ratio = 0.05
            # 余白を考慮した新しい範囲を設定
            new_min = x_lim_min - data_range * margin_ratio
            new_max = x_lim_max + data_range * margin_ratio
            # グラフのY軸範囲を設定
            self.ax.set_xlim(new_min, new_max)
        
        # グラフの再描画
        self.fig.canvas.draw_idle() 

    def close_figure(self):
        """現在のインスタンスの図を閉じる"""
        self.clear_plot()
        plt.close(self.fig)

    def show_figure_at_position(self, x_posi, y_posi):
        """ポップアップウィンドウの位置を設定"""
        manager = plt.get_current_fig_manager()
        try:
            # tkinter backend を使用している場合
            manager.window.wm_geometry(f"+{x_posi}+{y_posi}")
        except AttributeError:
            # Qt backend を使用している場合
            manager.window.setGeometry(x_posi, y_posi, manager.window.width(), manager.window.height())
            

class ImagePlotControl:
    def __init__(self, x, y, z, 
                 colormap="Spectral_r", title="", z_scale="linear", 
                 x_label="X", y_label="Y", z_label="Z",
                 figsize_w=5.8, figsize_h=3.3, plt_interaction=False, fontsize=12, 
                 slider=False, scientific_zscale=True):
        
        self.plt_interaction = plt_interaction
        self.slider = slider  # slider引数を保存
        self.scientific_zscale = scientific_zscale

        # plt_interaction に基づいてインタラクティブモードを設定
        if self.plt_interaction:
            plt.ion()
        else:
            plt.ioff()  # インタラクティブモードを無効化
        
        self.x = x
        self.y = y
        self.z = z
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label
        self.colormap = colormap
        self.title = title
        self.figsize_h = figsize_h
        self.figsize_w = figsize_w
        self.z_scale = z_scale
        self.pcolormesh = None  # pcolormesh を保存するための変数
        self.colorbar = None  # カラーバーを保持するためのインスタンス変数
        self.ax = None
        self.lines = []
        self.fontsize = fontsize

        plt.rcParams.update({'font.size': self.fontsize})
        plt.rcParams['font.family'] = 'Arial'

        # plotの作成
        self.plot_image(self.x, self.y, self.z, new_x_label=x_label, new_y_label=y_label)


    def plot_image(self, x, y, z, new_x_label=None, new_y_label=None):
        self.x = x
        self.y = y
        self.z = z

        # 既存のFigureが存在する場合、それを閉じる
        if hasattr(self, 'fig') and self.fig is not None:
            plt.close(self.fig)
        
        self.fig = plt.figure(figsize=(self.figsize_w, self.figsize_h), tight_layout=False)

        if self.slider: # グリッド定義（上下2行、1列）
            # 全体を 5行×10列 のグリッドにする（左右10%ずつスペース → 中央8列使用）
            self.ax = plt.subplot2grid((5, 12), (0, 1), rowspan=4, colspan=10)  # 上図：画像（上4行、左右1列空ける）
            self.slider_ax = plt.subplot2grid((5, 10), (4, 1), colspan=10)      # 下図：スライダー（下1行、左右1列空ける）
            self.slider_ax.set_axis_off()  # 空グラフは消す
        else:
            self.ax = self.fig.add_subplot(1, 1, 1)

            
        # colorbar zを定義->plot->colorbar作成
        if not hasattr(self, 'norm'):  # normがまだ設定されていない場合のみ設定
            self.norm = Normalize(vmin=np.min(self.z), vmax=np.max(self.z))
        self.pcolormesh = self.ax.pcolormesh(self.x, self.y, self.z, cmap=self.colormap, norm=self.norm, shading="auto")
        self.colorbar = self.fig.colorbar(self.pcolormesh, ax=self.ax, orientation="vertical")
        if self.colorbar is not None:
            self.colorbar.set_label(self.z_label)
        
        if self.z_scale == "log":
            self.ax.set_zscale("log")

        if self.title:
            self.ax.set_title(self.title, fontdict={"fontsize": self.fontsize*0.8})

        self.ax.set_xlabel(new_x_label or self.x_label)
        self.ax.set_ylabel(new_y_label or self.y_label)

        if self.scientific_zscale:
            self.colorbar.ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
            self.colorbar.ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

        self.ax.autoscale()
        self.fig.tight_layout()

        # スライダーを追加
        if self.plt_interaction and self.slider:
            self.add_slider()

        if self.plt_interaction:
            plt.show(block=False)
            self.fig.canvas.draw_idle()

    def add_slider(self, factor_inf=2):
        def replace_invalid_values(z):
            z_flat = np.ravel(z)
            valid_values = z_flat[np.isfinite(z_flat)]
            z_max = np.max(valid_values)
            z_min = np.min(valid_values)
            z_flat = np.where(np.isnan(z_flat), 0, z_flat)
            z_flat = np.where(np.isposinf(z_flat), factor_inf * z_max, z_flat)
            z_flat = np.where(np.isneginf(z_flat), factor_inf * z_min, z_flat)
            return z_flat.reshape(z.shape), z_min, z_max

        self.z, z_min, z_max = replace_invalid_values(self.z)
        initial_min = z_min
        initial_max = z_max

        ax_slider_min = self.fig.add_axes([0.175, 0.01, 0.65, 0.025])
        ax_slider_max = self.fig.add_axes([0.175, 0.06, 0.65, 0.025])

        self.slider_min = Slider(ax_slider_min, 'Min Z', z_min, z_max, valinit=initial_min)
        self.slider_max = Slider(ax_slider_max, 'Max Z', z_min, z_max, valinit=initial_max)

        def update(val):
            min_val = self.slider_min.val
            max_val = self.slider_max.val
            self.pcolormesh.set_clim(vmin=min_val, vmax=max_val)
            self.fig.canvas.draw_idle()

        self.slider_min.on_changed(update)
        self.slider_max.on_changed(update)

        if self.plt_interaction:
            plt.show(block=False)
            self.fig.canvas.draw_idle()

    def show_figure_at_position(self, x_posi, y_posi):
        """ポップアップウィンドウの位置を設定"""
        manager = plt.get_current_fig_manager()
        try:
            # tkinter backend を使用している場合
            manager.window.wm_geometry(f"+{x_posi}+{y_posi}")
        except AttributeError:
            # Qt backend を使用している場合
            manager.window.setGeometry(x_posi, y_posi, manager.window.width(), manager.window.height())

    def delete_image(self):
        # pcolormeshの削除
        if self.pcolormesh is not None:
            self.pcolormesh.remove()
            self.pcolormesh = None

        # カラーバーの削除
        if self.colorbar is not None:
            try:
                self.colorbar.remove()
                self.colorbar = None
            except Exception as e:
                pass
                # print(f"Error removing colorbar: {e}")

        # 描画の更新
        if self.fig is not None:
            self.fig.canvas.draw_idle()

    def close_figure(self):
        """現在のインスタンスの図を閉じる"""
        self.delete_image()
        plt.close(self.fig)

    def set_range(self, x_lim_min, x_lim_max, y_lim_min, y_lim_max):
        # 新しいプロットを作成
        self.ax.set_xlim(x_lim_min, x_lim_max)
        self.ax.set_ylim(y_lim_min, y_lim_max)
        # グラフの再描画
        self.fig.canvas.draw_idle() 

    def set_z_range(self, z_lim_min, z_lim_max):
        self.norm = Normalize(vmin=z_lim_min, vmax=z_lim_max)
        if self.pcolormesh:
            self.pcolormesh.set_norm(self.norm)
            if self.colorbar:
                self.colorbar.update_normal(self.pcolormesh)  # カラーバーも更新
                # Y軸を指数表記に設定
                if self.scientific_zscale:
                    self.colorbar.ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
                    self.colorbar.ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
         
            self.fig.canvas.draw_idle()

    def change_colormap(self, colormap):
        self.colormap = colormap
        self.delete_image()  # 画像を削除
        # self.plot_image(self.x, self.y, self.z)
        self.fig.canvas.draw_idle()

    def add_line(self, x, y, linecolor, linewidth):
        """lineを追加する。EDC/YDCの範囲を表示する。"""
        line = self.ax.plot(x, y, color=linecolor, linewidth=linewidth)
        self.lines.append(line[0])  # Line2Dオブジェクトをリストに追加
        self.fig.canvas.draw_idle()
        
    def remove_lines(self):
        """追加したすべての線を削除する。"""
        for line in self.lines:
            line.remove()
        self.lines.clear()  # リストをクリア

    def show_figures(self):
        # plt show()でたまってた分をすべて表示する。
        plt.show()
        # グラフの再描画
        self.fig.canvas.draw_idle()

    def update_canvas(self): # GUI側でこの関数を呼び出してもプロットが更新されない！
        self.fig.tight_layout()
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    # plot出来ない
    # smoothed_image_pltctrl=ImagePlotControl([0, 1], [0, 1], [[1,1], [1,2]], 
    #                                     title="n\nm", 
    #                                     plt_interaction=True, figsize_h=3.5, figsize_w=4,
    #                                     x_label="X", y_label="Y", z_label="Intensity", slider=True)
    pass