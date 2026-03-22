from testlib import MyTestCase
from lib import get_unique_short_filename, shorten_path, is_ext_supported, is_ext_supported_file, is_ext_supported_archive
from lib import group_delay, v2db, db2v, choose_smart_db_scale
from lib import get_unique_id, any_common_elements, window_has_argument
from lib import natural_sort_key, format_minute_seconds, string_to_enum, enum_to_string, strip_common
from lib import get_next_1_10_100, get_next_1_3_10, get_next_1_2_5_10
from lib import find_files_in_archive, load_file_from_archive
import math
import numpy as np



class TestUtils(MyTestCase):


    def test_db(self):
        self.assertAlmostEqual(v2db(0.1), -20)
        self.assertAlmostEqual(v2db(0.1j), -20)
        self.assertAlmostEqual(v2db(0.5-0.5j), -3.01, delta=0.01)
        self.assertAlmostEqual(db2v(-20), 0.1)


    def test_group_delay(self):
        n = 10
        f = np.linspace(0, 1e9, n)
        s = np.exp(1j * np.linspace(0, math.tau, n))
        f_gd, gd = group_delay(f, s)
        self.assertArrayAlmostEqual(f_gd, np.linspace(1e9/(n-1), 1e9, n-1))
        self.assertArrayAlmostEqual(gd, np.full([n-1], -math.tau/1e9))


    def test_natural_sort(self):
        list = ['Hello', 'Number100', 'Number10', 'A']
        sorted_list = sorted(list, key=lambda s: natural_sort_key(s))
        self.assertListEqual(sorted_list, ['A', 'Hello', 'Number10', 'Number100'])


    def test_steps(self):

        self.assertAlmostEqual(get_next_1_2_5_10(0), 1)
        self.assertAlmostEqual(get_next_1_2_5_10(1), 2)
        self.assertAlmostEqual(get_next_1_2_5_10(3), 5)
        self.assertAlmostEqual(get_next_1_2_5_10(6), 10)
        self.assertAlmostEqual(get_next_1_2_5_10(9), 10)
        self.assertAlmostEqual(get_next_1_2_5_10(10), 20)

        self.assertAlmostEqual(get_next_1_3_10(0), 1)
        self.assertAlmostEqual(get_next_1_3_10(1), 3)
        self.assertAlmostEqual(get_next_1_3_10(5), 10)
        self.assertAlmostEqual(get_next_1_3_10(10), 30)
        self.assertAlmostEqual(get_next_1_3_10(99), 100)
        self.assertAlmostEqual(get_next_1_3_10(100), 300)

        self.assertAlmostEqual(get_next_1_10_100(0), 1)
        self.assertAlmostEqual(get_next_1_10_100(1), 10)
        self.assertAlmostEqual(get_next_1_10_100(5), 10)
        self.assertAlmostEqual(get_next_1_10_100(10), 100)
        self.assertAlmostEqual(get_next_1_10_100(99), 100)
        self.assertAlmostEqual(get_next_1_10_100(100), 1_000)


    def test_common_elements(self):
        self.assertTrue(any_common_elements([1,2,3],[3,4,5]))
        self.assertFalse(any_common_elements([1,2,3],[4,5,6]))
