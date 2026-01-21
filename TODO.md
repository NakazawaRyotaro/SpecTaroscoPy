# ToDoList
- MBS_A1 classで初期化するインスタンス変数がおおい。

dataclassを使用し、インスタンス変数を減らす。

```chatGPT
from dataclasses import dataclass, field
from typing import Optional, List
import numpy as np

@dataclass
class Metadata:
    hn: Optional[float] = None
    Vsample: float = 0.0
    x_EF: Optional[float] = None
    SECO: Optional[float] = None
    WF: Optional[float] = None
    user: Optional[str] = None
    version: Optional[str] = None

@dataclass
class Axes:
    x: Optional[np.ndarray] = None
    y: Optional[np.ndarray] = None
    x_offset: float = 0.0
    y_offset: float = 0.0
    x_label: str = "X"
    y_label: str = "Y"

@dataclass
class Data:
    z: Optional[np.ndarray] = None
    z_paths: List[np.ndarray] = field(default_factory=list)

class MBS_A1:
    def __init__(...):
		
		# self.* = None or [] をなくす！！！

        self.data = ImageData()      # x, y, z
        self.meta = Metadata()       # hn, Vsample, ...
        self.proc = Processing()     # smooth条件など
        self.results = Results()     # EDC, YDC, peak など
```
MBS_A1での解析時は
```
def generate_an_edc(self):
    # 計算
    x_edc, y_edc = ...
    
    # 中身を更新するだけ
    self.results.edc_x = x_edc
    self.results.edc_y = y_edc
```
で更新していく。
