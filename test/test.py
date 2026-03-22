import sys, os
sys.path.extend([os.path.abspath('../src'), os.path.abspath('./src')])


from lib import NetworkExt, TDR, ExpressionParser, SParamFile
from lib.expressions.sparams import SParam, SParams
from lib.expressions.networks import Network, Networks

import unittest
import tempfile
import skrf
import math
import logging
import pathlib
import numpy as np



class Tempfile:  # TODO: delete this class?

    def __init__(self):
        self.tempfile = tempfile.NamedTemporaryFile()
        self.tempfile.close()

    def __enter__(self):
        return self.tempfile.name

    def __exit__(self, type, value, traceback):
        try:
            os.remove(self.tempfile.name)
        except:
            pass



class MyTests(unittest.TestCase):


    def __init__(self, methodName: str = ...) -> None:
        self.plot_count = 0
        super().__init__(methodName)


    def get_dummy_plot_data(self, n: int) -> "list[PlotData]":  # TODO: remove this method?
        result = []
        for i in range(n):
            result.append(PlotData(f'test{i}',PlotDataQuantity('test',SiFormat(),[i+1,i+2,i+3]),PlotDataQuantity('test',SiFormat(),[i+4,i+5,i+6]),None,'-',None))
        return result


    def get_dummy_sparam_file(self, n_ports: int) -> SParamFile:

        def generate_dummy_sparams(n_ports: int) -> tuple[np.ndarray,np.ndarray,np.ndarray]:

            N_POINTS = 301
            FREQ_RANGE = (10e6, 10e9)
            RL_WORST_DB, RL_PERIOD_HZ = -15, 4e9
            IL_PER_DB_SQRT_GHZ = -0.8
            PHASE_PERIOD_HZ = 1.1e9
            NOISE_DB = -60

            f = np.linspace(*FREQ_RANGE, N_POINTS)
            s = np.zeros([len(f),n_ports,n_ports], dtype=complex)
            for ep in range(n_ports):
                for ip in range(n_ports):
                    phase = np.exp(-1j*math.tau*f/PHASE_PERIOD_HZ)
                    if ep==ip:
                        magnitude = 10**(RL_WORST_DB/20)
                        magnitude_ripple = np.cos(math.tau*f/RL_PERIOD_HZ)
                        sij = magnitude * magnitude_ripple * phase
                    else:
                        assert n_ports >= 2, f'Expected number of ports to be >= 2'
                        splitting_loss = 1 / (n_ports - 1)  # this ensures passivity
                        cable_loss = 10**((IL_PER_DB_SQRT_GHZ*np.sqrt(f/1e9))/20)
                        mismatch_loss = 1 - (10**(RL_WORST_DB/10))
                        sij = splitting_loss * cable_loss * mismatch_loss * phase * 1j  # the 1j is required for passivity
                    s[:,ep,ip] = sij
            noisefloor = np.random.rayleigh(10**(NOISE_DB/20),s.shape) * np.exp(1j*np.random.uniform(0,math.tau,s.shape))
            s += noisefloor
            
            z0 = np.array([50]*n_ports)

            return f, s, z0

        filename = f'/dummy{n_ports}-port.s{n_ports}p'
        f, s, z0 = generate_dummy_sparams(n_ports)
        network = NetworkExt(f=f, s=s, f_unit='Hz', z0=z0)
        result = SParamFile(filename)
        result._nw = network  # this ensures that SParamFile does not attempt to read from that dummy filename
        return result


    def get_dummy_sparam_files(self, n: int, n_ports: int|None = None) -> list[SParamFile]:
        if n_ports is not None:
            n_ports_list = list([n_ports] * n)
        else:
            n_ports_list = list(range(1, n+1))
        return [self.get_dummy_sparam_file(np) for np in n_ports_list]


    def get_dummy_networks_single(self, n_ports: int) -> "Networks":
        return Networks(nws=[self.get_dummy_sparam_file(n_ports)])


    def get_dummy_networks(self, n: int, n_ports: int|None = None) -> "Networks":
        return Networks(nws=self.get_dummy_sparam_files(n, n_ports))


    def setUp(self) -> None:

        self.plot_count = 0
        def plot_dummy_fn(*args, **kwargs):
            self.plot_count += 1

        SParam.setup(plot_dummy_fn)
        Networks.setup()
        
        networks_all = self.get_dummy_sparam_files(4)
        networks_selected = [networks_all[0], networks_all[1]]

        self.expression_parser = ExpressionParser(
            available_networks = networks_all,
            selected_networks = networks_selected,
            plot_fn = plot_dummy_fn,
            default_actions = [],
            ref_nw_name = None,
            slicer_fn = None,
        )

        return super().setUp()


    @property
    def root_dir(self) -> pathlib.Path:
        path = pathlib.Path('.').absolute()
        assert path.joinpath('src').exists()
        assert path.joinpath('samples').exists()
        return path


    @property
    def sample_dir(self) -> pathlib.Path:
        return self.root_dir.joinpath('samples')
    

    def assertArrayEqual(self, a, b):
        a, b = np.array(a), np.array(b)
        if a.shape != b.shape:
            self.fail(f'Arrays are not almost equal (array shapes differ, {a.shape} != {b.shape})')
        if not np.array_equal(a, b):
            idx = np.unravel_index(np.argmax(np.abs(a-b)), a.shape)
            self.fail(f'Arrays are not almost equal (biggest difference is index {idx}, {a[idx]} != {b[idx]})')
    

    def assertArrayAlmostEqual(self, a, b, rtol=1e-5, atol=1e-8):
        a, b = np.array(a), np.array(b)
        if a.shape != b.shape:
            self.fail(f'Arrays are not almost equal (array shapes differ, {a.shape} != {b.shape})')
        if not np.all(np.isclose(a, b, rtol=rtol, atol=atol)):
            idx = np.unravel_index(np.argmax(np.abs(a-b)), a.shape)
            self.fail(f'Arrays are not almost equal (biggest difference is index {idx}, {a[idx]} != {b[idx]})')



