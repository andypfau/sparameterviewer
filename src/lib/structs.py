from __future__ import annotations

import os
from .si import Si, SiFmt
from .citi import CitiReader
from .utils import AchiveFileLoader, natural_sort_key

import dataclasses
import numpy as np
import skrf
import logging
import pathlib
import datetime
import os
from typing import Callable
from functools import total_ordering



@total_ordering
class PathExt(pathlib.Path):
    """ An extension of Path with has the additional property arch_path, to represent a file inside an archive """

    def __init__(self, path, *, arch_path: str|None = None):
        super().__init__(path)
        self._arch_path = arch_path
    
    def __hash__(self) -> int:
        if self._arch_path:
            return hash(str(super()) + os.sep + self._arch_path)
        return super().__hash__()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, PathExt):
            if self._arch_path != other._arch_path:
                return False
        return super().__eq__(other)

    def __lt__(self, other) -> bool:
        self_path = self.full_path
        if isinstance(other, PathExt):
            other_path = other.full_path
        else:
            other_path = str(super())
        return natural_sort_key(self_path) <= natural_sort_key(other_path)
    
    @property
    def arch_path(self) -> str|None:
        return self._arch_path
    
    @property
    def arch_name(self) -> str:
        if self._arch_path:
            return pathlib.Path(self._arch_path).name
        return None
    
    @property
    def full_name(self) -> str:
        if self._arch_path:
            return super().name + os.sep + pathlib.Path(self._arch_path).name
        return super().name
    
    @property
    def full_path(self) -> str:
        if self._arch_path:
            return str(super().absolute()) + os.sep + self._arch_path
        return str(super().absolute())
    
    @property
    def final_name(self) -> str:
        if self._arch_path:
            return pathlib.Path(self._arch_path).name
        return super().name
    
    def absolute(self) -> PathExt:
        return PathExt(super().absolute(), arch_path=self._arch_path)



