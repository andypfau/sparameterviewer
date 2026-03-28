from testlib import MyTestCase
from lib import Lock



class TestAsync(MyTestCase):


    def test_lock_simple(self):
        lock = Lock()
        
        with self.subTest():
            self.assertFalse(lock.locked)
        
        with lock:
            with self.subTest():
                self.assertTrue(lock.locked)
            with lock:
                with self.subTest():
                    self.assertTrue(lock.locked)
            with self.subTest():
                self.assertTrue(lock.locked)
        
        with self.subTest():
            self.assertFalse(lock.locked)


    def test_lock_initiailized(self):
        lock = Lock(True)
        
        with self.subTest():
            self.assertTrue(lock.locked)
        
        lock.force_unlock()

        with self.subTest():
            self.assertFalse(lock.locked)
