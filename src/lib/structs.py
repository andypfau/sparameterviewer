import os
from .si import Si, SiFmt
from .citi import CitiReader

import dataclasses
import numpy as np
import skrf
import logging
import zipfile
import tempfile
import datetime
import os
from typing import Callable



class SParamFile:
    """Wrapper for a skrf.Network"""


    before_load: Callable[None,bool] = None


    def __init__(self, file_path: str, archive_path: str = None, tag: int = None, name: str = None, short_name: str = None):

        self._file_path = os.path.abspath(file_path)
        self._archive_path = os.path.abspath(archive_path) if archive_path else None
        self.tag = tag

        self._nw = None
        self._error = None

        if archive_path is not None:
            name_prefix = os.path.split(archive_path)[1] + '/'
        else:
            name_prefix = ''
        self.name = name if name is not None else name_prefix+self.filename
        self.short_name = short_name if short_name is not None else name_prefix+os.path.splitext(self.filename)[0]
    

    def __eq__(self, other) -> bool:
        if isinstance(other, SParamFile):
            if self.file_path != other.file_path:
                return False
            if self.archive_path:
                if self.archive_path != other.archive_path:
                    return False
            return True
        return super.__eq__(self, other)
    

    def _load(self):
        if self._nw is not None:
            return

        try:
            if SParamFile.before_load:
                if not SParamFile.before_load():
                    return
        except:
            pass

        def load(path):
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
    def is_from_archive(self) -> bool:
        return self.archive_path is not None

    
    @property
    def nw(self) -> "skrf.Network":
        self._load()
        return self._nw


    @property
    def file_path(self) -> str:
        return self._file_path


    @property
    def filename(self) -> str:
        return os.path.split(self._file_path)[1]


    @property
    def archive_path(self) -> str:
        return self._archive_path
    

    @property
    def loaded(self) -> bool:
        return self._nw is not None
    

    @property
    def error(self) -> bool:
        return self._error is not None

    
    def get_plaintext(self) -> str:
        def load(path):
            try:
                with open(path, 'r') as fp:
                    return fp.read()
            except Exception as ex:
                logging.exception(f'Unable to read plaintext from "{path}" ({ex})')
        
        if self.is_from_archive:
            with tempfile.TemporaryDirectory() as tempdir:
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    try:
                        zipped_filename = zf.extract(self.file_path, tempdir)
                        plaintext = load(zipped_filename)
                        os.remove(zipped_filename)
                        return plaintext
                    except Exception as ex:
                        logging.warning(f'Unable to extract "{self.file_path}" from "{self.archive_path}" ({ex})')
                        return f'[Error: unable to extract "{self.file_path}" from "{self.archive_path}"]'
        else:
            return load(self.file_path)
    

    def get_info_str(self) -> str:
                
        f0, f1 = self.nw.f[0], self.nw.f[-1]
        n_pts = len(self.nw.f)
        _, fname = os.path.split(self.file_path)
        comm = '' if self.nw.comments is None else self.nw.comments
        n_ports = self.nw.s.shape[1]

        fileinfo = ''
        def fmt_tstamp(ts):
            return f'{datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M:%S}'
        if self.archive_path is not None:
            fileinfo += f'Archive path: {os.path.abspath(self.archive_path)}\n'
            try:
                created = fmt_tstamp(os.path.getctime(self.archive_path))
                fileinfo += f'Archive created: {created}, '
            except:
                fileinfo += f'Archive created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(self.archive_path))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(self.archive_path):,.0f} B'
                fileinfo += f'Archive size: {size}\n'
            except:
                fileinfo += f'Archive size: unknown\n'
            fileinfo += f'File path in archive: {self.file_path}\n'
        else:
            fileinfo += f'File path: {os.path.abspath(self.file_path)}\n'
            try:
                created = fmt_tstamp(os.path.getctime(self.file_path))
                fileinfo += f'File created: {created}, '
            except:
                fileinfo += f'File created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(self.file_path))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(self.file_path):,.0f} B'
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
