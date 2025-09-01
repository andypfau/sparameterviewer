from __future__ import annotations

import os
from .path_ext import PathExt
from .si import SiValue
from .citi import CitiReader
from .utils import ArchiveFileLoader

import numpy as np
import skrf
import logging
import datetime
import os
import tempfile
from typing import Callable



class SParamFile:
    """Wrapper for a skrf.Network"""


    before_load: Callable[[PathExt],bool] = None
    after_load: Callable[[PathExt],None] = None


    def __init__(self, path: str|PathExt, tag: int = None, name: str = None, short_name: str = None):

        self.path: PathExt = path if isinstance(path,PathExt) else PathExt(path)
        self.tag = tag

        self._nw = None
        self._error = None

        if path.arch_path:
            name_prefix = path.arch_path_name + '/'
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
                    try:
                        nw = skrf.network.Network(path)
                    except ValueError:
                        # I found this bizarre file in my collection where each line is preceeded with a space... attempt to fix that...
                        fixed = False
                        with open(path, 'r') as fp:
                            lines = fp.readlines()
                        for i,line in enumerate(lines):
                            if line.startswith(' '):
                                if '#' in line or '!' in line:
                                    lines[i] = line.strip()
                                    fixed = True
                        if not fixed:
                            raise
                        with tempfile.TemporaryDirectory() as temp_dir:
                            name = os.path.split(path)[1]
                            temp_path = os.path.join(temp_dir, name)
                            with open(temp_path, 'w') as fp:
                                fp.writelines(lines)
                            nw = skrf.network.Network(temp_path)

                    # I think there is a bug in skrf; I only get the 1st comment line
                    # As a workaround, read the comments manually
                    comments_lines = []
                    with open(path, 'r') as fp:
                        for line in fp.readlines():
                            if line.startswith('!'):
                                comments_lines.append(line[1:].strip())
                    if len(comments_lines) > 0:
                        nw.comments = '\n'.join(comments_lines)
                
                assert nw.number_of_ports >= 1, f'Expected at least one port, got {nw.number_of_ports} ports ({path})'
                assert len(nw.f) >= 1, f'Expected at least one frequency point, got {len(nw.f)} points ({path})'
                assert len(nw.s.shape) == 3, f'Expected 3-dimensional S-matrix (nxn over frequeny), got shape {len(nw.s.shape)} ({path})'
                assert nw.s.shape[0] >= 1, f'Expected frequency dimension of S-matrix to be at least one, got {nw.s.shape[0]} ({path})'
                assert nw.s.shape[1] >= 1, f'Expected egress port dimension of S-matrix to be at least one, got {nw.s.shape[1]} ({path})'
                assert nw.s.shape[2] >= 1, f'Expected ingress port dimension of S-matrix to be at least one, got {nw.s.shape[2]} ({path})'
                    
                self._nw = nw
            except Exception as ex:
                logging.exception(f'Unable to load network from "{path}" ({ex})')
                self._error = str(ex)
                self._nw = None
        
        if self.path.is_in_arch():
            from .utils import ArchiveFileLoader
            try:
                with ArchiveFileLoader(str(self.path), self.path.arch_path) as extracted_path:
                    load(extracted_path)
            except Exception as ex:
                logging.warning(f'Unable to extract and load <{self.path.arch_path}> from archive <{str(self.path)}> ({ex})')
        else:
            load(str(self.path))
        
        if SParamFile.after_load:
            SParamFile.after_load(self.path)

    
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
    

    @property
    def error_message(self) -> str|None:
        return self._error if self._error else None

    
    def get_plaintext(self) -> str:
        if self.path.is_in_arch():
            try:
                with ArchiveFileLoader(str(self.path), self.path.arch_path) as extracted_path:
                    with open(extracted_path, 'r') as fp:
                        return fp.read()
            except Exception as ex:
                raise RuntimeError(f'Unable to extract and load <{self.path.arch_path}> from archive <{str(self.path)}> ({ex})')
        else:
            with open(self.path, 'r') as fp:
                return fp.read()
    

    def get_info_str(self) -> str:

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
        
        _, fname = os.path.split(str(self.path))
        info = f'{fname}\n'
        info += '-'*len(fname)+'\n\n'
        
        if not self.nw:
            if self.error:
                info += 'File loading failed: ' + self.error_message
            else:
                info += 'File not loaded'
            info += '\n\n'
            info += fileinfo
            return info
                
        f0, f1 = self.nw.f[0], self.nw.f[-1]
        n_pts = len(self.nw.f)
        comm = '' if self.nw.comments is None else self.nw.comments
        n_ports = self.nw.s.shape[1]
        
        if (self.nw.z0 == self.nw.z0[0,0]).all():
            z0 = str(SiValue(self.nw.z0[0,0],'Ohm'))
        else:
            z0 = 'different for each port and/or frequency'
        
        if len(comm)>0:
            for comm_line in comm.splitlines():
                info += comm_line.strip() + '\n'
            info += '\n'
        info += f'Ports: {n_ports}, reference impedance: {z0}\n'

        n_points_str = f'{n_pts:,.0f} point{"s" if n_pts!=1 else ""}'
        
        if len(self.nw.f) > 1:
            freq_steps = np.diff(self.nw.f)
            freq_equidistant = np.allclose(freq_steps,freq_steps[0])
            if freq_equidistant:
                freq_step = freq_steps[0]
                spacing_str =  f'{SiValue(freq_step,"Hz")} equidistant spacing'
            else:
                freq_arbitrary = True
                if np.all(self.nw.f != 0):
                    freq_ratios = np.exp(np.diff(np.log(self.nw.f)))
                    if np.allclose(freq_ratios,freq_ratios[0]):
                        freq_arbitrary = False
                        freq_step = np.mean(freq_steps)
                        freq_ratio = freq_ratios[0]
                        spacing_str = f'{freq_ratio:.4g}x logarithmic spacing, average spacing {SiValue(freq_step,"Hz")}'
                if freq_arbitrary:
                    freq_step = np.mean(freq_steps)
                    spacing_str =  f'non-equidistant spacing, average spacing {SiValue(freq_step,"Hz")}'
        else:
            spacing_str =  f'single frequeny {SiValue(self.nw.f[0],"Hz")}'
        
        info += f'Frequency range: {SiValue(f0,"Hz")} to {SiValue(f1,"Hz")}, {n_points_str}, {spacing_str}'
        
        info += '\n\n'
        info += fileinfo

        return info
