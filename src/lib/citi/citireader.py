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
        try:
            self._citi = read_citifile(self.filename)
        except Exception as ex:
            # when reading a zero-byte file, the error is just "invalid agrument"; raise a more meaningful message instead
            raise RuntimeError(f'Unable to open file <{filename}> ({ex})')
        self.comments = self._get_comments()

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

    def _get_comments(self) -> list[str]:
        try:
            comments = []
            with open(self.filename, 'r') as fp:
                for line in fp.readlines():
                    if line.startswith('!') or line.startswith('#'):
                        comments.append(line[1:].strip())
            return comments
        except Exception as ex:
            logging.error(f'Unable to read comments form {self.filename} ({ex})')
            return []

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

        def parse_sparam_name(name):
            if (m := re.match(r'S?([0-9,; ]+)', data_name, re.IGNORECASE)):
                params = m.group(1)
            elif (m := re.match(r'S\(([0-9,; ]+)\)', data_name, re.IGNORECASE)):
                params = m.group(1)
            elif (m := re.match(r'S\[([0-9,; ]+)\]', data_name, re.IGNORECASE)):
                params = m.group(1)
            elif (m := re.match(r'S\{([0-9,; ]+)\}', data_name, re.IGNORECASE)):
                params = m.group(1)
            else:
                return None, None

            if (m := re.match(r'([0-9]+)[,; ]([0-9]+)', params, re.IGNORECASE)):
                return int(m.group(1)), int(m.group(2))
            elif (m := re.match(r'([0-9])([0-9])', params, re.IGNORECASE)):
                return int(m.group(1)), int(m.group(2))
            elif (m := re.match(r'([0-9][0-9][0-9])([0-9][0-9][0-9])', params, re.IGNORECASE)):
                return int(m.group(1)), int(m.group(2))
            else:
                return None, None

        variables_used = []
        for data_name in self.datas:

            egress_port, ingress_port = parse_sparam_name(data_name)
            if egress_port is None or ingress_port is None:
                continue
            variables_used.append(data_name)
            
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

        s_matrix = np.full([len(f),highest_port,highest_port], np.nan, dtype=complex)
        for (ep,ip),s in s_dict.items():
            s_matrix[:,ep-1,ip-1] = s
        
        name = os.path.splitext(os.path.split(self.filename)[1])[0]
        for k,v in at_coords.items():
            name += f', {k}={v}'
        
        comments = []
        
        citi_comment = self._citi.attrs.get('comments', '')
        if citi_comment:
            comments.extend([comment for comment in str(citi_comment).splitlines() if comment])
        
        comments.extend(self.comments)
        
        comments.append('CITI coordinates:')
        for cname in self._citi.coords:
            cdata = self._citi.coords[cname].data
            usage_str = 'used as frequency coordinate' if frequency_coord==cname else 'ignored'
            coord_sel_str = ''
            if cname in at_coords:
                coord_sel_str = f', using coordinate value {at_coords[cname]} (data: {cdata})'
            comments.append(f'- {cname}: {len(cdata)} × {cdata.dtype}, {usage_str}{coord_sel_str}')
        
        comments.append('CITI data variables:')
        for vname in self._citi.data_vars:
            vdata = self._citi.data_vars[vname]
            usage_str = 'used as S-parameter' if vname in variables_used else 'ignored'
            comments.append(f'- {vname}: {len(vdata)} × {vdata.dtype}, {usage_str}')
        
        comment = '\n'.join([comment for comment in comments if comment])

        nw = skrf.Network(f=f, f_unit='Hz', name=name, s=s_matrix, comments=comment)
        return nw
