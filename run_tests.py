import sys
import cProfile
import unittest
import pstats


def runtests():
    suite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner().run(suite)
 
if __name__ == '__main__':
    if len(sys.argv) > 1:
        cProfile.run('runtests()', sort='cumtime')
    else:
        runtests()
