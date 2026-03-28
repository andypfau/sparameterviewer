from testlib import MyTestCase
from lib import NetworkExt, TDR
import skrf
import numpy as np



class TestTdr(MyTestCase):


    def Z2Γ(self, z: complex, z0: complex) -> complex:
        return (z - z0) / (z +z0)

    def Z2T(self, z: complex, z0: complex) -> complex:
        return 1 + self.Z2Γ(z, z0)
    
    def Γ2Z(self, Γ: complex, z0: complex) -> complex:
        return z0 * (1 + Γ) / (1 - Γ)


    def test_line3_port1(self):
        nw = skrf.Network(self.sample_dir.joinpath('line-line-line.s2p'))
        self.assertArrayAlmostEqual(nw.z0[0,:], [50,100])
        
        tdr = TDR()
        tdr.dc_extrapolation = 'polar'
        tdr.dc_assumption = 'auto'
        tdr.interpolation = True
        tdr.shift_s = 100e-12
        tdr.window = 'blackman'
        tdr.step_response = True
        tdr.convert_to_impedance = True
        t, z11 = tdr.get(nw.f, nw.s[:,0,0], nw.z0[0,0])

        LINE_LEN = 500e-12
        z_line1 = z11[np.argmin(np.abs(t - (0.5*LINE_LEN*2 + tdr.shift_s)))]
        z_line2 = z11[np.argmin(np.abs(t - (1.5*LINE_LEN*2 + tdr.shift_s)))]
        z_line3 = z11[np.argmin(np.abs(t - (2.5*LINE_LEN*2 + tdr.shift_s)))]

        wave1 = 0
        wave2 = wave1 + self.Z2Γ(100,50)
        wave3 = wave2 + self.Z2T(100,50) * self.Z2Γ(50,100) * self.Z2T(50,100)
        
        self.assertAlmostEqual(z_line1, self.Γ2Z(wave1,50), delta=0.05)
        self.assertAlmostEqual(z_line2, self.Γ2Z(wave2,50), delta=0.05)
        self.assertAlmostEqual(z_line3, self.Γ2Z(wave3,50), delta=0.05)


    def test_line3_port2(self):
        nw = skrf.Network(self.sample_dir.joinpath('line-line-line.s2p'))
        self.assertArrayAlmostEqual(nw.z0[0,:], [50,100])
        
        tdr = TDR()
        tdr.dc_extrapolation = 'polar'
        tdr.dc_assumption = 'auto'
        tdr.interpolation = True
        tdr.shift_s = 500e-12  # must shift a bit more, because the 100 Ω port is immediately hit by a 50 Ω line
        tdr.window = 'blackman'
        tdr.step_response = True
        tdr.convert_to_impedance = True
        t, z22 = tdr.get(nw.f, nw.s[:,1,1], nw.z0[0,1])

        LINE_LEN = 500e-12
        z_line1 = z22[np.argmin(np.abs(t - (0.5*LINE_LEN*2 + tdr.shift_s)))]
        z_line2 = z22[np.argmin(np.abs(t - (1.5*LINE_LEN*2 + tdr.shift_s)))]
        z_line3 = z22[np.argmin(np.abs(t - (2.5*LINE_LEN*2 + tdr.shift_s)))]

        wave1 = self.Z2Γ(50,100)
        wave2 = wave1 + self.Z2T(50,100) * self.Z2Γ(100,50) * self.Z2T(100,50)
        wave3 = wave2 +  \
            self.Z2T(50,100) * self.Z2T(100,50) * self.Z2Γ(50,100) * self.Z2T(50,100) * self.Z2T(100,50) +  \
            self.Z2T(50,100) * self.Z2Γ(100,50) * self.Z2Γ(100,50) * self.Z2Γ(100,50) * self.Z2T(100,50)
        
        self.assertAlmostEqual(z_line1, self.Γ2Z(wave1,100), delta=0.05)
        self.assertAlmostEqual(z_line2, self.Γ2Z(wave2,100), delta=0.05)
        self.assertAlmostEqual(z_line3, self.Γ2Z(wave3,100), delta=0.05)


    def test_line3_thru(self):
        nw = skrf.Network(self.sample_dir.joinpath('line-line-line.s2p'))
        self.assertArrayAlmostEqual(nw.z0[0,:], [50,100])
        
        tdr = TDR()
        tdr.dc_extrapolation = 'polar'
        tdr.dc_assumption = 'auto'
        tdr.interpolation = True
        tdr.shift_s = 100e-12
        tdr.window = 'blackman'
        tdr.step_response = True
        tdr.convert_to_impedance = False
        t, t21 = tdr.get(nw.f, nw.s[:,1,0], nw.z0[1,1])

        LINE_LEN = 500e-12

        baseline, settled = t21[0], t21[-1]

        dut_length = None
        for time,level in zip(t,t21):
            if level >= (baseline + settled) / 2:
                dut_length = time
                break
        
        self.assertIsNotNone(dut_length)
        self.assertAlmostEqual(dut_length, tdr.shift_s + 3*LINE_LEN, delta=LINE_LEN/10)



