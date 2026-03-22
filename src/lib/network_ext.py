from __future__ import annotations
import skrf
import enum
import re
import warnings
import numpy as np
import itertools
from typing import Iterable



def flat_zip(a: Iterable, b: Iterable) -> Iterable:
    """ returns [a[0], b[0], a[1], b[1], ...]"""
    return itertools.chain(*zip(a,b))


def match_any(regexes: list[str], s: str, *args, **kwargs) -> re.Match:
    for regex in regexes:
        m = re.match(regex, s, *args, **kwargs)
        if m:
            return m
    return None




class NetworkExtPortMode(enum.StrEnum):
    se = 'S'
    pos = 'P'
    neg = 'N'
    df = 'D'
    cm = 'C'



class NetworkExtPort:
    
    def __init__(self, mode: NetworkExtPortMode, number: int, index: int|None=None):
        self._number, self._mode, self._index = number, mode, index
    

    @property
    def number(self) -> int: return self._number

    @property
    def mode(self) -> NetworkExtPortMode: return self._mode

    @property
    def index(self) -> int: return self._index


    def __repr__(self) -> str:
        return f'NetworkExtPort<{self._mode},{self._number},{self._index}>'
    

    def __str__(self) -> str:
        return f'{self._mode}{self._number}'
    

    @staticmethod
    def parse(s: str, index: int|None = None) -> NetworkExtPort:
        m = re.match(r'([PNDC])?(\d+)', s.upper(), re.I)
        if not m:
            raise ValueError(f'Cannot parse "{s}')
        match m.group(1):
            case None: mode = NetworkExtPortMode.se
            case 'P': mode = NetworkExtPortMode.pos
            case 'N': mode = NetworkExtPortMode.neg
            case 'D': mode = NetworkExtPortMode.df
            case 'C': mode = NetworkExtPortMode.cm
        number = int(m.group(2))
        return NetworkExtPort(mode, number, index)



