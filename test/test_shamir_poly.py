import unittest

from ethsnarks.shamirspoly import lagrange, shamirs_poly
from ethsnarks.field import FQ
from ethsnarks.r1cs import r1cs_constraint

from scipy.interpolate import lagrange as scipy_lagrange


def unzip(x):
    return [_[0] for _ in x], [_[1] for _ in x]


class ShamirPolyTests(unittest.TestCase):
    def test_fromdocs(self):
        p = 100003
        k = 4
        a = [FQ(6257, p), FQ(85026, p), FQ(44499, p), FQ(14701, p)]
        F = lambda i, x: a[i] * (x**i)
        X = lambda x: a[0] + F(1, x) + F(2, x) + F(3, x)
        # Create the shares
        Sx = [_ for _ in range(1, 5)]
        Sy = [X(_) for _ in Sx]
        for x, y in zip(Sx, Sy):
            z = shamirs_poly(FQ(x, p), a)
            assert z == y
        # Then recover secret
        result = int(scipy_lagrange(Sx, [_.n for _ in Sy]).c[-1]) % p
        assert a[0] == result


    def test_fromdocs2(self):
        p = 100003
        k = 4
        a = [FQ.random(p) for _ in range(0, k)] # [6257, 85026, 44499, 14701]
        F = lambda i, x: a[i] * (x**i)
        X = lambda x: a[0] + F(1, x) + F(2, x) + F(3, x)
        # Create the shares
        Sx = range(1, 5)
        Sy = [X(_) for _ in Sx]
        for x, y in zip(Sx, Sy):
            z = shamirs_poly(FQ(x, p), a)
            assert z == y
        # Then recover secret
        result = int(scipy_lagrange(Sx, [_.n for _ in Sy]).c[-1]) % p
        assert a[0] == result

    def test_random(self):
        # Randomized tests
        for _ in range(0, 10):
            alpha = [FQ.random() for _ in range(0, 4)]
            points = [(FQ(i), shamirs_poly(FQ(i), alpha))
                      for i in range(0, len(alpha))]
            assert alpha[0] == lagrange(points, 0)
            assert alpha[0] != lagrange(points[1:], 0)
            assert alpha[0] != lagrange(points[2:], 0)

    def test_random_small(self):
        q = 100003
        for _ in range(0, 10):
            alpha = [FQ.random(q) for _ in range(0, 4)]
            points = [(FQ(i, q), shamirs_poly(FQ(i, q), alpha))
                      for i in range(0, len(alpha))]
            assert alpha[0] == lagrange(points, 0)
            assert alpha[0] != lagrange(points[1:], 0)
            assert alpha[0] != lagrange(points[2:], 0)

            # XXX: scipy's lagrange has floating point precision for large numbers
            points_x, points_y = unzip(points)
            interpolation = scipy_lagrange([_.n for _ in points_x], [_.n for _ in points_y])
            assert int(interpolation.c[-1]) == alpha[0]

    def test_static(self):
        # Verify against static test vectors
        alpha = [FQ(6808181831819141657160280673506432691407806061837762993142662373500430825792),
                 FQ(4138536697521448323155976179625860582331141320072618244300034508091478437877),
                 FQ(20259243729221075783953642258755031830946498253783650311586175820530608751936),
                 FQ(11227115470523445882235139084890542822660569362938710556861479160600812964997)]
        points = [(FQ(i), shamirs_poly(FQ(i), alpha)) for i in range(0, len(alpha))]
        test_points = [(FQ(0), FQ(6808181831819141657160280673506432691407806061837762993142662373500430825792)),
                       (FQ(1), FQ(20544834857245836424258632451520592838797650598216707762192147676147522484985)),
                       (FQ(2), FQ(10833210933219706719196668784844423052753721417299010433393634464005858464330)),
                       (FQ(3), FQ(1259517139202877390892412692306630092142705895884865660519589327528699562575))]
        assert points == test_points
        assert alpha[0] == lagrange(points, 0)

    def test_poly_constraints(self):        
        I = FQ(14107816444829002666153088737167870815199986768206359534115449255516606414458)

        A = [
            FQ(17167899297711346731111134130539302906398306115120667361324654931060817769652),
            FQ(20692971555607562002131076139518972969954851288604992618106076572794460197154),
            FQ(11669314840495787582492056085422064523948780040073924653117253046363337959489),
            FQ(15735493254427804666818698471807230275586165984790760178845725782084556556535)
        ]

        S = [
            FQ(1),
            FQ(14107816444829002666153088737167870815199986768206359534115449255516606414458),
            FQ(5067932324814081810415131337916762410698113547031307360925810907599032394672),
            FQ(13201723662860499519704937914604513230538757359894370890481138582074383924053)
        ]

        T = [
            FQ(17167899297711346731111134130539302906398306115120667361324654931060817769652),
            FQ(13947767308050706262790594447202101821284419559667543268525874072511409211876),
            FQ(12611939459072476081893406313696501745859572890147944797422704733972764295239),
            FQ(1657398546220101661314129991806057074896482894269175421846876999103942041527)
        ]

        result = shamirs_poly(I, A)
        assert result == T[-1]

        for i in range(0, len(A)):
            if i == 0:
                r1cs_constraint(1, S[i], 1)
            elif i == 1:
                r1cs_constraint(I, I, S[i+1])
            elif i < (len(A)-1):
                r1cs_constraint(I, S[i], S[i+1])

            if i == 0:
                r1cs_constraint(A[i], S[i], T[i])
            else:
                r1cs_constraint(A[i], S[i], (T[i] - T[i-1]))


if __name__ == "__main__":
    unittest.main()
