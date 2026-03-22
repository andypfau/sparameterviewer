from testlib import MyTestCase
from lib import SParamFile
import pathlib
import numpy as np



class TestFileFormats(MyTestCase):


    def test_load_touchstone(self):
        for path in self.sample_dir.glob('*.s?p'):
            SParamFile(path)
    
    
    def test_load_citi(self):
        for path in self.sample_dir.glob('*.cti'):
            SParamFile(path)
    
    
    def test_touchstone_contents(self):
        f = SParamFile(self.sample_dir.joinpath('line-line-line.s2p'))
        self.assertEqual(f.nw.number_of_ports, 2)
        self.assertArrayAlmostEqual(f.nw.z0_simple, [50,100])
        self.assertArrayEqual(f.nw.port_modes, ['S', 'S'])
        self.assertIsInstance(f.nw.comments, str)
        self.assertTrue('2-Port simulation' in f.nw.comments)  # should be in 1st line
        self.assertTrue('This model can be used to verify' in f.nw.comments)  # should be in a later line
        
        f = SParamFile(self.sample_dir.joinpath('diff_amp.s4p'))
        self.assertEqual(f.nw.number_of_ports, 4)
        self.assertArrayEqual(f.nw.port_modes, ['S', 'S', 'S', 'S'])
        self.assertArrayAlmostEqual(f.nw.z0_simple, [50,50,50,50])


    def test_citi_contents(self):
        f = SParamFile(self.sample_dir.joinpath('coupler_3port.cti'))
        self.assertEqual(f.nw.number_of_ports, 3)
        self.assertArrayAlmostEqual(f.nw.z0_simple, [50,50,50])
        self.assertArrayEqual(f.nw.port_modes, ['S', 'S', 'S'])
        self.assertIsInstance(f.nw.comments, str)
        self.assertTrue('Simulation of a' in f.nw.comments)  # should be in 1st line
        self.assertTrue('P1 and P2 are the thru ports' in f.nw.comments)  # should be in a later line
