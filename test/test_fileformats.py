from testlib import MyTestCase
from lib import SParamFile, PathExt, CitiWriter
import os
import skrf
import zipfile
import tempfile



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


    def test_load_from_zip(self):
        with tempfile.TemporaryDirectory() as wdir:
            
            nw1name = 'test.s1p'
            nw1path = os.path.join(wdir, nw1name)
            nw = skrf.Network(f=[0,1e9,2e9], f_unit='Hz', s=[[[1]], [[0.5]], [[0]]], z0=50)
            nw.write_touchstone(nw1path)

            nw2name = 'test.cti'
            nw2path = os.path.join(wdir, nw2name)
            CitiWriter().write(nw, nw2path)

            zippath = os.path.join(wdir, 'test.zip')
            with zipfile.ZipFile(zippath, 'w') as zf:
                zf.write(nw1path, nw1name)
                zf.write(nw2path, nw2name)
            
            os.remove(nw1path)
            os.remove(nw2path)

            for nwname in [nw1name, nw2name]:
                f = SParamFile(PathExt(zippath, arch_path=nwname))
                self.assertEqual(f.nw.number_of_ports, 1)
                self.assertEqual(len(f.nw.f), 3)
                self.assertArrayAlmostEqual(f.nw.z0_simple, [50])
                self.assertSequenceEqual(f.nw.port_modes, ['S'])
