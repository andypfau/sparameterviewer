import os
from .si import Si, SiFmt
from .citi import CitiReader

import dataclasses
import numpy as np
import skrf
import logging
import zipfile
import tempfile



class SParamFile:
    """Wrapper for a skrf.Network"""


    def __init__(self, file_path: str, archive_path: str = None, tag: int = None, name: str = None, short_name: str = None):

        self.file_path = file_path
        self.archive_path = archive_path
        self.filename = os.path.split(self.file_path)[1]
        self.tag = tag

        self._nw = None
        self._error = None

        if archive_path is not None:
            name_prefix = os.path.split(archive_path)[1] + '/'
        else:
            name_prefix = ''
        self.name = name if name is not None else name_prefix+self.filename
        self.short_name = short_name if short_name is not None else name_prefix+os.path.splitext(self.filename)[0]
    

    def _load(self):
        if self._nw is not None:
            return

        def load(path):
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext == '.cti':
                    citi = CitiReader(path)
                    nw = citi.get_network(None, {}, select_default=True)
                else:
                    nw = skrf.network.Network(path)
                self._nw = nw
            except Exception as ex:
                logging.exception(f'Unable to load network from "{path}" ({ex})')
                self._error = str(ex)
                self._nw = None
        
        if self.archive_path is not None:
            with tempfile.TemporaryDirectory() as tempdir:
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    try:
                        zipped_filename = zf.extract(self.file_path, tempdir)
                        load(zipped_filename)
                        os.remove(zipped_filename)
                    except Exception as ex:
                        logging.warning(f'Unable to extract "{self.file_path}" from "{self.archive_path}" ({ex})')
        else:
            load(self.file_path)

    @property
    def nw(self) -> "skrf.Network":
        self._load()
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
    z: "PlotDataQuantity|None"
