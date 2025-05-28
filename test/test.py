import sys, os
sys.path.append(os.path.abspath('../src'))


from lib import PlotData, PlotDataQuantity, SiFormat, ExpressionParser
from lib import SParamFile
from lib.expressions.networks import Network, Networks
from lib.expressions.sparams import SParam, SParams

import unittest, tempfile, skrf
import numpy as np


class Tempfile:

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


def get_dummy_plot_data(n: int) -> "list[PlotData]":
    result = []
    for i in range(n):
        result.append(PlotData(f'test{i}',PlotDataQuantity('test',SiFormat(),[i+1,i+2,i+3]),PlotDataQuantity('test',SiFormat(),[i+4,i+5,i+6]),None,'-',None))
    return result


def get_dummy_sparam_file(n_ports: int) -> "SParamFile":
    N_FREQUENCIES = 101
    filename = f'/tmp/{n_ports}-port.s{n_ports}p'
    frequencies = np.geomspace(1e6,10e9,N_FREQUENCIES)
    sparams = np.random.rand(N_FREQUENCIES,n_ports,n_ports) + 1j*np.random.rand(N_FREQUENCIES,n_ports,n_ports)
    network = skrf.Network(f=frequencies, s=sparams, f_unit='Hz')
    return SParamFile(filename, network)


def get_dummy_sparam_files(n: int) -> "list[SParamFile]":
    return [get_dummy_sparam_file(n_ports) for n_ports in range(1,n+1)]


def get_dummy_networks_single(n_ports: int) -> "Networks":
    return Networks(nws=[get_dummy_sparam_file(n_ports)])


def get_dummy_networks(n: int) -> "Networks":
    return Networks(nws=get_dummy_sparam_files(n))



class SParamViewerTest(unittest.TestCase):


    def __init__(self, methodName: str = ...) -> None:
        self.plot_count = 0
        super().__init__(methodName)


    def setUp(self) -> None:

        self.plot_count = 0
        def plot_dummy_fn(*args, **kwargs):
            self.plot_count += 1

        SParam._plot_fn = plot_dummy_fn
        Networks.available_networks = []

        all = get_dummy_sparam_files(4)
        selected = [all[0], all[1]]
        self.eval_kwargs = dict(
            available_networks = all,
            selected_networks = selected,
            plot_fn = plot_dummy_fn
        )

        return super().setUp()

    
    def test_empty_expression(self):
        ExpressionParser.eval('', **self.eval_kwargs)

    
    def test_simple_expression_objects(self):
        ExpressionParser.eval('nws("*1*").s(1,1).plot()', **self.eval_kwargs)
    

    def test_advanced_expression_add_parts(self):
        ExpressionParser.eval('nw("*2*").add_sc(1e-15).add_sl(1e-12).add_sr(10).add_pc(1e-15).add_pl(1e-12).add_pr(10).add_tl(90,1e9).s(2,1).plot()', **self.eval_kwargs)
    

    def test_advanced_expression_deembed(self):
        ExpressionParser.eval('(nw("*2*") ** nw("*2*").half().invert()).s(2,1).plot()', **self.eval_kwargs)
    

    def test_advanced_expression_stability_k(self):
        ExpressionParser.eval('nw("*2*").k().plot()', **self.eval_kwargs)
    

    def test_advanced_expression_stability_mu(self):
        ExpressionParser.eval('nw("*2*").mu().plot()', **self.eval_kwargs)
    

    def test_advanced_expression_stability_mu1(self):
        ExpressionParser.eval('nw("*2*").mu(1).plot()', **self.eval_kwargs)
    

    def test_advanced_expression_stability_mu2(self):
        ExpressionParser.eval('nw("*2*").mu(2).plot()', **self.eval_kwargs)
    

    def test_multiple_expressions(self):
        ExpressionParser.eval('nw("*1*").s(1,1).plot()\nnw("*2*").s(2,1).plot()', **self.eval_kwargs)
        self.assertEqual(self.plot_count,2)

    
    def test_simple_expression_with_invalid_file(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("invalid").s(1,1).plot()', **self.eval_kwargs)

    
    def test_simple_expression_with_invalid_function(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('foo(nw("*1*").s(1,1).plot())', **self.eval_kwargs)

    
    def test_simple_expression_with_invalid_method(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("*1*").s(1,1).plot().invalid()', **self.eval_kwargs)

    
    def test_simple_expression_with_syntax_error(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("*1*).s(1,1).plot().invalid()', **self.eval_kwargs)
    

    def test_network_plot_stab(self):
        nw = get_dummy_networks_single(2)
        nw.plot_stab(1e9)


    def test_networks_plot_single(self):
        nw = get_dummy_networks_single(2)
        nw.s(2,1).plot()

    
    def test_networks_plot_multiple(self):
        nw = get_dummy_networks(3)
        nw.s(2,1).plot()



if __name__ == '__main__':
    # TODO: fix tests
    unittest.main()
