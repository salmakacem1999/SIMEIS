import sys
import time
import random
import math

HEAVY = "--heavy" in sys.argv
TIME_PER_TEST = 300 if HEAVY else 3

print(f"Mode {'lourd' if HEAVY else 'rapide'} - {TIME_PER_TEST}s par test")

def create_property_based_test(f, regressions=[], time_test=10):
    tstart = time.time()
    i = 0
    while (time.time() - tstart) < time_test:
        if i < len(regressions):
            seed = regressions[i]
        else:
            seed = random.randrange(0, 2**64)
        random.seed(seed)
        try:
            f()
            print("Test", f.__name__, i, "OK")
        except AssertionError as err:
            print("Test", f.__name__, "failed with seed", seed)
            print(err)
            sys.exit(1)
        i += 1
    print(f"  -> {i} iterations in {time.time() - tstart:.1f}s")

def get_dist(a, b):
    return math.sqrt(((a[0]-b[0])**2) + ((a[1]-b[1])**2) + ((a[2]-b[2])**2))

def addition():
    x = random.randrange(0, 10000)
    y = random.randrange(0, 10000)
    z = random.randrange(0, 10000)
    assert x + y == y + x
    assert (x + y) + z == x + (y + z)
    assert x + 0 == x
    assert x + (-x) == 0

def distance():
    x1,y1,z1 = random.randrange(-100,100),random.randrange(-100,100),random.randrange(-100,100)
    x2,y2,z2 = random.randrange(-100,100),random.randrange(-100,100),random.randrange(-100,100)
    x3,y3,z3 = random.randrange(-100,100),random.randrange(-100,100),random.randrange(-100,100)
    a,b,c = (x1,y1,z1),(x2,y2,z2),(x3,y3,z3)
    assert get_dist(a,b) >= 0
    assert get_dist(a,a) == 0.0
    assert abs(get_dist(a,b) - get_dist(b,a)) < 1e-9
    assert get_dist(a,c) <= get_dist(a,b) + get_dist(b,c) + 1e-9

create_property_based_test(addition, time_test=TIME_PER_TEST)
create_property_based_test(distance, regressions=[4480881574280375424], time_test=TIME_PER_TEST)
print("All property-based tests OK")
