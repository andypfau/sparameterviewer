from testlib import MyTestCase
from lib import SiFormat, SiValue, SiRange
import skrf
import numpy as np



class TestSiValue(MyTestCase):


    def test_plain(self):
        self.assertEqual(str(SiValue(0)), '0')
        self.assertEqual(str(SiValue(3e-12)), '3 p')
        self.assertEqual(str(SiValue(3e-12, 'F')), '3 pF')
        self.assertEqual(str(SiValue(0.3e-12)), '300 f')


    def test_unit(self):
        self.assertEqual(str(SiValue(0, 'V')), '0 V')
        self.assertEqual(str(SiValue(3e-12, 'F')), '3 pF')
        self.assertEqual(str(SiValue(0.3e-12, 'F')), '300 fF')


    def test_parse(self):
        self.assertAlmostEqual(SiFormat('V').parse('3.141 V'), 3.141)
        self.assertAlmostEqual(SiFormat('A').parse('0.5 mA'), 0.5e-3)
    

    def parse_invalid(self):
        with self.assertRaises(ValueError):
            SiFormat('A').parse('0.5 mV')
        with self.assertRaises(ValueError):
            SiFormat('A').parse('somethinginvalid')



class TestSiRange(MyTestCase):


    def test_plain(self):
        self.assertEqual(str(SiRange(0, 1)), '0 … 1')


    def test_unit(self):
        self.assertEqual(str(SiRange(0, 1, SiFormat('V'))), '0 V … 1 V')
        self.assertEqual(str(SiRange(1e-3, 3e3, SiFormat('Ω'))), '1 mΩ … 3 kΩ')


    def test_wildcard(self):
        self.assertEqual(str(SiRange(any, any, SiFormat('V'))), '*')
        self.assertEqual(str(SiRange(0, any, SiFormat('V'))), '0 V … *')
        self.assertEqual(str(SiRange(any, 5, SiFormat('V'))), '* … 5 V')


    def test_parse(self):
        r = SiRange(spec=SiFormat('V')).parse('1.5m-3k')
        self.assertAlmostEqual(r.low, 1.5e-3)
        self.assertAlmostEqual(r.high, 3e3)

        r = SiRange(spec=SiFormat('V')).parse('1kV-*')
        self.assertAlmostEqual(r.low, 1e3)
        self.assertAlmostEqual(r.high, any)
    

    def parse_invalid(self):
        with self.assertRaises(ValueError):
            SiRange(spec=SiFormat('V')).parse('1kV to 2kv')
        with self.assertRaises(ValueError):
            SiRange(spec=SiFormat('V')).parse('somethinginvalid')
