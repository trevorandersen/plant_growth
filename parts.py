"""
parts.py - the parts that make up a plant.

INHERITANCE
    PlantPart                 the base class every part shares
    ├── Roots
    ├── Stem
    └── AttachedPart          parts that grow *on* the stem
        ├── Leaves
        ├── Flowers
        │   └── SunflowerHead     (a special kind of flower)
        └── Berries
            └── Strawberries      (a special kind of berry)

POLYMORPHISM
    A Plant never needs to know which kind of part it is holding. It just does

        for part in plant.parts():
            part.draw(surface, base, plant)

    and Python runs the right draw() for Roots, Stem, Leaves, and so on.
"""

import math
import random

import pygame


def mix_colour(a, b, t):
    """Blend colour a into colour b. t=0 gives a, t=1 gives b."""
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def leaf_shape(start, angle, length, width):
    """Points for a pointed oval (a leaf or a petal) that starts at `start`
    and points in direction `angle` (radians)."""
    ux, uy = math.cos(angle), math.sin(angle)  # along the leaf
    px, py = -uy, ux                           # across the leaf
    left, right = [], []
    for i in range(9):
        s = i / 8
        half_width = width / 2 * math.sin(math.pi * s) ** 0.8
        cx, cy = start[0] + ux * length * s, start[1] + uy * length * s
        left.append((cx + px * half_width, cy + py * half_width))
        right.append((cx - px * half_width, cy - py * half_width))
    return left + right[::-1]


# --------------------------------------------------------------------------
# Base class
# --------------------------------------------------------------------------

class PlantPart:
    """Base class for every part of a plant.

    Subclasses override is_present(), details() and draw().
    """

    name = "Part"

    def is_present(self):
        """Has this part started to grow yet?"""
        return False

    def details(self):
        """A short description of this part, e.g. '120 px tall'."""
        return ""

    def describe(self):
        # This method is NOT overridden. It works for every subclass because
        # it calls is_present() and details(), which ARE overridden.
        if self.is_present():
            return f"{self.name}: {self.details()}"
        return f"{self.name}: none"

    def draw(self, surface, base, plant):
        """Draw this part. `base` is the (x, y) point where the stem meets the soil."""
        raise NotImplementedError(f"{type(self).__name__} must override draw()")


# --------------------------------------------------------------------------
# Roots and stem
# --------------------------------------------------------------------------

class Roots(PlantPart):
    name = "Roots"

    def __init__(self):
        self.depth = 0          # how far down the roots reach (pixels)
        self.branches = 0       # number of side roots
        self.style = "tap"      # "tap" = one thick main root, "fibrous" = many thin roots
        self.colour = (225, 205, 165)

    def is_present(self):
        return self.depth > 0

    def details(self):
        return f"{self.style} roots, {self.depth:.0f} px deep, {self.branches} side roots"

    def draw(self, surface, base, plant):
        if not self.is_present():
            return
        x, y = base[0], base[1] + plant.seed_depth  # roots grow out of the seed
        rng = random.Random(42)  # same seed every frame, so the roots don't jiggle

        if self.style == "tap":
            # One thick, wiggly main root going straight down...
            main = [(x + 3 * math.sin(k * 1.3), y + self.depth * k / 10) for k in range(11)]
            pygame.draw.lines(surface, self.colour, False, main, 4)
            # ...with thinner side roots coming off it.
            for i in range(self.branches):
                f = (i + 1) / (self.branches + 1)
                sx, sy = main[round(f * 10)]
                side = 1 if i % 2 == 0 else -1
                length = 12 + (1 - f) * self.depth * 0.5 * (0.7 + 0.6 * rng.random())
                end = (sx + side * length, sy + length * 0.45)
                mid = ((sx + end[0]) / 2, (sy + end[1]) / 2 - 4)
                pygame.draw.lines(surface, self.colour, False, [(sx, sy), mid, end], 2)
        else:
            # Lots of thin roots fanning out from the seed.
            for i in range(self.branches):
                spread = (i / max(1, self.branches - 1)) - 0.5 if self.branches > 1 else 0
                angle = math.radians(90 + spread * 140)  # 90 degrees = straight down
                length = self.depth * (0.55 + 0.45 * rng.random())
                points = [(x, y)]
                for k in range(1, 5):
                    wobble = rng.uniform(-6, 6)
                    points.append((x + math.cos(angle) * length * k / 4 + wobble,
                                   y + math.sin(angle) * length * k / 4))
                pygame.draw.lines(surface, self.colour, False, points, 2)