class TestExpressionParser(MyTests):


    def test_empty_expression(self):
        self.expression_parser.eval('')


    def test_simple_expression(self):
        self.expression_parser.eval('nws("*1*").s(1,1).plot()')


    def test_file_selection_methods(self):
        self.expression_parser.eval('sel_nws().plot_sel_params()')
        self.expression_parser.eval('nws("*").plot_sel_params()')
        self.expression_parser.eval('nw("*1*").plot_sel_params()')


    def test_param_selection_methods(self):
        self.expression_parser.eval('sel_nws().s(2,1).plot()')
        self.expression_parser.eval('sel_nws().s(21).plot()')
        self.expression_parser.eval('sel_nws().s("21").plot()')
        self.expression_parser.eval('sel_nws().s("2,1").plot()')
        self.expression_parser.eval('sel_nws().s("S21").plot()')
        self.expression_parser.eval('sel_nws().s("S2,1").plot()')
        self.expression_parser.eval('sel_nws().sel_params().plot()')
        self.expression_parser.eval('sel_nws().plot_sel_params()')


    def test_invalid_param_selection_methods_warns(self):
        with self.assertLogs(level=logging.WARNING):
            self.expression_parser.eval('sel_nws().s("X21").plot()')
        with self.assertLogs(level=logging.WARNING):
            self.expression_parser.eval('sel_nws().s(123).plot()')


    def test_deembedding(self):
        self.expression_parser.eval('(nw("*2*") ** nw("*2*").half().invert()).s(2,1).plot()')


    def test_k(self):
        self.expression_parser.eval('nw("*2*").k().plot()')


    def test_mu(self):
        self.expression_parser.eval('nw("*2*").mu().plot()')
        self.expression_parser.eval('nw("*2*").mu(1).plot()')
        self.expression_parser.eval('nw("*2*").mu(2).plot()')
        self.assertEqual(self.plot_count, 3)


    def test_multiline(self):
        self.expression_parser.eval('nw("*1*").s(1,1).plot()' + '\n' + 'nw("*2*").s(2,1).plot()')
        self.assertEqual(self.plot_count, 2)


    def test_matching_anything_using_nw_warns(self):
        with self.assertLogs(level=logging.WARNING):
            self.expression_parser.eval('nw("*").s(1,1).plot()')


    def test_matching_invalid_file_warns(self):
        with self.assertLogs(level=logging.WARNING):
            self.expression_parser.eval('nw("invalid_name.s1p").s(1,1).plot()')


    def test_invalid_function_fails(self):
        with self.assertRaises(Exception):
            self.expression_parser.eval('invalid_function(nw("*1*").s(1,1).plot())')


    def test_invalid_method_fails(self):
        with self.assertRaises(Exception):
            self.expression_parser.eval('nw("*1*").s(1,1).plot().invalid_method()')


    def test_simple_expression_with_syntax_error(self):
        with self.assertRaises(Exception):
            self.expression_parser.eval('sel_nws().s("S11).plot()')
        with self.assertRaises(Exception):
            self.expression_parser.eval('sel_nws(.s(11).plot()')
        with self.assertRaises(Exception):
            self.expression_parser.eval('sel_nws():s(11).plot()')
        with self.assertRaises(Exception):
            self.expression_parser.eval('/?/')



