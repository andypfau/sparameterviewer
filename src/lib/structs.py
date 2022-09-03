import os
from .si import Si, SiFmt

import dataclasses
import numpy as np
import skrf



@dataclasses.dataclass
class SParamFile:
    """Wrapper for a skrf.Network"""

    file_path: str
    filename: str = dataclasses.field(init=False)
    nw: skrf.Network
    tag: any = None
    name: str = None
    short_name: str = None

    def __post_init__(self):
        self.filename = os.path.split(self.file_path)[1]
        if self.name is None:
            self.name = self.filename
        if self.short_name is None:
            self.short_name = os.path.splitext(self.filename)[0]

    @staticmethod
    def load(file_path: str, tag: any = None) -> "SParamFile":
        nw = skrf.Network(file_path)
        nw.name = os.path.split(file_path)[1]
        return SParamFile(file_path, nw, tag)



@dataclasses.dataclass
class PlotDataQuantity:
    name: str
    format: SiFmt
    values: np.ndarray



@dataclasses.dataclass
class PlotData:
    name: str
    x: PlotDataQuantity
    y: PlotDataQuantity
    style: str
    color: object
