import numpy as np
import math
import matplotlib.pyplot as plt
import mpmath as mp
import pandas as pd
import tkinter
import csv
from scipy.optimize import curve_fit
import os
from math import log10, floor
from decimal import Decimal, ROUND_HALF_UP
import customtkinter
import customtkinter as ctk
import tkinter.messagebox as messagebox


def destroy_widget_by_variable(parent, widget):
    """
    特定の変数で定義されたウィジェットを削除する関数

    Args:
        parent: 親ウィジェット（通常はフレームやウィンドウ）
        widget: 削除したいウィジェット（例: hoge）
    """
    # ウィジェットが現在どこに配置されているかの情報を取得
    try:
        grid_info = widget.grid_info()
        # ウィジェットが配置されている場合、そのウィジェットを削除
        widget.destroy()
    except tkinter.TclError:
        print("ウィジェットがグリッド上に存在しません。")


def destroy_widget_by_row(widget, row, upper_row_limit=1000):
    # 配置されたウィジットの情報を取得
        children = widget.winfo_children()
    # row 行目以下にウィジットがあるかどうかをチェック
        for child in children:
            if child.grid_info()['row'] >= row and child.grid_info()['row'] <=upper_row_limit:
                # 5行目以下にウィジットがある場合、削除する
                child.destroy()

def get_input_values_in_widgets(widget):
    # AnaluzerDataFrame内のウィジットをすべて取得
    input_values = []
    
    children = widget.winfo_children()
    
    # for child in children: # デバッグ
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

def get_input_values_in_widgets_by_row_column(widget, target_row, target_column):
    """
    特定の行/列番号にあるウィジェットの値を取得する関数
    """
    value = None
    state = None

    # ウィジェット内の全ての子要素を取得
    children = widget.winfo_children()
    
    for child in children:
        # 各ウィジェットの配置情報を取得
        grid_info = child.grid_info()
        row = grid_info.get('row', -1)  # 'row'が存在しない場合はデフォルト値-1
        column = grid_info.get('column', -1)  # 'column'が存在しない場合はデフォルト値-1

        # デバッグ: 子ウィジェットの行番号を確認
        # print(f"Child: {child}, Row: {row}")
        
        # ターゲットの行番号のウィジェットだけを取得
        if row == target_row and column == target_column:
            if isinstance(child, customtkinter.CTkEntry):
                value = child.get()
            elif isinstance(child, customtkinter.CTkCheckBox):
                state = child.get()

    return value, state
