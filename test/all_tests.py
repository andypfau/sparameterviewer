import sys, os
sys.path.extend([os.path.abspath('../src'), os.path.abspath('./src')])

import unittest



if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)
