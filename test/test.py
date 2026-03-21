import sys, os
sys.path.extend([os.path.abspath('../src'), os.path.abspath('./src')])


from lib import NetworkExt, TDR

import unittest
import tempfile
import skrf
import pathlib
import numpy as np



class MyTests(unittest.TestCase):

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



#class Tempfile:
#
#    def __init__(self):
#        self.tempfile = tempfile.NamedTemporaryFile()
#        self.tempfile.close()
#
#    def __enter__(self):
#        return self.tempfile.name
#
#    def __exit__(self, type, value, traceback):
#        try:
#            os.remove(self.tempfile.name)
#        except:
#            pass
#
#
#def get_dummy_plot_data(n: int) -> "list[PlotData]":
#    result = []
#    for i in range(n):
#        result.append(PlotData(f'test{i}',PlotDataQuantity('test',SiFormat(),[i+1,i+2,i+3]),PlotDataQuantity('test',SiFormat(),[i+4,i+5,i+6]),None,'-',None))
#    return result
#
#
#def get_dummy_sparam_file(n_ports: int) -> "SParamFile":
#    N_FREQUENCIES = 101
#    filename = f'/tmp/{n_ports}-port.s{n_ports}p'
#    frequencies = np.geomspace(1e6,10e9,N_FREQUENCIES)
#    sparams = np.random.rand(N_FREQUENCIES,n_ports,n_ports) + 1j*np.random.rand(N_FREQUENCIES,n_ports,n_ports)
#    network = NetworkExt(f=frequencies, s=sparams, f_unit='Hz')
#    return SParamFile(filename, network)
#
#
#def get_dummy_sparam_files(n: int) -> "list[SParamFile]":
#    return [get_dummy_sparam_file(n_ports) for n_ports in range(1,n+1)]
#
#
#def get_dummy_networks_single(n_ports: int) -> "Networks":
#    return Networks(nws=[get_dummy_sparam_file(n_ports)])
#
#
#def get_dummy_networks(n: int) -> "Networks":
#    return Networks(nws=get_dummy_sparam_files(n))
#
#
#
#class SParamViewerTest(unittest.TestCase):
#
#
#    def __init__(self, methodName: str = ...) -> None:
#        self.plot_count = 0
#        super().__init__(methodName)
#
#
#    def setUp(self) -> None:
#
#        self.plot_count = 0
#        def plot_dummy_fn(*args, **kwargs):
#            self.plot_count += 1
#
#        SParam._plot_fn = plot_dummy_fn
#        Networks.available_networks = []
#
#        all = get_dummy_sparam_files(4)
#        selected = [all[0], all[1]]
#        self.eval_kwargs = dict(
#            available_networks = all,
#            selected_networks = selected,
#            plot_fn = plot_dummy_fn
#        )
#
#        return super().setUp()
#
#    
#    def test_empty_expression(self):
#        ExpressionParser.eval('', **self.eval_kwargs)
#
#    
#    def test_simple_expression_objects(self):
#        ExpressionParser.eval('nws("*1*").s(1,1).plot()', **self.eval_kwargs)
#    
#
#    def test_advanced_expression_add_parts(self):
#        ExpressionParser.eval('nw("*2*").add_sc(1e-15).add_sl(1e-12).add_sr(10).add_pc(1e-15).add_pl(1e-12).add_pr(10).add_tl(90,1e9).s(2,1).plot()', **self.eval_kwargs)
#    
#
#    def test_advanced_expression_deembed(self):
#        ExpressionParser.eval('(nw("*2*") ** nw("*2*").half().invert()).s(2,1).plot()', **self.eval_kwargs)
#    
#
#    def test_advanced_expression_stability_k(self):
#        ExpressionParser.eval('nw("*2*").k().plot()', **self.eval_kwargs)
#    
#
#    def test_advanced_expression_stability_mu(self):
#        ExpressionParser.eval('nw("*2*").mu().plot()', **self.eval_kwargs)
#    
#
#    def test_advanced_expression_stability_mu1(self):
#        ExpressionParser.eval('nw("*2*").mu(1).plot()', **self.eval_kwargs)
#    
#
#    def test_advanced_expression_stability_mu2(self):
#        ExpressionParser.eval('nw("*2*").mu(2).plot()', **self.eval_kwargs)
#    
#
#    def test_multiple_expressions(self):
#        ExpressionParser.eval('nw("*1*").s(1,1).plot()\nnw("*2*").s(2,1).plot()', **self.eval_kwargs)
#        self.assertEqual(self.plot_count,2)
#
#    
#    def test_simple_expression_with_invalid_file(self):
#        with self.assertRaises(Exception):
#            ExpressionParser.eval('nw("invalid").s(1,1).plot()', **self.eval_kwargs)
#
#    
#    def test_simple_expression_with_invalid_function(self):
#        with self.assertRaises(Exception):
#            ExpressionParser.eval('foo(nw("*1*").s(1,1).plot())', **self.eval_kwargs)
#
#    
#    def test_simple_expression_with_invalid_method(self):
#        with self.assertRaises(Exception):
#            ExpressionParser.eval('nw("*1*").s(1,1).plot().invalid()', **self.eval_kwargs)
#
#    
#    def test_simple_expression_with_syntax_error(self):
#        with self.assertRaises(Exception):
#            ExpressionParser.eval('nw("*1*).s(1,1).plot().invalid()', **self.eval_kwargs)
#    
#
#    def test_network_plot_stab(self):
#        nw = get_dummy_networks_single(2)
#        nw.plot_stab(1e9)
#
#
#    def test_networks_plot_single(self):
#        nw = get_dummy_networks_single(2)
#        nw.s(2,1).plot()
#
#    
#    def test_networks_plot_multiple(self):
#        nw = get_dummy_networks(3)
#        nw.s(2,1).plot()



