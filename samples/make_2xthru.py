"""
Generate 2xTHRU networks, which represent a band-pass filter, and some feed-lines
"""



import math
import random
import os
import skrf
import zipfile
import tempfile
import numpy as np



TARGET_DIR = 'samples'

N_POINTS = 301
FREQ_RANGE = (10e6, 10e9)

with tempfile.TemporaryDirectory() as tempdir:
    print(f'Working inside temporary directory <{tempdir}>...')
    
    zip_path = os.path.join(os.path.abspath(TARGET_DIR), '2xthru.zip')
    print(f'Creating <{zip_path}>...')
    with zipfile.ZipFile(zip_path, 'w') as zfp:

        freq = skrf.Frequency(*FREQ_RANGE, N_POINTS)

        def make_msl(len_m: float, w_m: float, name='MSL') -> skrf.Network:
            len_m += random.gauss(0, 60e-6)
            w_m += random.gauss(0, 10e-6)
            msl = skrf.media.MLine(
                frequency=freq,
                ep_r=3.4,
                tand=0.03,
                w=w_m,
                h=0.1e-3,
                t=18e-6,
                z0_port=50,
            )
            def make(name):
                return msl.line(len_m, unit='m', name=name)
            if isinstance(name, list):
                return tuple([make(n) for n in name])
            else:
                return make(name)

        conn1, conn2 = make_msl(5e-3, 0.19e-3, name=['Connector 1', 'Connector 2'])  # tiny mismatch
        trace1, trace2 = make_msl(25e-3, 0.214e-3, name=['Feed 1', 'Feed 2'])
        feed1  = skrf.circuit.Circuit(connections=[
            [(skrf.circuit.Circuit.Port(freq, 'Port 1'), 0), (conn1, 0)],
            [(conn1, 1), (trace1, 0)],
            [(trace1, 1), (skrf.circuit.Circuit.Port(freq, 'Port 2'), 0)],
        ]).network
        feed2  = skrf.circuit.Circuit(connections=[
            [(skrf.circuit.Circuit.Port(freq, 'Port 1'), 0), (conn2, 0)],
            [(conn2, 1), (trace2, 0)],
            [(trace2, 1), (skrf.circuit.Circuit.Port(freq, 'Port 2'), 0)],
        ]).network

        shunt1, shunt5 = make_msl(8.64e-3, 1.05e-3, name=['Shunt 1', 'Shunt 5'])
        line1, line4 = make_msl(9.39e-3, 0.170e-3, name=['Line 1', 'Line 4'])
        shunt2, shunt4 = make_msl(8.41e-3, 2.37e-3, name=['Shunt 2', 'Shunt 4'])
        line2, line3 = make_msl(9.60e-3, 0.11e-3, name=['Line 2', 'Line 3'])
        shunt3 = make_msl(8.41e-3, 2.43e-3, name='Shunt 3')

        filter = skrf.circuit.Circuit(connections=[
            [(skrf.circuit.Circuit.Port(freq, 'Port 1'), 0), (shunt1, 0), (line1, 0)],
            [(shunt1, 1), (skrf.circuit.Circuit.Ground(freq, 'GND 1'), 0)],
            [(line1, 1), (shunt2, 0), (line2, 0)],
            [(shunt2, 1), (skrf.circuit.Circuit.Ground(freq, 'GND 2'), 0)],
            [(line2, 1), (shunt3, 0), (line3, 0)],
            [(shunt3, 1), (skrf.circuit.Circuit.Ground(freq, 'GND 3'), 0)],
            [(line3, 1), (shunt4, 0), (line4, 0)],
            [(shunt4, 1), (skrf.circuit.Circuit.Ground(freq, 'GND 4'), 0)],
            [(line4, 1), (shunt5, 0), (skrf.circuit.Circuit.Port(freq, 'Port 2'), 0)],
            [(shunt5, 1), (skrf.circuit.Circuit.Ground(freq, 'GND 5'), 0)],
        ]).network

        def save_nw(nw, filename):
            file_path = os.path.join(os.path.abspath(tempdir), filename)
            nw.write_touchstone(file_path)
            zfp.write(file_path, filename)

        save_nw(filter, 'Dut.s2p')
        save_nw(feed1**feed2, 'ThruThru.s2p')
        save_nw(feed1**filter**feed2, 'ThruDutThru.s2p')

print(f'Done.')
