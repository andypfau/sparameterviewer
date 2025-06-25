from .si import SiFormat

import dataclasses
import numpy as np



@dataclasses.dataclass
class PlotDataQuantity:
    name: str
    format: SiFormat
    values: np.ndarray



@dataclasses.dataclass
class PlotData:
    name: str
    x: PlotDataQuantity
    y: PlotDataQuantity
    z: PlotDataQuantity|None
    color: str