class TestSeMixed(MyTestCase):


    def test_sms_roundtrip_skrf(self):
        nw = skrf.Network(self.sample_dir.joinpath('diff_amp.s4p'))
        nw_mixed = nw.copy()
        nw_mixed.se2gmm(p=2)  # port order of diff_amp.s4p (P1,P2,N1,N2) is already compatible, no re-ordering needed
        self.assertEqual(nw.number_of_ports, nw_mixed.number_of_ports)
        self.assertArrayEqual(nw_mixed.port_modes, ['D', 'D', 'C', 'C'])
        
        nw_roundtrip = nw_mixed.copy()
        nw_roundtrip.gmm2se(p=2)
        self.assertEqual(nw.number_of_ports, nw_roundtrip.number_of_ports)
        self.assertArrayEqual(nw_roundtrip.port_modes, ['S', 'S', 'S', 'S'])
        self.assertArrayAlmostEqual(nw.f, nw_roundtrip.f)
        self.assertArrayAlmostEqual(nw.s, nw_roundtrip.s)
        self.assertArrayAlmostEqual(nw.z0, nw_roundtrip.z0)


    def test_invalid_s2m_fails(self):
        nw = NetworkExt(self.sample_dir.joinpath('diff_amp.s4p'))
        nw.ports = 'D1 D2 C1 C2'.split(' ')  # doesn't actually apply to the network, doesn't matter
        with self.assertRaises(RuntimeError):
            nw.to_mixed()  # should fail, because we defined that the network already has D/C ports


    def test_unneccessary_s2m_ok(self):
        nw = NetworkExt(self.sample_dir.joinpath('diff_amp.s4p'))
        nw.ports = 'S1 S2 S3 S4'.split(' ')
        nw.to_mixed()  # should do nothing


    def test_invalid_m2s_fails(self):
        nw = NetworkExt(self.sample_dir.joinpath('diff_amp.s4p'))
        nw.ports = 'P1 P2 N1 N2'.split(' ')
        with self.assertRaises(RuntimeError):
            nw.to_singleended()  # should fail, because the network does not have D/C ports


    def test_unneccessary_m2s_ok(self):
        nw = NetworkExt(self.sample_dir.joinpath('diff_amp.s4p'))
        nw.ports = 'S1 S2 S3 S4'.split(' ')
        nw.to_singleended()  # should do nothing


    def test_sms_roundtrip_new(self):
        nw = NetworkExt(self.sample_dir.joinpath('diff_amp.s4p'))
        nw.ports = 'P1 P2 N1 N2'.split(' ')
        
        nw_mixed = nw.to_mixed()
        self.assertEqual(nw.number_of_ports, nw_mixed.number_of_ports)
        self.assertEqual(str(nw_mixed.ports[0]), 'D1')
        self.assertEqual(str(nw_mixed.ports[1]), 'D2')
        self.assertEqual(str(nw_mixed.ports[2]), 'C1')
        self.assertEqual(str(nw_mixed.ports[3]), 'C2')

        nw_roundtrip = nw_mixed.to_singleended().reorder_ports('P1 P2 N1 N2'.split(' '))
        self.assertEqual(nw.number_of_ports, nw_roundtrip.number_of_ports)
        self.assertEqual(str(nw_roundtrip.ports[0]), 'P1')
        self.assertEqual(str(nw_roundtrip.ports[1]), 'P2')
        self.assertEqual(str(nw_roundtrip.ports[2]), 'N1')
        self.assertEqual(str(nw_roundtrip.ports[3]), 'N2')

        self.assertArrayAlmostEqual(nw.f, nw_roundtrip.f)
        self.assertArrayAlmostEqual(nw.s, nw_roundtrip.s)
        self.assertArrayAlmostEqual(nw.z0, nw_roundtrip.z0)
