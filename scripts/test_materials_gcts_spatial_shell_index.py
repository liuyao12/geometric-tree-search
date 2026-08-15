import math
import random
import unittest

from materials_gcts_port_cover_graph import _SpatialShellIndex


class SpatialShellIndexTest(unittest.TestCase):
    def test_exact_shell_queries_match_brute_force(self):
        generator = random.Random(401844)
        points = tuple((generator.uniform(-8, 8),
                        generator.uniform(-8, 8),
                        generator.uniform(-8, 8)) for _ in range(1200))
        index = _SpatialShellIndex(points)
        for center in points[::137]:
            for radius in (1.5, 4.0, 8.0, 13.0):
                tolerance = .35
                expected = {item for item, point in enumerate(points)
                            if abs(math.dist(center, point) - radius) <=
                            tolerance}
                self.assertEqual(
                    set(index.shell(center, radius, tolerance)), expected)


if __name__ == "__main__":
    unittest.main()
