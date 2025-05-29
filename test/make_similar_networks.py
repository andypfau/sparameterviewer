# Generate dummy-networks of various port counts for testing purposes. These networks should be more-or-less passive.



import math
import os
import skrf
import zipfile
import tempfile
import random
import numpy as np
import scipy.interpolate



DIR = 'samples'

N_NETWORKS = 200
FREQ_RANGE = (10e6, 10e9)
N_POINTS = 301
RL_REF_DB = -15
IL_PER_DB_SQRT_GHZ = -0.8
PHASE_PERIOD_HZ = 1.1e9
OUTLIER_CHANCE = 0.04
NOISE_DB = -60

with tempfile.TemporaryDirectory() as tempdir:
    print(f'Working inside temporary directory <{tempdir}>...')
    
    zip_path = os.path.join(os.path.abspath(DIR), 'dummy_similar.zip')
    print(f'Creating <{zip_path}>...')
    with zipfile.ZipFile(zip_path, 'w') as zfp:

        for i in range(N_NETWORKS):
            
            filename = f'dummy_similar_{i+1}.s2p'
            file_path = os.path.join(os.path.abspath(tempdir), filename)
            print(f'Generating <{filename}>...')

            def make_random_scalar(n_points, center, sigma, n_frequency, outlier_chance=0):
                assert n_frequency >= 3
                x = np.linspace(0, 1, n_frequency)
                x[1:-1] += np.random.uniform(-0.25/(n_frequency-1), +0.25/(n_frequency-1), n_frequency-2)
                y = np.random.normal(center, sigma, n_frequency)
                
                if random.uniform(0,1) <= outlier_chance:
                    scale = 0.1 / (n_frequency-1)
                    random_index = random.randint(1,n_frequency-2)
                    x_to_insert = x[random_index]
                    x = np.insert(x, random_index+0, x_to_insert*(1-scale))
                    x = np.insert(x, random_index+2, x_to_insert*(1+scale))
                    y_to_insert = y[random_index]
                    y = np.insert(y, random_index+0, y_to_insert)
                    y = np.insert(y, random_index+1, -y_to_insert)

                def cosine_interpolation(x, xp, yp):
                    def cosine_part(x):
                        return 0.5 - math.cos(x*math.pi) / 2
                    assert len(xp) >= 2 and len(xp) == len(yp)
                    result = []
                    i = 0
                    for x in x:
                        if i < len(xp)-2:
                            if x >= xp[i+1]:
                                i += 1
                        rel_x = (x - xp[i]) / (xp[i+1] - xp[i])
                        rel_y = yp[i] + cosine_part(rel_x) * (yp[i+1] - yp[i])
                        result.append(rel_y)
                    return np.array(result)
                        
                mesh = np.linspace(0, 1, n_points)
                return cosine_interpolation(mesh, x, y)

            def make_random_sii(n, mag, σ_mag, pha, Δ_pha, σ_Δ_pha, outlier_chance):
                
                offset = -0.8 * mag

                v_mag = make_random_scalar(n, mag, σ_mag, 5, outlier_chance)
                v_pha = np.linspace(pha/5,pha/5+Δ_pha/5,n)
                primary = v_mag * np.exp(1j*v_pha)
                
                v_mag = make_random_scalar(n, mag, σ_mag, 12)
                v_pha = np.linspace(pha,pha+Δ_pha,n) + make_random_scalar(n, 0, σ_Δ_pha, 12, outlier_chance)
                secondary = v_mag * np.exp(1j*v_pha)
                
                return offset + primary + secondary
            
            f = np.linspace(*FREQ_RANGE, N_POINTS)
            rl_lin = 10**(RL_REF_DB/20)
            cable_loss = 10**((IL_PER_DB_SQRT_GHZ*np.sqrt(f/1e9))/20)
            s11 = make_random_sii(N_POINTS, rl_lin, rl_lin/10, 0, 5*math.tau, math.tau*0.001, OUTLIER_CHANCE)
            s22 = make_random_sii(N_POINTS, rl_lin, rl_lin/10, 0, 8*math.tau, math.tau*0.001, OUTLIER_CHANCE)
            mismatch = make_random_sii(N_POINTS, rl_lin, rl_lin/10, 0, 6*math.tau, math.tau*0.001, OUTLIER_CHANCE)
            sij = cable_loss * np.sqrt(1 - np.abs(mismatch)**2) * np.exp(-1j*math.tau*f/PHASE_PERIOD_HZ)
            
            
            s = np.zeros([len(f),2,2], dtype=complex)
            s[:,0,0] = s11
            s[:,0,1] = sij
            s[:,1,0] = sij
            s[:,1,1] = s22
            
            noisefloor = np.random.rayleigh(10**(NOISE_DB/20),s.shape) * np.exp(1j*np.random.uniform(0,math.tau,s.shape))
            s += noisefloor

            nw = skrf.Network(s=s, f=f, f_unit='Hz', comments=f'Programmatically generated dummy network for testing purposes')
            nw.write_touchstone(file_path)
            zfp.write(file_path, filename)

print(f'Done.')
