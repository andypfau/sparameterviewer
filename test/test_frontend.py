from testlib import MyTestCase
from lib import NetworkExt, ExpressionParser, SParamFile
from lib.expressions.sparams import SParam, SParams
from lib.expressions.networks import Network, Networks
import math
import logging
import numpy as np



class MyFrontendTestCase(MyTestCase):


    def __init__(self, methodName: str = ...) -> None:
        self.plot_count = 0
        super().__init__(methodName)


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



class TestExpressionParser(MyFrontendTestCase):


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



class TestPlotting(MyFrontendTestCase):


    def test_network_plot_stab(self):
        nw = self.get_dummy_networks_single(2)
        nw.plot_stab(1e9)


    def test_networks_plot_single(self):
        nw = self.get_dummy_networks_single(2)
        nw.s(2,1).plot()

   
    def test_networks_plot_multiple(self):
        nw = self.get_dummy_networks(3)
        nw.s(2,1).plot()
