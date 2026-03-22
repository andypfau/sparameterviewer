import unittest
import pathlib
import numpy as np
import numbers



class MyTestCase(unittest.TestCase):


    def __init__(self, methodName: str = ...) -> None:
        self.plot_count = 0
        super().__init__(methodName)


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
            is_numeric = isinstance(a.dtype, numbers.Number) and isinstance(b.dtype, numbers.Number)
            if is_numeric:
                idx = np.unravel_index(np.argmax(np.abs(a-b)), a.shape)
                self.fail(f'Arrays are not almost equal (biggest difference is index {idx}, {a[idx]} != {b[idx]})')
            else:
                idx = np.unravel_index(np.argmax(a != b), a.shape)
                self.fail(f'Arrays are not equal (first different index is {idx}, {a[idx]} != {b[idx]})')
    

    def assertArrayAlmostEqual(self, a, b, rtol=1e-5, atol=1e-8):
        a, b = np.array(a), np.array(b)
        if a.shape != b.shape:
            self.fail(f'Arrays are not almost equal (array shapes differ, {a.shape} != {b.shape})')
        if not np.all(np.isclose(a, b, rtol=rtol, atol=atol)):
            idx = np.unravel_index(np.argmax(np.abs(a-b)), a.shape)
            self.fail(f'Arrays are not almost equal (biggest difference is index {idx}, {a[idx]} != {b[idx]})')
