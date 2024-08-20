from CITIfile import read_citifile

import numpy as np
import skrf
import re
import os
import logging
import difflib



class CitiReader:

    def __init__(self, filename: str):
        self.filename = filename
        self._citi = read_citifile(self.filename)

    @property
    def datas(self) -> list[str]:
        return [name for name in self._citi.data_vars]

    @property
    def coords(self) -> dict[str,list[any]]:
        return {name: self._citi.coords[name] for name in self._citi.coords}

    @property
    def coord_names(self) -> list[str]:
        return 

    def guess_frequency_coord_name(self) -> str:
        coord_names = [name for name in self._citi.coords]
        coord_names_lower = [name.lower() for name in coord_names]
        candidates = ['frequency', 'freq', 'f']
        for candidate in candidates:
            matches = difflib.get_close_matches(candidate, coord_names_lower, n=1)
            if len(matches) >= 1:
                match = matches[0]
                for coord_name in coord_names:
                    if match == coord_name.lower():
                        return coord_name
        raise RuntimeError(f'Unable to guess the frequency coordinate of CITI files (names are {self.coord_names})')

    def get_network(self, frequency_coord: "str|None", at_coords: dict[str,any], select_default: bool = False) -> "skrf.Network":

        if frequency_coord is None:
            frequency_coord = self.guess_frequency_coord_name()
        
        for given_coord_name in at_coords.keys():
            if given_coord_name == frequency_coord:
                raise RuntimeError(f'The name of the frequency coordinate ("{frequency_coord}") of CITI file must be available as an independent variable')
            if given_coord_name not in self.coords.keys():
                raise RuntimeError()
        for required_coord_name in self.coords.keys():
            if required_coord_name == frequency_coord:
                continue
            if required_coord_name not in at_coords.keys():
                if select_default:
                    value = np.array(self.coords[required_coord_name])[0]
                    logging.warning(f'Using the default value {value} for coordinate "{required_coord_name}" to read CITI file, because no explicit value was provided')
                    at_coords[required_coord_name] = value
                else:
                    raise RuntimeError(f'No value given for the CITI coordinate "{required_coord_name}"')

        f = None
        s_dict = {}
        highest_port = 0
        for data_name in self.datas:

            m = re.match(r'S[\(\[]([0-9]+),([0-9]+)[\]\)]', data_name)
            if not m:
                continue
            egress_port = int(m.group(1))
            ingress_port = int(m.group(2))
            dict_key = (egress_port,ingress_port)
            highest_port = max(highest_port, max(egress_port, ingress_port))

            data = self._citi.data_vars[data_name].sel(**at_coords)
            s_dict[dict_key] = np.array(data)
        
            if len(data.indexes.variables) != 1:
                raise RuntimeError(f'Expected CITI data variable to have exactly one index, but got {len(data.indexes)}; please make sure you provide the appropriate amount of coordinates')
            for key in data.indexes.variables.keys():
                f = np.array(self._citi.coords[key])
                break
        
        if f is None:
            raise RuntimeError(f'CITI file contains not usable data')
        if highest_port < 1:
            raise RuntimeError(f'Highest port number in CITI file is {highest_port}, expected 1 or more')

        s_matrix = np.zeros([len(f),highest_port,highest_port], dtype=complex)
        for (ep,ip),s in s_dict.items():
            s_matrix[:,ep-1,ip-1] = s
        
        name = os.path.splitext(os.path.split(self.filename)[1])[0]
        for k,v in at_coords.items():
            name += f', {k}={v}'
        
        comment = self._citi.attrs.get('comments', '')
        
        comment += '\nCITI coordinates:'
        for cname in self._citi.coords:
            cdata = self._citi.coords[cname].data
            csel = ''
            if cname in at_coords:
                csel = f', using coordinate value {at_coords[cname]}'
            comment += f'\n- {cname}: {len(cname)} ({cdata}, {cdata.dtype}{csel})'
        
        comment += '\nCITI data variables:'
        for vname in self._citi.data_vars:
            vdata = self._citi.data_vars[vname]
            comment += f'\n- {vname}: {vdata.dtype}'

        nw = skrf.Network(f=f, f_unit='Hz', name=name, s=s_matrix, comments=comment)
        return nw