class NetworkExt(skrf.Network):


    def __init__(self, file=None, name=None, params=None, comments=None, f_unit=None, s_def=None, **kwargs):
        super().__init__(file=file,name=name, params=params, comments=comments,f_unit=f_unit, s_def=s_def, **kwargs)
        self._ports: list[NetworkExtPort] = []


    def copy(self) -> NetworkExt:
        result = NetworkExt(s=self.s, f=self.f, f_unit='Hz', z0=self.z0, comments=self.comments, name=self.name)
        result._ports = list(self.ports)
        return result
    
    @property
    def z0_simple(self) -> np.ndarray:
        z0 = super().z0
        assert z0.ndim == 2
        return z0[0,:]
    

    def _ensure_ports(self):
        
        if len(self._ports) == 0:
            ports = []
            
            def get_next_se_port_number():
                all_numbers = set([port._number for port in ports])
                number = 1
                while number in all_numbers:
                    number += 1
                return number
            
            def get_next_df_port_number():
                se_numbers = set([port._number for port in ports if port._mode == NetworkExtPortMode.se])
                df_numbers = set([port._number for port in ports if port._mode == NetworkExtPortMode.df])
                cm_numbers = set([port._number for port in ports if port._mode == NetworkExtPortMode.cm])
                matched_port_numbers = df_numbers & cm_numbers
                unmatched_df_numbers = df_numbers - cm_numbers
                number = 1
                while (number in se_numbers) or (number in matched_port_numbers) or (number in unmatched_df_numbers):
                    number += 1
                return number
            
            def get_next_cm_port_number():
                se_numbers = set([port._number for port in ports if port._mode == NetworkExtPortMode.se])
                df_numbers = set([port._number for port in ports if port._mode == NetworkExtPortMode.df])
                cm_numbers = set([port._number for port in ports if port._mode == NetworkExtPortMode.cm])
                matched_port_numbers = df_numbers & cm_numbers
                unmatched_cm_numbers = cm_numbers - df_numbers
                number = 1
                while (number in se_numbers) or (number in matched_port_numbers) or (number in unmatched_cm_numbers):
                    number += 1
                return number
            
            for i in range(self.number_of_ports):
                if self.port_modes[i] == 'S':
                    ports.append(NetworkExtPort(NetworkExtPortMode.se, get_next_se_port_number(), i))
                elif self.port_modes[i] == 'D':
                    ports.append(NetworkExtPort(NetworkExtPortMode.df, get_next_df_port_number(), i))
                elif self.port_modes[i] == 'C':
                    ports.append(NetworkExtPort(NetworkExtPortMode.cm, get_next_cm_port_number(), i))
                else:
                    raise RuntimeError(f'Got unexpected port mode "{self.port_modes[i]}')
            
            self._ports = ports
        self._verify_ports(self._ports)
        

    def _verify_ports(self, ports: Iterable[NetworkExtPort]):
        se_ports = [port for port in ports if port.mode==NetworkExtPortMode.se]
        diff_ports = [port for port in ports if port.mode!=NetworkExtPortMode.se]
        diff_port_pairs: dict[int,list[int]] = {}
        expected_n_se_ports = len(se_ports)
        expected_n_diff_ports = len(diff_ports) // 2
        n_ports = expected_n_se_ports + expected_n_diff_ports
        diff_ports_are_mixed = None
        numbers, indices = set(), set()
        for port in ports:
            if port._index < 0 or port._index >= self.number_of_ports:
                raise ValueError(f'Port index {port._index} out of range 0...{self.number_of_ports-1}')
            if port._number < 1 or port._number > n_ports:
                raise ValueError(f'Port number {port._number} out of range 1...{n_ports}')
            if port._index in indices:
                raise ValueError(f'Duplicate index {port._index}')
            if port._mode != NetworkExtPortMode.se:
                diff_port_pairs_indices = diff_port_pairs.get(port._number, [])
                diff_port_pairs_indices.append(port._index)
                diff_port_pairs[port._number] = diff_port_pairs_indices
                if port._mode in [NetworkExtPortMode.df, NetworkExtPortMode.cm]:
                    if diff_ports_are_mixed is None:
                        diff_ports_are_mixed = True
                    elif not diff_ports_are_mixed:
                        raise ValueError(f'Got a mix of CM/DF and Pos/Neg')
                elif port._mode in [NetworkExtPortMode.pos, NetworkExtPortMode.neg]:
                    if diff_ports_are_mixed is None:
                        diff_ports_are_mixed = False
                    elif diff_ports_are_mixed:
                        raise ValueError(f'Got a mix of CM/DF and Pos/Neg')
            numbers.add(port._number)
            indices.add(port._index)
        if len(numbers) != n_ports:
            raise ValueError(f'Got {len(numbers)} port(s), expected {n_ports}')
        if len(indices) != self.number_of_ports:
            raise ValueError(f'Got {len(indices)} port(s), expected {self.number_of_ports}')
        if len(diff_port_pairs) != expected_n_diff_ports:
            raise ValueError(f'Expected there to be {expected_n_diff_ports} differential tuples, got {len(diff_port_pairs)}')
        if not all([len(indices)==2 for indices in diff_port_pairs.values()]):
            raise ValueError(f'Expected differential indices to be 2-tuples, got {diff_port_pairs}')
    

    @property
    def ports(self) -> list[NetworkExtPort]:
        self._ensure_ports()
        return list(self._ports)
    @ports.setter
    def ports(self, value: Iterable[NetworkExtPort]|Iterable[str]):
        def parse_port(p,i):
            if isinstance(p, str):
                return NetworkExtPort.parse(p,i)
            if isinstance(p, NetworkExtPort):
                return p
            raise ValueError()
        parsed_ports = [parse_port(port,index) for index,port in enumerate(value)]
        
        self._verify_ports(parsed_ports)

        self._ports = [*parsed_ports]

        port_modes_str = ''
        for index in range(self.number_of_ports):
            for port in self._ports:
                if port._index == index:
                    match port._mode:
                        case NetworkExtPortMode.se:
                            port_modes_str += 'S'
                        case NetworkExtPortMode.pos:
                            port_modes_str += 'S'
                        case NetworkExtPortMode.neg:
                            port_modes_str += 'S'
                        case NetworkExtPortMode.df:
                            port_modes_str += 'D'
                        case NetworkExtPortMode.cm:
                            port_modes_str += 'C'
                        case _:
                            raise ValueError()
                    break
        self.port_modes = np.array(port_modes_str)
    

    @property
    def is_singleended(self) -> bool:
        return not any([p._mode in [NetworkExtPortMode.cm, NetworkExtPortMode.df] for p in self.ports])
    

    @property
    def has_posneg_pairs(self) -> bool:
        return any([p._mode in [NetworkExtPortMode.pos, NetworkExtPortMode.neg] for p in self.ports])


    @property
    def is_mixed(self) -> bool:
        any_df_or_cm = any([p._mode in [NetworkExtPortMode.cm, NetworkExtPortMode.df] for p in self.ports])
        any_pos_or_neg = any([p._mode in [NetworkExtPortMode.pos, NetworkExtPortMode.neg] for p in self.ports])
        return any_df_or_cm and not any_pos_or_neg


    def get_indices(self, index: str|int|tuple[int,int], prefix: str = '') -> tuple[int,int]:
        
        def decode_single_integer(index: int) -> tuple[int,int]:
            # treat as plain indices
            if index >= 11 and index <= 99:
                ep, ip = index // 10, index % 10
            elif index >= 1010 and index <= 9999:
                ep, ip = index // 100, index % 100
            else:
                raise ValueError(f'Index {index} out of range')
            return ep-1, ip-1

        def decode_str(index: str) -> tuple[int,int]:
            
            # try to parse as plain indices
            m = match_any([r'(\d)(\d)', r'(\d\d)(\d\d)', r'(\d+)[,;](\d+)'], index)
            if m:
                ep, ip = m.group(1)-1, m.group(2)-1
                return ep, ip
            
            # parse as proper S-parameter name
            self._ensure_ports()
            m = match_any([prefix+r'([DC]{0,2})(\d)(\d)', prefix+r'([DC]{0,2})(\d\d)(\d\d)', prefix+r'([DC]{0,2})(\d+)[,;](\d+)'], index.upper())
            if not m:
                raise ValueError(f'Cannot parse "{index}"')
            modes, num1, num2 = m.group(1) or '', int(m.group(2)), int(m.group(3))
            indices: list[int] = []
            for num in [num1, num2]:
                for port in self._ports:
                    if port._number == num:
                        if port._mode == NetworkExtPortMode.se:
                            indices.append(port._index)
                            break
                        else:
                            if len(modes) < 1:
                                raise ValueError(f'Mode for port {port._number} missing (ports <{self._ports}>)')
                            if str(port._mode) == modes[0]:
                                modes = modes[1:]
                                indices.append(port._index)
                                break
            if len(modes) > 0:
                raise ValueError(f'Too many modes (given "{index}" for ports <{self._ports}>)')
            if len(indices) != 2:
                raise ValueError(f'Not enough valid indices (given "{index}" for ports <{self._ports}>)')
            return indices[0], indices[1]
        
        if isinstance(index, int):
            return decode_single_integer(index)
        elif isinstance(index, tuple):
            return index
        elif isinstance(index, str):
            return decode_str(index)
        
        raise ValueError(f'Unexpected index: <{index}> (ports <{self._ports}>)')
    
    
    def sij(self, key: str|int|tuple[int,int]) -> np.ndarray:
        ep, ip = self.get_indices(key)
        return super().s[:,ep,ip]


    def indices_to_str(self, egress_index: int, ingress_index: int, prefix: str = 'S') -> str:
        self._ensure_ports()
        def get_mode_and_port(index):
            for port in self._ports:
                if port._index == index:
                    if port._mode == NetworkExtPortMode.se:
                        mode = ''
                    else:
                        mode = str(port._mode)
                    return mode, port._number
            raise ValueError(f'Index {index} not found')
        mode1, port1 = get_mode_and_port(egress_index)
        mode2, port2 = get_mode_and_port(ingress_index)
        separator = ',' if port1>=10 or port2>=10 else ''
        return f'{prefix}{mode1}{mode2}{port1}{separator}{port2}'


    def to_singleended(self) -> NetworkExt:
        self._verify_ports(self._ports)
        if not self.is_mixed:
            raise RuntimeError(f'Cannot convert network to single-ended')
        
        se_ports = [p for p in self._ports if p._mode == NetworkExtPortMode.se]
        df_ports = [p for p in self._ports if p._mode == NetworkExtPortMode.df]
        cm_ports = [p for p in self._ports if p._mode == NetworkExtPortMode.cm]
        assert len(df_ports) + len(cm_ports) + len(se_ports) == self.number_of_ports
        assert len(df_ports) == len(cm_ports)

        ordered_indices = list(range(self.number_of_ports))
        cm_df_se_indices = list([p._index for p in [*df_ports, *cm_ports, *se_ports]])
        result = self.copy()

        if ordered_indices != cm_df_se_indices:
            result.renumber(cm_df_se_indices,ordered_indices)
        
        result.gmm2se(p=len(df_ports))

        pos_neg_ports: list[NetworkExtPort] = []
        for pport in df_ports:
            pos_neg_ports.append(NetworkExtPort(NetworkExtPortMode.pos, pport.number, len(pos_neg_ports)))
        for pport in df_ports:
            pos_neg_ports.append(NetworkExtPort(NetworkExtPortMode.neg, pport.number, len(pos_neg_ports)))
        for sport in se_ports:
            pos_neg_ports.append(NetworkExtPort(NetworkExtPortMode.se, sport.number, len(pos_neg_ports)))
        result.ports = pos_neg_ports

        return result


    def to_mixed(self) -> NetworkExt:
        self._verify_ports(self._ports)
        if not self.is_singleended:
            raise RuntimeError(f'Cannot convert network to mixed-mode')
        if not self.has_posneg_pairs:
            warnings.warn(f'Cannot convert to mixed mode (no positive or negative port terminals defined)')
            return self.copy()
        
        se_ports = [p for p in self._ports if p._mode == NetworkExtPortMode.se]
        pos_ports = [p for p in self._ports if p._mode == NetworkExtPortMode.pos]
        neg_ports = [p for p in self._ports if p._mode == NetworkExtPortMode.neg]
        pos_neg_ports = list(flat_zip(pos_ports, neg_ports))
        assert len(pos_neg_ports) + len(se_ports) == self.number_of_ports
        assert len(pos_ports) == len(neg_ports)

        ordered_indices = list(range(self.number_of_ports))
        pos_neg_se_indices = list([p._index for p in [*pos_neg_ports, *se_ports]])
        result = self.copy()

        if ordered_indices != pos_neg_se_indices:
            result.renumber(pos_neg_se_indices,ordered_indices)
        
        result.se2gmm(p=len(pos_ports))

        df_cm_ports: list[NetworkExtPort] = []
        for pport in pos_ports:
            df_cm_ports.append(NetworkExtPort(NetworkExtPortMode.df, pport.number, len(df_cm_ports)))
        for pport in pos_ports:
            df_cm_ports.append(NetworkExtPort(NetworkExtPortMode.cm, pport.number, len(df_cm_ports)))
        for sport in se_ports:
            df_cm_ports.append(NetworkExtPort(NetworkExtPortMode.se, sport.number, len(df_cm_ports)))
        result.ports = df_cm_ports

        return result
