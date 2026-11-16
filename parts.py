"""
parts.py - the parts that make up a plant.

Roots is plural on purpose: one Roots object is the whole root system.
Leaf, Flower and Berry are singular: each object is ONE leaf, flower or
berry, and a plant keeps a list of them.

INHERITANCE
    PlantPart                 the base class every part shares
    ├── Roots
    ├── Stem
    └── AttachedPart          one thing that grows at a spot on the stem
        ├── Leaf
        ├── Flower
        │   └── SunflowerHead     (a special kind of Flower)
        └── Berry
            └── StrawberryFruit   (a special kind of Berry)

POLYMORPHISM
    A Plant never needs to know which kind of part it is holding:

        for part in plant.parts():
            part.draw(surface, base, plant)

    Python runs the right draw() for Roots, Stem, Leaf, Flower, Berry, ...
    In the same way, every leaf, flower and berry has its own grow().
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

    Subclasses override is_present(), details(), grow() and draw().
    """

    def is_present(self):
        """Has this part started to grow yet?"""
        return True

    def details(self):
        """A short description of this part, e.g. '120 px tall'."""
        return ""

    def describe(self):
        # This method is NOT overridden. It works for every subclass because
        # it calls is_present() and details(), which ARE overridden.
        if self.is_present():
            return self.details()
        return "not grown yet"

    def grow(self):
        """Grow a little. Called once per step. By default, nothing happens."""

    def draw(self, surface, base, plant):
        """Draw this part. `base` is the (x, y) point where the stem meets the soil."""
        raise NotImplementedError(f"{type(self).__name__} must override draw()")


# --------------------------------------------------------------------------
# Roots and stem: one of each per plant
# --------------------------------------------------------------------------

