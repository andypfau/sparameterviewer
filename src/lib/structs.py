from .touchstone import Touchstone
from .si import Si, SiFmt

from dataclasses import dataclass
import numpy as np


@dataclass
class LoadedSParamFile:
    id: str
    filename: str
    sparam: Touchstone


@dataclass
class PlotDataQuantity:
    name: str
    format: SiFmt
    values: np.ndarray


@dataclass
class PlotData:
    name: str
    x: PlotDataQuantity
    y: PlotDataQuantity
    style: str
    color: object
