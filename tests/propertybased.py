import sys
import time
import random

HEAVY = "--heavy" in sys.argv
TIME_PER_TEST = 300 if HEAVY else 3
 
print(f"Mode {'lourd (--heavy)' if HEAVY else 'rapide'} — {TIME_PER_TEST}s par test")
 
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


### Example
import math


def get_dist(a, b):
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))


def addition():
    x = random.randrange(0, 10000)
    y = random.randrange(0, 10000)
    z = random.randrange(0, 10000)

    # Exercice:    Tester les additions
    assert x + y == y + x, \
        f"Commutativité échouée : {x} + {y} != {y} + {x}"
 
    # Associativité : le groupement des opérandes ne change pas le résultat
    assert (x + y) + z == x + (y + z), \
        f"Associativité échouée : ({x}+{y})+{z} != {x}+({y}+{z})"
 
    # Élément neutre : ajouter 0 ne change pas la valeur
    assert x + 0 == x, \
        f"Élément neutre échoué : {x} + 0 != {x}"
 
    # Opposé : x + (-x) doit valoir 0
    assert x + (-x) == 0, \
        f"Opposé échoué : {x} + ({-x}) != 0"


def distance():
    x1 = random.randrange(-100, 100)
    y1 = random.randrange(-100, 100)
    z1 = random.randrange(-100, 100)
    a = (x1, y1, z1)

    x2 = random.randrange(-100, 100)
    y2 = random.randrange(-100, 100)
    z2 = random.randrange(-100, 100)
    b = (x2, y2, z2)

    # Exercice:     Tester la distance entre le point A et le point B
    x3 = random.randrange(-100, 100)
    y3 = random.randrange(-100, 100)
    z3 = random.randrange(-100, 100)
    c = (x3, y3, z3)
 
    d_ab = get_dist(a, b)
    d_ba = get_dist(b, a)
    d_aa = get_dist(a, a)
    d_bc = get_dist(b, c)
    d_ac = get_dist(a, c)
 
    # Non-négativité : une distance ne peut pas être négative
    assert d_ab >= 0, \
        f"Distance négative : d({a},{b}) = {d_ab}"
 
    # Identité : la distance d'un point à lui-même est 0
    assert d_aa == 0.0, \
        f"Identité échouée : d({a},{a}) = {d_aa} (attendu 0)"
 
    # Symétrie : d(A,B) == d(B,A), tolérance epsilon pour les flottants
    assert abs(d_ab - d_ba) < 1e-9, \
        f"Symétrie échouée : d(A,B)={d_ab} != d(B,A)={d_ba}"
 
    # Inégalité triangulaire : le chemin direct est toujours <= chemin indirect
    assert d_ac <= d_ab + d_bc + 1e-9, \
        f"Inégalité triangulaire : d(A,C)={d_ac} > d(A,B)+d(B,C)={d_ab+d_bc}"



create_property_based_test(addition, time_test=TIME_PER_TEST)
create_property_based_test(distance, regressions=[4480881574280375424], time_test=TIME_PER_TEST)
print("Tous les property-based tests OK ✓")