class Roots(PlantPart):
    """The whole root system of a plant."""

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
    """The main stem and its side branches."""

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

    def spot_for(self, index, low, high):
        """Choose where the index-th leaf (or flower) grows.

        Returns (segment, t, side): which stem segment, how far along it
        (0 = bottom, 1 = tip, kept between low and high) and which side.
        """
        segment_count = 1 + self.branches
        segment = index % segment_count        # take turns between the segments
        k = index // segment_count             # parts already on this segment
        t = high - (high - low) * ((k * 0.382) % 1)   # 0.382 spreads them out evenly
        side = 1 if index % 2 == 0 else -1
        return segment, t, side

    def place(self, base, spot):
        """Turn a spot into ((x, y), direction of the stem there, side)."""
        segs = self.segments(base)
        if not segs or spot is None:
            return None
        segment, t, side = spot
        (x1, y1), (x2, y2) = segs[min(segment, len(segs) - 1)]
        length = math.hypot(x2 - x1, y2 - y1) or 1
        direction = ((x2 - x1) / length, (y2 - y1) / length)
        return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t), direction, side

    def draw(self, surface, base, plant):
        colour = self.bark_colour if self.woody else self.colour
        for n, (start, end) in enumerate(self.segments(base)):
            width = self.thickness if n == 0 else max(2, round(self.thickness * 0.6))
            pygame.draw.line(surface, colour, start, end, width)
            pygame.draw.circle(surface, colour, end, width // 2)


# --------------------------------------------------------------------------
# One leaf, one flower, one berry
# --------------------------------------------------------------------------

class AttachedPart(PlantPart):
    """One thing that grows at a spot on the stem: a Leaf, Flower or Berry.

    `zone` says how far along a stem segment it may grow (0 = bottom, 1 = tip).
    The plant sets `spot` when it attaches the part.
    """

    zone = (0.2, 0.95)

    def __init__(self):
        self.spot = None
        self.age = 0            # steps since this part appeared

    def grow(self):
        self.age += 1

    def position(self, base, plant):
        """Where this part is right now: ((x, y), stem direction, side), or None."""
        return plant.stem.place(base, self.spot)


class Leaf(AttachedPart):
    zone = (0.15, 0.9)

    def __init__(self, full_size=30, width=0.5, leaflets=1, colour=(60, 160, 70)):
        super().__init__()          # gives us self.spot and self.age
        self.full_size = full_size  # length when fully grown (pixels)
        self.growth = 1 / 3         # 0 = nothing, 1 = full size
        self.width = width          # leaf width as a fraction of its length
        self.leaflets = leaflets    # 3 for a strawberry-style leaf
        self.colour = colour

    def size(self):
        return self.full_size * self.growth

    def grow(self):
        super().grow()                               # get one step older...
        self.growth = min(1.0, self.growth + 1 / 3)  # ...and a bit bigger

    def details(self):
        return f"{self.size():.0f} px long"

    def draw(self, surface, base, plant):
        where = self.position(base, plant)
        if where is None:
            return
        point, (dx, dy), side = where
        angle = math.atan2(dy, dx) + side * math.radians(60)
        vein = mix_colour(self.colour, (255, 255, 255), 0.35)
        offsets = [0] if self.leaflets == 1 else [math.radians(d) for d in (-40, 0, 40)]
        for offset in offsets:
            length = self.size() if offset == 0 else self.size() * 0.8
            shape = leaf_shape(point, angle + offset, length, length * self.width)
            pygame.draw.polygon(surface, self.colour, shape)
            pygame.draw.line(surface, vein, point, shape[8], 1)


class Flower(AttachedPart):
    zone = (0.8, 1.0)

    def __init__(self, size=12, petals=5, petal_colour=(255, 255, 255),
                 centre_colour=(250, 210, 40), centre=0.3, open_steps=2):
        super().__init__()
        self.size = size
        self.petals = petals
        self.petal_colour = petal_colour
        self.centre_colour = centre_colour
        self.centre = centre            # centre size as a fraction of the flower
        self.open_steps = open_steps    # steps to go from bud to fully open
        self.bloom = 0.0                # 0 = closed bud, 1 = fully open

    def grow(self):
        super().grow()
        self.bloom = min(1.0, self.bloom + 1 / self.open_steps)

    def is_finished(self):
        """Has this flower been fully open for a step? Then it can become a berry."""
        return self.age > self.open_steps

    def details(self):
        if self.bloom <= 0:
            return "bud"
        if self.bloom >= 1:
            return "open"
        return f"{self.bloom:.0%} open"

    def draw(self, surface, base, plant):
        where = self.position(base, plant)
        if where is None:
            return
        point = where[0]
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


class SunflowerHead(Flower):
    """A huge flower with lots of petals and a seed-packed centre."""

    def __init__(self):
        super().__init__(size=50, petals=22, petal_colour=(255, 200, 20),
                         centre_colour=(95, 60, 30), centre=0.45)

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


class Berry(AttachedPart):
    """A berry grows in the spot where a flower was."""

    def __init__(self, full_size=8, unripe_colour=(120, 180, 70),
                 ripe_colour=(200, 30, 40), ripen_steps=2):
        super().__init__()
        self.full_size = full_size
        self.growth = 0.5               # 0 = nothing, 1 = full size
        self.unripe_colour = unripe_colour
        self.ripe_colour = ripe_colour
        self.ripen_steps = ripen_steps  # steps to go from unripe to ripe
        self.ripeness = 0.0             # 0 = unripe, 1 = ripe
        self.hang = (random.uniform(3, 11), random.uniform(4, 10))  # each berry hangs a bit differently

    def size(self):
        return self.full_size * self.growth

    def grow(self):
        super().grow()
        self.growth = min(1.0, self.growth + 0.25)
        self.ripeness = min(1.0, self.ripeness + 1 / self.ripen_steps)

    def details(self):
        return f"{self.size():.0f} px, {self.ripeness:.0%} ripe"

    def draw(self, surface, base, plant):
        where = self.position(base, plant)
        if where is None:
            return
        point, _, side = where
        # The berry hangs a little below the stem on a short stalk.
        centre = (point[0] + side * self.hang[0], point[1] + self.size() + self.hang[1])
        pygame.draw.line(surface, (80, 120, 50), point, centre, 1)
        self.draw_berry(surface, centre, mix_colour(self.unripe_colour, self.ripe_colour, self.ripeness))

    def draw_berry(self, surface, centre, colour):
        s = self.size()
        pygame.draw.circle(surface, colour, centre, s)
        shine = mix_colour(colour, (255, 255, 255), 0.5)
        pygame.draw.circle(surface, shine, (centre[0] - s * 0.35, centre[1] - s * 0.35), max(1, s * 0.25))


class StrawberryFruit(Berry):
    """A strawberry: a cone shape with seeds on the outside."""

    def __init__(self):
        super().__init__(full_size=11, unripe_colour=(235, 240, 200), ripe_colour=(220, 30, 45))

    def draw_berry(self, surface, centre, colour):
        # Only the shape changes; Berry.draw() still decides where it hangs.
        x, y, s = centre[0], centre[1], self.size()
        body = [(x - s, y - s * 0.6), (x + s, y - s * 0.6),
                (x + s * 0.7, y + s * 0.4), (x, y + s * 1.4), (x - s * 0.7, y + s * 0.4)]
        pygame.draw.polygon(surface, colour, body)
        for sx, sy in ((-0.4, -0.2), (0.4, -0.2), (0, 0.2), (-0.3, 0.6), (0.3, 0.6), (0, 1.0)):
            pygame.draw.circle(surface, (250, 225, 120), (x + sx * s, y + sy * s), 1)
        calyx = [(x - s, y - s * 0.8), (x, y - s * 0.4), (x + s, y - s * 0.8), (x, y - s * 1.1)]
        pygame.draw.polygon(surface, (60, 140, 50), calyx)