class SParamFile:
    """Wrapper for a skrf.Network"""


    before_load: Callable[PathExt,bool] = None
    after_load: Callable[PathExt,None] = None


    def __init__(self, path: str|PathExt, tag: int = None, name: str = None, short_name: str = None):

        self.path: PathExt = path if isinstance(path,PathExt) else PathExt(path)
        self.tag = tag

        self._nw = None
        self._error = None

        if path.arch_path:
            name_prefix = path.arch_name + '/'
        else:
            name_prefix = ''
        self.name = name if name is not None else name_prefix+self.path.name
        self.short_name = short_name if short_name is not None else name_prefix+os.path.splitext(self.path.name)[0]
    

    def __eq__(self, other) -> bool:
        if isinstance(other, SParamFile):
            if self.path != other.path:
                return False
            return True
        return super.__eq__(self, other)
    

    def _load(self):
        if self._nw is not None:
            return

        if SParamFile.before_load:
            if not SParamFile.before_load(self.path):
                self._error = 'aborted by user'
                raise RuntimeError(f'Loading aborted by user')

        def load(path: str):
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.cti', '.citi']:
                    citi = CitiReader(path)
                    nw = citi.get_network(None, {}, select_default=True)
                else:
                    nw = skrf.network.Network(path)
                self._nw = nw
            except Exception as ex:
                logging.exception(f'Unable to load network from "{path}" ({ex})')
                self._error = str(ex)
                self._nw = None
        
        if self.is_from_archive:
            try:
                with AchiveFileLoader(str(self.path), self.path.arch_path) as extracted_path:
                    load(extracted_path)
            except Exception as ex:
                logging.warning(f'Unable to extract and load <{self.path.arch_path}> from archive <{str(self.path)}> ({ex})')
        else:
            load(str(self.path))
        
        if SParamFile.after_load:
            SParamFile.after_load(self.path)

    
    @property
    def is_from_archive(self) -> bool:
        return self.path.arch_path is not None

    
    @property
    def nw(self) -> "skrf.Network":
        self._load()
        return self._nw
    

    @property
    def loaded(self) -> bool:
        return self._nw is not None
    

    @property
    def error(self) -> bool:
        return self._error is not None

    
    def get_plaintext(self) -> str:
        if self.is_from_archive:
            try:
                with AchiveFileLoader(str(self.path), self.path.arch_path) as extracted_path:
                    with open(extracted_path, 'r') as fp:
                        return fp.read()
            except Exception as ex:
                raise RuntimeError(f'Unable to extract and load <{self.path.arch_path}> from archive <{str(self.path)}> ({ex})')
        else:
            with open(self.path, 'r') as fp:
                return fp.read()
    

    def get_info_str(self) -> str:
        if not self.nw:
            if self.error:
                return self.error
            return 'File not loaded'
                
        f0, f1 = self.nw.f[0], self.nw.f[-1]
        n_pts = len(self.nw.f)
        _, fname = os.path.split(str(self.path))
        comm = '' if self.nw.comments is None else self.nw.comments
        n_ports = self.nw.s.shape[1]

        fileinfo = ''
        def fmt_tstamp(ts):
            return f'{datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M:%S}'
        if self.path.arch_path:
            fileinfo += f'Archive path: {os.path.abspath(str(self.path))}\n'
            fileinfo += f'File path in archive: {self.path.arch_path}\n'
            try:
                created = fmt_tstamp(os.path.getctime(str(self.path)))
                fileinfo += f'Archive created: {created}, '
            except:
                fileinfo += f'Archive created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(str(self.path)))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(str(self.path)):,.0f} B'
                fileinfo += f'Archive size: {size}\n'
            except:
                fileinfo += f'Archive size: unknown\n'
        else:
            fileinfo += f'File path: {os.path.abspath(str(self.path))}\n'
            try:
                created = fmt_tstamp(os.path.getctime(str(self.path)))
                fileinfo += f'File created: {created}, '
            except:
                fileinfo += f'File created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(str(self.path)))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(str(self.path)):,.0f} B'
                fileinfo += f'File size: {size}\n'
            except:
                fileinfo += f'File size: unknown\n'
        
        if (self.nw.z0 == self.nw.z0[0,0]).all():
            z0 = str(Si(self.nw.z0[0,0],'Ohm'))
        else:
            z0 = 'different for each port and/or frequency'
        
        info = f'{fname}\n'
        info += '-'*len(fname)+'\n\n'
        
        if len(comm)>0:
            for comm_line in comm.splitlines():
                info += comm_line.strip() + '\n'
            info += '\n'
        info += f'Ports: {n_ports}, reference impedance: {z0}\n'

        n_points_str = f'{n_pts:,.0f} point{"s" if n_pts!=0 else ""}'
        
        freq_steps = np.diff(self.nw.f)
        freq_equidistant = np.allclose(freq_steps,freq_steps[0])
        if freq_equidistant:
            freq_step = freq_steps[0]
            spacing_str =  f'{Si(freq_step,"Hz")} equidistant spacing'
        else:
            freq_arbitrary = True
            if np.all(self.nw.f != 0):
                freq_ratios = np.exp(np.diff(np.log(self.nw.f)))
                if np.allclose(freq_ratios,freq_ratios[0]):
                    freq_arbitrary = False
                    freq_step = np.mean(freq_steps)
                    freq_ratio = freq_ratios[0]
                    spacing_str = f'{freq_ratio:.4g}x logarithmic spacing, average spacing {Si(freq_step,"Hz")}'
            if freq_arbitrary:
                freq_step = np.mean(freq_steps)
                spacing_str =  f'non-equidistant spacing, average spacing {Si(freq_step,"Hz")}'
        
        info += f'Frequency range: {Si(f0,"Hz")} to {Si(f1,"Hz")}, {n_points_str}, {spacing_str}'
        info += '\n\n'

        info += fileinfo

        return info




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
    color: str
