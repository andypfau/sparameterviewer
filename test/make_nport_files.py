# Generate dummy-networks of various port counts for testing purposes. These networks should be more-or-less passive.



import math
import os
import skrf
import zipfile
import tempfile
import numpy as np



DIR = 'samples'

N_POINTS = 301
FREQ_RANGE = (10e6, 10e9)
PORT_RANGE = (1,32)
RL_WORST_DB, RL_PERIOD_HZ = -15, 4e9
IL_PER_DB_SQRT_GHZ = -0.8
PHASE_PERIOD_HZ = 1.1e9
NOISE_DB = -60

with tempfile.TemporaryDirectory() as tempdir:
    print(f'Working inside temporary directory <{tempdir}>...')
    
    zip_path = os.path.join(os.path.abspath(DIR), 'dummy_networks.zip')
    print(f'Creating <{zip_path}>...')
    with zipfile.ZipFile(zip_path, 'w') as zfp:

        for n_ports in range(PORT_RANGE[0], PORT_RANGE[1]+1):
            
            if n_ports >= 2:
                desc = f'{n_ports}-way divider'
                filename = f'dummy_{n_ports}-way-divider.s{n_ports}p'
            else:
                desc = 'termination'
                filename = f'dummy_termination.s{n_ports}p'
            file_path = os.path.join(os.path.abspath(tempdir), filename)
            print(f'Generating <{filename}>...')

            f = np.linspace(*FREQ_RANGE, N_POINTS)
            
            s = np.zeros([len(f),n_ports,n_ports], dtype=complex)
            for ep in range(n_ports):
                for ip in range(n_ports):
                    phase = np.exp(1j*math.tau*f/PHASE_PERIOD_HZ)
                    if ep==ip:
                        magnitude = 10**(RL_WORST_DB/20)
                        magnitude_ripple = np.cos(math.tau*f/RL_PERIOD_HZ)
                        sij = magnitude * magnitude_ripple * phase
                    else:
                        assert n_ports >= 2
                        splitting_loss = 1 / (n_ports - 1)  # this ensures passivity
                        cable_loss = 10**((IL_PER_DB_SQRT_GHZ*np.sqrt(f/1e9))/20)
                        mismatch_loss = 1 - (10**(RL_WORST_DB/10))
                        sij = splitting_loss * cable_loss * mismatch_loss * phase * 1j  # the 1j is required for passivity
                    s[:,ep,ip] = sij

            noisefloor = np.random.rayleigh(10**(NOISE_DB/20),s.shape) * np.exp(1j*np.random.uniform(0,math.tau,s.shape))
            s += noisefloor

            nw = skrf.Network(s=s, f=f, f_unit='Hz', comments=f'Programmatically generated dummy network ({desc}) for testing purposes')
            nw.write_touchstone(file_path)
            zfp.write(file_path, filename)

print(f'Done.')