class Stem(PlantPart):
    name = "Stem"

    def __init__(self):
        self.height = 0             # height of the main stem (pixels)
        self.thickness = 2
        self.branches = 0           # side branches growing off the main stem
        self.branch_angle = 45      # degrees away from straight up
        self.branch_fan = 0         # extra degrees for each pair of branches
        self.branch_length = 0.45   # as a fraction of the main stem's height
        self.branch_start = 0.35    # where the lowest branch joins (0 = ground, 1 = top)
        self.branch_end = 0.8       # where the highest branch joins
        self.woody = False          # woody stems are brown bark, not green
        self.colour = (75, 150, 60)
        self.bark_colour = (120, 85, 55)

    def is_present(self):
        return self.height > 0

    def details(self):
        kind = "woody" if self.woody else "green"
        text = f"{kind}, {self.height:.0f} px tall"
        if self.branches:
            text += f", {self.branches} branches"
        return text

    def segments(self, base):
        """The stem as a list of straight lines ((x1, y1), (x2, y2)).
        segments[0] is the main stem; the rest are branches."""
        if not self.is_present():
            return []
        x, y = base
        segs = [((x, y), (x, y - self.height))]
        for i in range(self.branches):
            f = self.branch_start
            if self.branches > 1:
                f += (self.branch_end - self.branch_start) * i / (self.branches - 1)
            start = (x, y - self.height * f)
            side = 1 if i % 2 == 0 else -1
            angle = math.radians(self.branch_angle + self.branch_fan * (i // 2))
            length = self.height * self.branch_length * (1 - 0.4 * f)
            end = (start[0] + side * math.sin(angle) * length,
                   start[1] - math.cos(angle) * length)
            segs.append((start, end))
        return segs

    def attachment_points(self, base, count, low, high):
        """Spread `count` points over the stem and its branches, between
        fraction `low` and `high` of the way along each one.
        Returns a list of (point, direction, side) tuples."""
        segs = self.segments(base)
        if not segs or count <= 0:
            return []
        per_segment = math.ceil(count / len(segs))
        points = []
        for i in range(count):
            (x1, y1), (x2, y2) = segs[i % len(segs)]
            k = i // len(segs)
            t = high if per_segment == 1 else low + (high - low) * k / (per_segment - 1)
            length = math.hypot(x2 - x1, y2 - y1) or 1
            direction = ((x2 - x1) / length, (y2 - y1) / length)
            side = 1 if (k + i % len(segs)) % 2 == 0 else -1
            points.append(((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t), direction, side))
        return points

    def draw(self, surface, base, plant):
        colour = self.bark_colour if self.woody else self.colour
        for n, (start, end) in enumerate(self.segments(base)):
            width = self.thickness if n == 0 else max(2, round(self.thickness * 0.6))
            pygame.draw.line(surface, colour, start, end, width)
            pygame.draw.circle(surface, colour, end, width // 2)


# --------------------------------------------------------------------------
# Parts that grow on the stem
# --------------------------------------------------------------------------

class AttachedPart(PlantPart):
    """A part that grows on the stem: leaves, flowers or berries.

    Adds a count and a size, and a `zone`: how far along each stem
    segment these parts grow (0 = bottom, 1 = tip).
    """

    zone = (0.2, 0.95)

    def __init__(self):
        self.count = 0
        self.size = 0

    def is_present(self):
        return self.count > 0 and self.size > 0

    def places(self, base, plant):
        return plant.stem.attachment_points(base, self.count, *self.zone)


class Leaves(AttachedPart):
    name = "Leaves"
    zone = (0.15, 0.9)

    def __init__(self):
        super().__init__()          # gives us self.count and self.size
        self.width = 0.5            # leaf width as a fraction of its length
        self.leaflets = 1           # 3 for a strawberry-style leaf
        self.colour = (60, 160, 70)

    def details(self):
        return f"{self.count} leaves, {self.size:.0f} px long"

    def draw(self, surface, base, plant):
        if not self.is_present():
            return
        vein = mix_colour(self.colour, (255, 255, 255), 0.35)
        for point, (dx, dy), side in self.places(base, plant):
            angle = math.atan2(dy, dx) + side * math.radians(60)
            if self.leaflets == 1:
                spread = [0]
            else:
                spread = [math.radians(d) for d in (-40, 0, 40)]
            for offset in spread:
                length = self.size if offset == 0 else self.size * 0.8
                shape = leaf_shape(point, angle + offset, length, length * self.width)
                pygame.draw.polygon(surface, self.colour, shape)
                tip = shape[8]
                pygame.draw.line(surface, vein, point, tip, 1)


class Flowers(AttachedPart):
    name = "Flowers"
    zone = (0.8, 1.0)

    def __init__(self):
        super().__init__()
        self.bloom = 0.0                    # 0 = closed bud, 1 = fully open
        self.petals = 5
        self.petal_colour = (255, 255, 255)
        self.centre_colour = (250, 210, 40)
        self.centre = 0.3                   # centre size as a fraction of the flower

    def details(self):
        s = "" if self.count == 1 else "s"
        if self.bloom <= 0:
            return f"{self.count} bud{s}"
        return f"{self.count} flower{s}, {self.bloom:.0%} open"

    def draw(self, surface, base, plant):
        if not self.is_present():
            return
        for point, _, _ in self.places(base, plant):
            if self.bloom <= 0:
                self.draw_bud(surface, point)
            else:
                self.draw_flower(surface, point, self.size * (0.4 + 0.6 * self.bloom))

    def draw_bud(self, surface, centre):
        r = max(3, self.size * 0.25)
        pygame.draw.circle(surface, (90, 150, 60), centre, r)
        pygame.draw.circle(surface, self.petal_colour, (centre[0], centre[1] - r * 0.4), r * 0.5)

    def draw_flower(self, surface, centre, radius):
        petal_width = min(radius * 0.8, 2 * math.pi * radius / self.petals)
        edge = mix_colour(self.petal_colour, (0, 0, 0), 0.15)
        for k in range(self.petals):
            angle = 2 * math.pi * k / self.petals
            shape = leaf_shape(centre, angle, radius, petal_width)
            pygame.draw.polygon(surface, self.petal_colour, shape)
            pygame.draw.polygon(surface, edge, shape, 1)
        pygame.draw.circle(surface, self.centre_colour, centre, max(2, radius * self.centre))


class SunflowerHead(Flowers):
    """A flower with lots of petals and a seed-packed centre."""

    def __init__(self):
        super().__init__()
        self.petals = 22
        self.petal_colour = (255, 200, 20)
        self.centre_colour = (95, 60, 30)
        self.centre = 0.45

    def draw_flower(self, surface, centre, radius):
        super().draw_flower(surface, centre, radius)  # draw it like any flower...
        # ...then add the spiral of seeds you see in a real sunflower.
        golden_angle = math.pi * (3 - math.sqrt(5))
        seeds = int(60 * self.bloom)
        for n in range(seeds):
            r = radius * self.centre * 0.9 * math.sqrt(n / max(1, seeds))
            a = n * golden_angle
            pygame.draw.circle(surface, (60, 38, 20),
                               (centre[0] + r * math.cos(a), centre[1] + r * math.sin(a)), 1.5)


class Berries(AttachedPart):
    name = "Berries"
    zone = (0.55, 1.0)

    def __init__(self):
        super().__init__()
        self.ripeness = 0.0                 # 0 = unripe, 1 = ripe
        self.unripe_colour = (120, 180, 70)
        self.ripe_colour = (200, 30, 40)

    def details(self):
        return f"{self.count} berries, {self.ripeness:.0%} ripe"

    def draw(self, surface, base, plant):
        if not self.is_present():
            return
        colour = mix_colour(self.unripe_colour, self.ripe_colour, self.ripeness)
        for i, (point, _, side) in enumerate(self.places(base, plant)):
            # Each berry hangs a little below the stem on a short stalk.
            hang = (point[0] + side * (3 + (i * 7) % 9),
                    point[1] + self.size + 4 + (i * 5) % 7)
            pygame.draw.line(surface, (80, 120, 50), point, hang, 1)
            self.draw_berry(surface, hang, colour)

    def draw_berry(self, surface, centre, colour):
        pygame.draw.circle(surface, colour, centre, self.size)
        shine = mix_colour(colour, (255, 255, 255), 0.5)
        pygame.draw.circle(surface, shine,
                           (centre[0] - self.size * 0.35, centre[1] - self.size * 0.35),
                           max(1, self.size * 0.25))


class Strawberries(Berries):
    """Strawberries are a cone shape with seeds on the outside."""

    def __init__(self):
        super().__init__()
        self.unripe_colour = (235, 240, 200)
        self.ripe_colour = (220, 30, 45)

    def details(self):
        return f"{self.count} strawberries, {self.ripeness:.0%} ripe"

    def draw_berry(self, surface, centre, colour):
        # Only the shape changes; Berries.draw() still decides where each one goes.
        x, y, s = centre[0], centre[1], self.size
        body = [(x - s, y - s * 0.6), (x + s, y - s * 0.6),
                (x + s * 0.7, y + s * 0.4), (x, y + s * 1.4), (x - s * 0.7, y + s * 0.4)]
        pygame.draw.polygon(surface, colour, body)
        for sx, sy in ((-0.4, -0.2), (0.4, -0.2), (0, 0.2), (-0.3, 0.6), (0.3, 0.6), (0, 1.0)):
            pygame.draw.circle(surface, (250, 225, 120), (x + sx * s, y + sy * s), 1)
        calyx = [(x - s, y - s * 0.8), (x, y - s * 0.4), (x + s, y - s * 0.8), (x, y - s * 1.1)]
        pygame.draw.polygon(surface, (60, 140, 50), calyx)
