import os
from .si import Si, SiFmt

import dataclasses
import numpy as np
import skrf
import logging



class SParamFile:
    """Wrapper for a skrf.Network"""


    def __init__(self, file_path: str, tag: int = None, name: str = None, short_name: str = None):

        self.file_path = file_path
        self.filename = os.path.split(self.file_path)[1]
        self.tag = tag

        self._nw = None
        self._error = None

        self.name = name if name is not None else self.filename
        self.short_name = short_name if short_name is not None else os.path.splitext(self.filename)[0]
    

    @property
    def nw(self):
        if not self._nw:
            try:
                logging.debug(f'Loading network "{self.file_path}"')
                self._nw = skrf.network.Network(self.file_path)
            except Exception as ex:
                logging.exception(f'Unable to load network from "{self.file_path}" ({ex})')
                self._error = str(ex)
                self._nw = None
        return self._nw
    

    def loaded(self) -> bool:
        return self._nw is not None
    

    def error(self) -> bool:
        return self._error is not None



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
    z: PlotDataQuantity
    style: str
    color: object