class TdrTests(MyTests):


    def test_sms_roundtrip_skrf(self):
        nw = skrf.Network(self.sample_dir.joinpath('line-line-line.s2p'))
        
        tdr = TDR()
        tdr.dc_extrapolation = 'polar'
        tdr.interpolation = True
        tdr.shift_s = 100e-12
        tdr.window = 'blackman'
        tdr.step_response = True
        tdr.convert_to_impedance = True
        t, z = tdr.get(nw.f, nw.s[:,0,0], nw.z0[0,0])

        z_line1 = z[np.argmin(np.abs(t - 0.5e-9))]
        z_line2 = z[np.argmin(np.abs(t - 1.5e-9))]
        z_line3 = z[np.argmin(np.abs(t - 2.5e-9))]

        # note that each cascaded line shadows-off the next one, so the
        #   impedance error accumulates quickly; to compensate for that,
        #   an increasingly larger delta has to be accepted
        
        self.assertAlmostEqual(z_line1,  50, delta=0.05)
        self.assertAlmostEqual(z_line2, 100, delta=0.50)
        self.assertAlmostEqual(z_line3,  50, delta=5.00)



class SeMixedTests(MyTests):


    def test_sms_roundtrip_skrf(self):
        nw = skrf.Network(self.sample_dir.joinpath('diff_amp.s4p'))
        nw_roundtrip = nw.copy()
        nw_roundtrip.se2gmm(p=2)  # port order of diff_amp.s4p (P1,P2,N1,N2) is already compatible, no re-ordering needed
        self.assertArrayEqual(nw_roundtrip.port_modes, ['D', 'D', 'C', 'C'])
        nw_roundtrip.gmm2se(p=2)
        self.assertArrayEqual(nw_roundtrip.port_modes, ['S', 'S', 'S', 'S'])
        self.assertEqual(nw.number_of_ports, nw_roundtrip.number_of_ports)
        self.assertArrayAlmostEqual(nw.f, nw_roundtrip.f)
        self.assertArrayAlmostEqual(nw.s, nw_roundtrip.s)
        self.assertArrayAlmostEqual(nw.z0, nw_roundtrip.z0)


    def test_sms_roundtrip_new(self):
        nw = NetworkExt(self.sample_dir.joinpath('diff_amp.s4p'))
        nw.ports = ['P1', 'P2', 'N1', 'N2']
        nw_roundtrip = nw.to_mixed().to_singleended()
        self.assertEqual(nw.number_of_ports, nw_roundtrip.number_of_ports)
        self.assertArrayAlmostEqual(nw.f, nw_roundtrip.f)
        self.assertArrayAlmostEqual(nw.s, nw_roundtrip.s)  # TODO: this fails; no idea why, skrf.Network works as expected...
        self.assertArrayAlmostEqual(nw.z0, nw_roundtrip.z0)



if __name__ == '__main__':
    # TODO: fix tests
    unittest.main()