class TestPlotting(MyTests):


    def test_network_plot_stab(self):
        nw = self.get_dummy_networks_single(2)
        nw.plot_stab(1e9)


    def test_networks_plot_single(self):
        nw = self.get_dummy_networks_single(2)
        nw.s(2,1).plot()

   
    def test_networks_plot_multiple(self):
        nw = self.get_dummy_networks(3)
        nw.s(2,1).plot()



class TestTdr(MyTests):


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
        tdr.interpolation = True
        tdr.shift_s = 100e-12
        tdr.window = 'blackman'
        tdr.step_response = True
        tdr.convert_to_impedance = True
        t, z11 = tdr.get(nw.f, nw.s[:,0,0], nw.z0[0,0])

        LINE_LEN = 500e-12 * 2
        z_line1 = z11[np.argmin(np.abs(t - (0.5*LINE_LEN + tdr.shift_s)))]
        z_line2 = z11[np.argmin(np.abs(t - (1.5*LINE_LEN + tdr.shift_s)))]
        z_line3 = z11[np.argmin(np.abs(t - (2.5*LINE_LEN + tdr.shift_s)))]

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
        tdr.interpolation = True
        tdr.shift_s = 500e-12  # must shift a bit more, because the 100 Ω port is immediately hit by a 50 Ω line
        tdr.window = 'blackman'
        tdr.step_response = True
        tdr.convert_to_impedance = True
        t, z22 = tdr.get(nw.f, nw.s[:,1,1], nw.z0[0,1])

        LINE_LEN = 500e-12 * 2
        z_line1 = z22[np.argmin(np.abs(t - (0.5*LINE_LEN + tdr.shift_s)))]
        z_line2 = z22[np.argmin(np.abs(t - (1.5*LINE_LEN + tdr.shift_s)))]
        z_line3 = z22[np.argmin(np.abs(t - (2.5*LINE_LEN + tdr.shift_s)))]

        wave1 = self.Z2Γ(50,100)
        wave2 = wave1 + self.Z2T(50,100) * self.Z2Γ(100,50) * self.Z2T(100,50)
        wave3 = wave2 +  \
            self.Z2T(50,100) * self.Z2T(100,50) * self.Z2Γ(50,100) * self.Z2T(50,100) * self.Z2T(100,50) +  \
            self.Z2T(50,100) * self.Z2Γ(100,50) * self.Z2Γ(100,50) * self.Z2Γ(100,50) * self.Z2T(100,50)
        
        self.assertAlmostEqual(z_line1, self.Γ2Z(wave1,100), delta=0.05)
        self.assertAlmostEqual(z_line2, self.Γ2Z(wave2,100), delta=0.05)
        self.assertAlmostEqual(z_line3, self.Γ2Z(wave3,100), delta=0.05)



class TestSeMixed(MyTests):


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



if __name__ == '__main__':
    unittest.main()
