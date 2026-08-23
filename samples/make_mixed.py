"""
Convert the .s4p of the differential amp, which are single-ended S-parameters,
  to a .s4p in mixed-mode representation and Touchstone 2.0 format.
"""



import os
import skrf
import numpy as np
import zipfile
import tempfile


TARGET_DIR = 'samples'


path_se = os.path.join(TARGET_DIR,'diff_amp.s4p')
nws = skrf.Network(path_se)

nwm = nws.copy()
nwm.renumber([0,2,1,3], [0,1,2,3])  # => P1, P2 = SE in, P3,P4 = SE out
nwm.se2gmm(p=2)                     # => P1 = diff in, P2 = diff out, P3 = CM in, P4 = CM out

with tempfile.TemporaryDirectory() as tempdir:
    print(f'Working inside temporary directory <{tempdir}>...')
    
    path_mixed = os.path.join(tempdir,'diff_amp_mixed.s4p')
    with open(path_mixed, 'w') as fp:

        fp.write(f'! Mixed-mode representation of <{path_se}>\n')
        fp.write('!         +-------+\n')
        fp.write('!    1 o--|Df   Df|--o 2\n')
        fp.write('!         |In  Out|\n')
        fp.write('!    3 o--|CM   CM|--o 4\n')
        fp.write('!         +-------+\n')
        fp.write('! This network serves as a sample for mixed-mode Touchstone 2.0 files\n')

        fp.write('[Version] 2.0\n')
        fp.write('# HZ S DB\n')
        fp.write(f'[Number of Ports] {nwm.number_of_ports}\n')
        fp.write(f'[Number of Frequencies] {len(nwm.f)}\n')

        fp.write('[Reference]')
        for i in range(nws.number_of_ports):
            fp.write(f' {np.real(nws.z0[0,i])}')  # impedance is given for the SINGLE-ENDED ports, by spec
        fp.write('\n')

        assert all(nwm.port_modes == ['D', 'D', 'C', 'C'])
        fp.write(f'[Mixed-Mode Order] D1,2 D3,4 C1,2 C3,4\n')

        s_db = 20 * np.log10(np.maximum(1e-15, np.abs(nwm.s)))
        s_deg = np.rad2deg(np.angle(nwm.s))  # angles are in degrees, by spec

        fp.write('[Network Data]\n')
        for i,f in enumerate(nwm.f):
            fp.write(f'{f}')
            for ep in range(nwm.number_of_ports):
                for ip in range(nwm.number_of_ports):
                    fp.write(f' {s_db[i,ep,ip]}')
                    fp.write(f' {s_deg[i,ep,ip]}')
            fp.write('\n')
        fp.write('[End]\n')

    zip_path = os.path.join(os.path.abspath(TARGET_DIR), 'diff_amp.zip')
    print(f'Creating <{zip_path}>...')
    with zipfile.ZipFile(zip_path, 'w') as zfp:
        zfp.write(path_se, 'diff_amp_se.s4p')
        zfp.write(path_mixed, 'diff_amp_mixed.s4p')

print(f'Done.')
