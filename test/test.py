import sys, os
sys.path.append(os.path.abspath('../src'))


from lib import DataExport, PlotData, PlotDataQuantity, SiFmt, ExpressionParser, LoadedSParamFile, Touchstone

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
        result.append(PlotData(f'test{i}',PlotDataQuantity('test',SiFmt(),[i+1,i+2,i+3]),PlotDataQuantity('test',SiFmt(),[i+4,i+5,i+6]),'-',None))
    return result


def get_dummy_sparams(n: int) -> "list[LoadedSParamFile]":
    N_FREQUENCIES = 101
    result = []
    for i in range(n):
        n_ports = i+1
        filename = f'/tmp/{n_ports}-port.s{n_ports}p'
        frequencies = np.geomspace(1e6,10e9,N_FREQUENCIES)
        sparams = np.random.rand(N_FREQUENCIES,n_ports,n_ports) + 1j*np.random.rand(N_FREQUENCIES,n_ports,n_ports)
        network = skrf.Network(f=frequencies, s=sparams, f_unit='Hz')
        touchstone = Touchstone(filename, network=network)
        result.append(LoadedSParamFile(f'{n_ports}-port', filename, touchstone))
    return result


def dummy_method(*args, **kwargs):
    return


class SParamViewerTest(unittest.TestCase):

    def test_export_empty_to_spreadsheet(self):
        with Tempfile() as fn:
            DataExport.to_spreadsheet(get_dummy_plot_data(0), fn)

    def test_export_to_spreadsheet(self):
        with Tempfile() as fn:
            DataExport.to_spreadsheet(get_dummy_plot_data(2), fn)

    def test_export_empty_to_csv(self):
        with Tempfile() as fn:
            DataExport.to_csv(get_dummy_plot_data(0), fn)

    def test_export_to_csv(self):
        with Tempfile() as fn:
            DataExport.to_csv(get_dummy_plot_data(2), fn)
    
    def test_empty_expression(self):
        ExpressionParser.eval('', get_dummy_sparams(4), dummy_method)
    
    def test_simple_expression_objects(self):
        ExpressionParser.eval('Network("1").s(1,1).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_simple_expression_functions(self):
        ExpressionParser.eval('plot(s(nw("1"),1,1))', get_dummy_sparams(4), dummy_method)
    
    def test_advanced_expression_add_parts(self):
        ExpressionParser.eval('nw("2").add_sc(1e-15).add_sl(1e-12).add_sr(10).add_pc(1e-15).add_pl(1e-12).add_pr(10).add_tl(90,1e9).s(2,1).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_advanced_expression_deembed(self):
        ExpressionParser.eval('(nw("2") ** nw("2").half().invert()).s(2,1).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_advanced_expression_stability_k(self):
        ExpressionParser.eval('nw("2").k().plot()', get_dummy_sparams(4), dummy_method)
    
    def test_advanced_expression_stability_mu(self):
        ExpressionParser.eval('nw("2").mu().plot()', get_dummy_sparams(4), dummy_method)
    
    def test_advanced_expression_stability_mu1(self):
        ExpressionParser.eval('nw("2").mu(1).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_advanced_expression_stability_mu2(self):
        ExpressionParser.eval('nw("2").mu(2).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_multiple_expressions(self):
        n_calls = 0
        def counting_dummy_method(*args, **kwargs):
            nonlocal n_calls
            n_calls += 1
        ExpressionParser.eval('nw("1").s(1,1).plot()\nnw("2").s(2,1).plot()', get_dummy_sparams(4), counting_dummy_method)
        self.assertEqual(n_calls,2)
    
    def test_simple_expression_with_invalid_file(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("invalid").s(1,1).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_simple_expression_with_invalid_sparam(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("1").s(9,9).plot()', get_dummy_sparams(4), dummy_method)
    
    def test_simple_expression_with_invalid_function(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('foo(nw("1").s(1,1).plot())', get_dummy_sparams(4), dummy_method)
    
    def test_simple_expression_with_invalid_method(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("1").s(1,1).plot().invalid()', get_dummy_sparams(4), dummy_method)
    
    def test_simple_expression_with_syntax_error(self):
        with self.assertRaises(Exception):
            ExpressionParser.eval('nw("1).s(1,1).plot().invalid()', get_dummy_sparams(4), dummy_method)


if __name__ == '__main__':
    unittest.main()
