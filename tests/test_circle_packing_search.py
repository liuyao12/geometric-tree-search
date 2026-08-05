import math
import unittest

from circle_packing_search import Circle, Solver


class CirclePackingSearchTest(unittest.TestCase):
    def test_rejects_invalid_denominators(self) -> None:
        with self.assertRaises(ValueError):
            Solver([1, 3])

    def test_oriented_seed_corners_give_reflections(self) -> None:
        solver = Solver([3], max_circles=7)
        seed = (Circle(3, 2 / 3, 0),)
        upper = solver.place_at_corner(seed, -1, 0, 3)
        lower = solver.place_at_corner(seed, 0, -1, 3)
        self.assertIsNotNone(upper)
        self.assertIsNotNone(lower)
        assert upper is not None and lower is not None
        self.assertAlmostEqual(upper.x, lower.x)
        self.assertAlmostEqual(upper.y, -lower.y)
        self.assertGreater(upper.y, 0)

    def test_seven_thirds_configuration_is_a_victory(self) -> None:
        solver = Solver([3], max_circles=7)
        circles = [Circle(3, 0.0, 0.0)]
        circles.extend(
            Circle(3, (2 / 3) * math.cos(k * math.pi / 3),
                   (2 / 3) * math.sin(k * math.pi / 3))
            for k in range(6)
        )
        self.assertTrue(solver.is_victory(tuple(circles)))

    def test_search_finds_four_circle_thirds_configuration(self) -> None:
        result = Solver([3], max_circles=7, node_limit=20_000).solve()
        self.assertEqual(result.status, "found")
        self.assertEqual(len(result.circles or ()), 4)
        self.assertTrue(result.circles is not None)
        assert result.circles is not None
        self.assertTrue(all(len(c) >= 3 for c in Solver([3]).contacts(result.circles)))


if __name__ == "__main__":
    unittest.main()
