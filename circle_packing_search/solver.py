"""A bounded DFS for corner-generated circle packings in the unit disk."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


BOUNDARY = -1


@dataclass(frozen=True)
class Circle:
    denominator: int
    x: float
    y: float

    @property
    def radius(self) -> float:
        return 1.0 / self.denominator


@dataclass
class SearchResult:
    status: str
    circles: tuple[Circle, ...] | None
    nodes: int
    max_depth: int
    reason: str


class Solver:
    """Search the finite prefix of the corner-insertion tree.

    An oriented contact ``(a, b)`` denotes the side to the left of the vector
    from support center ``a`` to support center ``b``.  Reversing the pair
    denotes the other side.
    """

    def __init__(
        self,
        denominators: Iterable[int],
        *,
        max_circles: int | None = None,
        node_limit: int = 100_000,
        tolerance: float = 1e-9,
    ) -> None:
        values = tuple(sorted(set(denominators)))
        if not values or any(not isinstance(n, int) or isinstance(n, bool) or n < 2
                             for n in values):
            raise ValueError("denominators must be a nonempty set of integers >= 2")
        if node_limit < 1:
            raise ValueError("node_limit must be positive")
        area_bound = max(values) ** 2
        if max_circles is None:
            max_circles = area_bound
        if max_circles < len(values):
            raise ValueError("max_circles must allow every denominator to occur")

        self.denominators = values
        self.max_circles = min(max_circles, area_bound)
        self.node_limit = node_limit
        self.tol = tolerance
        self.nodes = 0
        self.max_depth = 0
        self._seen: set[tuple[tuple[int, int, int], ...]] = set()
        self._interrupted = False

    def solve(self) -> SearchResult:
        # Even one copy of each requested circle cannot fit if their total area
        # exceeds that of the container.
        if sum(1.0 / (n * n) for n in self.denominators) > 1.0 + self.tol:
            return SearchResult("exhausted", None, 0, 0,
                                "required circles fail the area bound")

        for denominator in self.denominators:
            radius = 1.0 / denominator
            seed = (Circle(denominator, 1.0 - radius, 0.0),)
            answer = self._dfs(seed)
            if answer is not None:
                return SearchResult("found", answer, self.nodes, self.max_depth,
                                    "local holding condition certified numerically")
            if self._interrupted:
                return SearchResult("node_limit", None, self.nodes, self.max_depth,
                                    "node limit reached")
        return SearchResult("exhausted", None, self.nodes, self.max_depth,
                            "bounded corner-generated search exhausted")

    def _dfs(self, circles: tuple[Circle, ...]) -> tuple[Circle, ...] | None:
        if self.nodes >= self.node_limit:
            self._interrupted = True
            return None
        key = self._state_key(circles)
        if key in self._seen:
            return None
        self._seen.add(key)
        self.nodes += 1
        self.max_depth = max(self.max_depth, len(circles))

        contacts = self.contacts(circles)
        if self.is_victory(circles, contacts):
            return circles
        if len(circles) >= self.max_circles:
            return None

        missing = set(self.denominators) - {circle.denominator for circle in circles}
        actions: list[tuple[int, int, int, Circle]] = []
        for a, b in self.oriented_corners(circles, contacts):
            for denominator in self.denominators:
                candidate = self.place_at_corner(circles, a, b, denominator)
                if candidate is None:
                    continue
                trial = circles + (candidate,)
                new_degree = len(self.contacts(trial)[len(circles)])
                actions.append((denominator not in missing, -new_degree,
                                denominator, candidate))

        # Try missing radii and immediately high-contact placements first.
        actions.sort(key=lambda item: item[:3])
        emitted: set[tuple[int, int, int]] = set()
        for _, _, _, candidate in actions:
            candidate_key = self._circle_key(candidate)
            if candidate_key in emitted:
                continue
            emitted.add(candidate_key)
            answer = self._dfs(circles + (candidate,))
            if answer is not None or self._interrupted:
                return answer
        return None

    def contacts(self, circles: tuple[Circle, ...]) -> tuple[frozenset[int], ...]:
        result = [set() for _ in circles]
        for i, circle in enumerate(circles):
            if abs(math.hypot(circle.x, circle.y) - (1.0 - circle.radius)) <= self.tol:
                result[i].add(BOUNDARY)
            for j in range(i):
                other = circles[j]
                target = circle.radius + other.radius
                if abs(math.hypot(circle.x - other.x, circle.y - other.y) - target) <= self.tol:
                    result[i].add(j)
                    result[j].add(i)
        return tuple(frozenset(neighbors) for neighbors in result)

    def is_victory(
        self,
        circles: tuple[Circle, ...],
        contacts: tuple[frozenset[int], ...] | None = None,
    ) -> bool:
        if {circle.denominator for circle in circles} != set(self.denominators):
            return False
        contacts = contacts if contacts is not None else self.contacts(circles)
        return all(self.is_held(circles, index, contacts)
                   for index in range(len(circles)))

    def contact_angles(
        self,
        circles: tuple[Circle, ...],
        index: int,
        contacts: tuple[frozenset[int], ...] | None = None,
    ) -> tuple[float, ...]:
        contacts = contacts if contacts is not None else self.contacts(circles)
        circle = circles[index]
        angles = []
        for neighbor in contacts[index]:
            if neighbor == BOUNDARY:
                angle = math.atan2(circle.y, circle.x)
            else:
                other = circles[neighbor]
                angle = math.atan2(other.y - circle.y, other.x - circle.x)
            angles.append(angle % math.tau)
        return tuple(sorted(angles))

    def largest_contact_gap(
        self,
        circles: tuple[Circle, ...],
        index: int,
        contacts: tuple[frozenset[int], ...] | None = None,
    ) -> float:
        angles = self.contact_angles(circles, index, contacts)
        if len(angles) < 2:
            return math.tau
        gaps = [right - left for left, right in zip(angles, angles[1:])]
        gaps.append(angles[0] + math.tau - angles[-1])
        return max(gaps)

    def is_held(
        self,
        circles: tuple[Circle, ...],
        index: int,
        contacts: tuple[frozenset[int], ...] | None = None,
    ) -> bool:
        contacts = contacts if contacts is not None else self.contacts(circles)
        return (len(contacts[index]) >= 3
                and self.largest_contact_gap(circles, index, contacts)
                < math.pi - self.tol)

    def oriented_corners(
        self,
        circles: tuple[Circle, ...],
        contacts: tuple[frozenset[int], ...] | None = None,
    ) -> tuple[tuple[int, int], ...]:
        contacts = contacts if contacts is not None else self.contacts(circles)
        pairs: list[tuple[int, int]] = []
        for i, neighbors in enumerate(contacts):
            for neighbor in neighbors:
                if neighbor == BOUNDARY or neighbor < i:
                    pairs.append((neighbor, i))
                    pairs.append((i, neighbor))
        return tuple(pairs)

    def place_at_corner(
        self,
        circles: tuple[Circle, ...],
        a: int,
        b: int,
        denominator: int,
    ) -> Circle | None:
        radius = 1.0 / denominator
        ax, ay, da = self._support_geometry(circles, a, radius)
        bx, by, db = self._support_geometry(circles, b, radius)
        dx, dy = bx - ax, by - ay
        separation = math.hypot(dx, dy)
        if separation <= self.tol:
            return None
        along = (da * da - db * db + separation * separation) / (2.0 * separation)
        height_sq = da * da - along * along
        if height_sq < -self.tol:
            return None
        height = math.sqrt(max(0.0, height_sq))
        ux, uy = dx / separation, dy / separation
        # Positive perpendicular is the left side of oriented support a -> b.
        x = ax + along * ux - height * uy
        y = ay + along * uy + height * ux
        candidate = Circle(denominator, x, y)
        if not self._is_legal(circles, candidate):
            return None
        return candidate

    def _support_geometry(
        self, circles: tuple[Circle, ...], support: int, new_radius: float
    ) -> tuple[float, float, float]:
        if support == BOUNDARY:
            return 0.0, 0.0, 1.0 - new_radius
        circle = circles[support]
        return circle.x, circle.y, circle.radius + new_radius

    def _is_legal(self, circles: tuple[Circle, ...], candidate: Circle) -> bool:
        if math.hypot(candidate.x, candidate.y) > 1.0 - candidate.radius + self.tol:
            return False
        for circle in circles:
            distance = math.hypot(candidate.x - circle.x, candidate.y - circle.y)
            if distance < candidate.radius + circle.radius - self.tol:
                return False
        return True

    def _circle_key(self, circle: Circle) -> tuple[int, int, int]:
        quantum = max(self.tol * 8.0, 1e-12)
        return (circle.denominator, round(circle.x / quantum), round(circle.y / quantum))

    def _state_key(self, circles: tuple[Circle, ...]) -> tuple[tuple[int, int, int], ...]:
        return tuple(sorted(self._circle_key(circle) for circle in circles))
