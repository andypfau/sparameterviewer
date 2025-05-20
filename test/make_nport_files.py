# Generate dummy-networks of various port counts for testing purposes. These networks should be more-or-less passive.



import math
import os
import skrf
import random
import numpy as np



DIR = 'samples'

N_POINTS = 301
FREQ_RANGE = (10e6, 10e9)
PORT_RANGE = (1,32)
RL_WORST_DB, RL_PERIOD_HZ = -15, 4e9
RL_PHASE_PERIOD_HZ = 1.1e9
IL_PER_DB_SQRT_GHZ = -0.8
IL_PHASE_PERIOD_HZ = 1e9
NOISE_DB = -60



for n_ports in range(PORT_RANGE[0], PORT_RANGE[1]+1):
    
    filename = os.path.join(os.path.abspath(DIR), f'dummy_nw_{n_ports}-port.s{n_ports}p')
    print(f'Generating <{filename}>...')

    f = np.linspace(*FREQ_RANGE, N_POINTS)
    
    s = np.zeros([len(f),n_ports,n_ports], dtype=complex)
    for ep in range(n_ports):
        for ip in range(n_ports):
            if ep==ip:
                magnitude = 10**(RL_WORST_DB/20)
                magnitude_ripple = np.cos(math.tau*f/RL_PERIOD_HZ)
                phase = np.exp(1j*math.tau*f/RL_PHASE_PERIOD_HZ)
                sij = magnitude * magnitude_ripple * phase
            else:
                assert n_ports >= 2
                splitting_loss = math.sqrt(n_ports - 1)
                cable_loss = 10**((IL_PER_DB_SQRT_GHZ*np.sqrt(f/1e9))/20)
                mismatch_loss = math.sqrt(1 - (10**(RL_WORST_DB/10)))
                phase = np.exp(1j*math.tau*f/IL_PHASE_PERIOD_HZ)
                sij = splitting_loss * cable_loss * mismatch_loss * phase
            s[:,ep,ip] = sij

    noisefloor = np.random.rayleigh(10**(NOISE_DB/20),s.shape) * np.exp(1j*np.random.uniform(0,math.tau,s.shape))
    s += noisefloor

    nw = skrf.Network(s=s, f=f, f_unit='Hz')

    nw.write_touchstone(filename)

print(f'Done.')
