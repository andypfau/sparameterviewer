import math
import os
import skrf
import zipfile
import tempfile
import numpy as np



WDIR = 'samples'

nw_s = skrf.Network(f'{WDIR}/diff_amp.s4p')
print(f'Single-Ended')
print(f'Port names: {nw_s.port_names}')
print(f'Port modes: {nw_s.port_modes}')
print(f'Port tuples: {nw_s.port_tuples}')

print()

nw = nw_s.copy()
nw.se2gmm(2)
print(f'Mixed-Mode')
print(f'Port names: {nw.port_names}')
print(f'Port modes: {nw.port_modes}')
print(f'Port tuples: {nw.port_tuples}')

def get_sparam_name(nw: skrf.Network, egress: int, ingress: int, prefix: str = 'S') -> str:

    def _get_mode(index: int) -> str:
        if index < 0 or index >= len(nw.port_modes):
            return ''
        return nw.port_modes[index]
        

    is_mixed_mode = 'C' in nw.port_modes or 'D' in nw.port_modes
    if is_mixed_mode:
        egress_mode, ingress_mode = _get_mode(egress-1), _get_mode(ingress-1)
        if egress<10 and ingress<10:
            return f'{prefix}{egress_mode}{ingress_mode}{egress}{ingress}'
        else:
            return f'{prefix}{egress_mode}{ingress_mode}{egress},{ingress}'
    else:
        if egress<10 and ingress<10:
            return f'{prefix}{egress}{ingress}'
        else:
            return f'{prefix}{egress},{ingress}'


def get_port_index(nw: skrf.Network, mode: str, number: int) -> int:
    port_numbers = dict()
    for i in range(nw.number_of_ports):
        current_mode = nw.port_modes[i]
        port_numbers[current_mode] = port_numbers.get(current_mode, 0) + 1
        current_number = port_numbers[current_mode]
        if current_mode==mode and current_number==number:
            return i
    raise RuntimeError(f'Cannot find port {mode}{number} in network {nw.name}; port numbers is {port_numbers}')

for i in range(4):
    for j in range(4):
        print(get_sparam_name(nw, i+1,j+1), end='  ')
    print('')
