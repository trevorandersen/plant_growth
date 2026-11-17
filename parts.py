"""
Plant parts for the Plant Growth Simulator.

A plant has one Roots and one Stem. "Roots" is plural because one Roots
object is the whole root system.
Leaf, Flower and Berry are singular because each object is one leaf, flower
or berry, and a plant keeps a list of them.

Inheritance:
    PlantPart                 the base class every part shares
    ├── Roots                 the whole root system
    │   ├── TapRoots          one thick main root with side roots
    │   └── FibrousRoots      many thin roots
    ├── Stem
    └── AttachedPart          one thing that grows at a spot on the stem
        ├── Leaf
        ├── Flower
        │   └── SunflowerHead
        └── Berry
            └── StrawberryFruit

Polymorphism:
    A plant never needs to know which kind of part it is holding:

        for part in plant.get_parts():
            part.grow()
            part.draw(surface, base, plant)

    Python runs the right grow() and draw() for whatever class each part is.
    In the same way, str(part) uses that class's own __str__().
"""

import math
import random

import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUD_COLOUR = (90, 150, 60)
STALK_COLOUR = (80, 120, 50)
# Stepping by the golden fraction spreads things out evenly without them lining up
GOLDEN_FRACTION = (3 - math.sqrt(5)) / 2  # about 0.382
GOLDEN_ANGLE = 2 * math.pi * GOLDEN_FRACTION  # radians
ROOT_SHAPE_SEED = 42
TAP_ROOT_PIECES = 10
FIBROUS_ROOT_PIECES = 4
OUTLINE_STEPS = 8
LEAF_ANGLE = 60  # degrees away from the stem
LEAFLET_ANGLES = (-40, 0, 40)  # degrees away from the middle of the leaf
LEAF_GROWTH_PER_STEP = 1 / 3


def mix_colour(start_colour, end_colour, fraction):
    """Blend from start_colour (fraction 0) to end_colour (fraction 1)."""
    return tuple(round(start + (end - start) * fraction) for start, end in zip(start_colour, end_colour))


def calculate_leaf_outline(start, angle, length, width):
    """Calculate the points around a pointed oval, which is the shape of a leaf or a petal.

    The oval begins at the (x, y) point start and points in the direction angle (radians).
    """
    along_x, along_y = math.cos(angle), math.sin(angle)
    across_x, across_y = -along_y, along_x
    left_points = []
    right_points = []
    for i in range(OUTLINE_STEPS + 1):
        fraction = i / OUTLINE_STEPS
        # Widest in the middle, narrowing to a point at each end
        half_width = width / 2 * math.sin(math.pi * fraction) ** 0.8
        middle_x = start[0] + along_x * length * fraction
        middle_y = start[1] + along_y * length * fraction
        left_points.append((middle_x + across_x * half_width, middle_y + across_y * half_width))
        right_points.append((middle_x - across_x * half_width, middle_y - across_y * half_width))
    return left_points + right_points[::-1]


def format_branches(number_of_branches):
    """Format a number of branches as text, like "1 branch" or "3 branches"."""
    if number_of_branches == 1:
        return "1 branch"
    return f"{number_of_branches} branches"


class PlantPart:
    """Base class for every part of a plant.

    Subclasses override is_present(), __str__(), grow() and draw().
    """

    def is_present(self):
        """Determine if this part has started to grow."""
        return True

    def describe(self):
        """Describe this part as it is now, like "120 px tall" or "not grown yet"."""
        # This method is not overridden. It works for every subclass because
        # it calls is_present() and __str__(), which are overridden.
        if self.is_present():
            return str(self)
        return "not grown yet"

    def grow(self):
        """Grow for one step. A part stays the same unless its class overrides this."""

    def draw(self, surface, base, plant):
        """Draw this part of plant, where base is the (x, y) point at which the stem meets the soil."""
        raise NotImplementedError(f"{type(self).__name__} must override draw()")


class Roots(PlantPart):
    """The whole root system of a plant.

    TapRoots and FibrousRoots are the two kinds of Roots. Each one overrides
    draw_roots() to draw its own shape; everything else is shared.
    """

    def __init__(self):
        """Initialise Roots that have not started to grow."""
        self.depth = 0  # pixels
        self.number_of_branches = 0
        self.colour = (225, 205, 165)

    def __str__(self):
        """Return how deep the roots reach and how many branches they have."""
        return f"{self.depth:.0f} px deep, {format_branches(self.number_of_branches)}"

    def is_present(self):
        """Determine if the roots have started to grow."""
        return self.depth > 0

    def draw(self, surface, base, plant):
        """Draw the roots growing down out of the plant's seed."""
        if self.is_present():
            top = (base[0], base[1] + plant.seed_depth)
            # Start from the same seed every time so the roots do not jiggle between frames
            random_generator = random.Random(ROOT_SHAPE_SEED)
            self.draw_roots(surface, top, random_generator)

    def draw_roots(self, surface, top, random_generator):
        """Draw the shape of the roots, growing down from the (x, y) point top."""
        raise NotImplementedError(f"{type(self).__name__} must override draw_roots()")


class TapRoots(Roots):
    """Roots with one thick main root going straight down and thinner side roots."""

    def draw_roots(self, surface, top, random_generator):
        """Draw a wiggly main root with side roots branching off it."""
        x, y = top
        main_root = [(x + 3 * math.sin(i * 1.3), y + self.depth * i / TAP_ROOT_PIECES)
                     for i in range(TAP_ROOT_PIECES + 1)]
        pygame.draw.lines(surface, self.colour, False, main_root, 4)
        for i in range(self.number_of_branches):
            fraction = (i + 1) / (self.number_of_branches + 1)
            start_x, start_y = main_root[round(fraction * TAP_ROOT_PIECES)]
            # Side roots go right, left, right... and are shorter further down
            side = 1 if i % 2 == 0 else -1
            length = 12 + (1 - fraction) * self.depth * 0.5 * random_generator.uniform(0.7, 1.3)
            end = (start_x + side * length, start_y + length * 0.45)
            middle = ((start_x + end[0]) / 2, (start_y + end[1]) / 2 - 4)
            pygame.draw.lines(surface, self.colour, False, [(start_x, start_y), middle, end], 2)


class FibrousRoots(Roots):
    """Roots made of many thin roots that fan out from the seed."""

    def draw_roots(self, surface, top, random_generator):
        """Draw thin, wobbly roots fanning out from down-left to down-right."""
        x, y = top
        for i in range(self.number_of_branches):
            if self.number_of_branches > 1:
                spread = i / (self.number_of_branches - 1) - 0.5
            else:
                spread = 0
            angle = math.radians(90 + spread * 140)  # 90 degrees is straight down
            length = self.depth * random_generator.uniform(0.55, 1.0)
            points = [(x, y)]
            for j in range(1, FIBROUS_ROOT_PIECES + 1):
                distance = length * j / FIBROUS_ROOT_PIECES
                wobble = random_generator.uniform(-6, 6)
                points.append((x + math.cos(angle) * distance + wobble, y + math.sin(angle) * distance))
            pygame.draw.lines(surface, self.colour, False, points, 2)


class Stem(PlantPart):
    """The main stem of a plant and its side branches.

    The stem is made of straight segments. Segment 0 is the main stem and
    segments 1, 2, 3... are the branches.
    """

    def __init__(self):
        """Initialise a Stem that has not started to grow."""
        self.height = 0  # pixels, for the main stem only
        self.thickness = 2
        self.number_of_branches = 0
        self.branch_angle = 45  # degrees away from straight up
        # Each pair of branches leans out this many degrees more than the pair below it
        self.branch_fan = 0
        self.branch_length = 0.45  # as a fraction of the main stem's height
        # Branches join the main stem between these fractions of its height (0 is the ground)
        self.branch_start = 0.35
        self.branch_end = 0.8
        self.is_woody = False
        self.colour = (75, 150, 60)
        self.bark_colour = (120, 85, 55)

    def __str__(self):
        """Return the stem's kind and height, and how many branches it has if any."""
        kind = "woody" if self.is_woody else "green"
        description = f"{kind}, {self.height:.0f} px tall"
        if self.number_of_branches > 0:
            description += f", {format_branches(self.number_of_branches)}"
        return description

    def is_present(self):
        """Determine if the stem has started to grow."""
        return self.height > 0

    def calculate_segment(self, base, segment_index):
        """Calculate where one segment of the stem starts and ends, as ((x1, y1), (x2, y2))."""
        x, y = base
        if segment_index == 0:
            return (x, y), (x, y - self.height)
        branch_index = segment_index - 1
        join_fraction = self.branch_start
        if self.number_of_branches > 1:
            join_fraction += (self.branch_end - self.branch_start) * branch_index / (self.number_of_branches - 1)
        start = (x, y - self.height * join_fraction)
        # Branches go right, left, right... and are shorter higher up
        side = 1 if branch_index % 2 == 0 else -1
        angle = math.radians(self.branch_angle + self.branch_fan * (branch_index // 2))
        length = self.height * self.branch_length * (1 - 0.4 * join_fraction)
        end = (start[0] + side * math.sin(angle) * length, start[1] - math.cos(angle) * length)
        return start, end

    def calculate_segments(self, base):
        """Calculate every segment of the stem: the main stem, then each branch."""
        return [self.calculate_segment(base, i) for i in range(1 + self.number_of_branches)]

    def choose_spot(self, taken_spots, lowest, highest):
        """Choose the spot where a new leaf or flower will grow.

        taken_spots are the spots that the other leaves (or flowers) already have.
        A spot is (segment_index, fraction, side): which segment of the stem,
        how far along it (0 is the bottom, 1 is the tip) and which side (1 or -1).
        The fraction is kept between lowest and highest.
        """
        segment_counts = [0] * (1 + self.number_of_branches)
        for taken_segment_index, _, _ in taken_spots:
            segment_counts[taken_segment_index] += 1
        # Use the emptiest segment
        number_on_segment = min(segment_counts)
        segment_index = segment_counts.index(number_on_segment)
        # Start at the top of the zone, then spread the rest out below it
        fraction = highest - (highest - lowest) * (number_on_segment * GOLDEN_FRACTION % 1)
        # Swap sides along the segment
        side = 1 if (number_on_segment + segment_index) % 2 == 0 else -1
        return segment_index, fraction, side

    def calculate_position(self, base, spot):
        """Calculate where a spot is now, as ((x, y), direction of the stem there, side)."""
        segment_index, fraction, side = spot
        (x1, y1), (x2, y2) = self.calculate_segment(base, segment_index)
        # Avoid dividing by zero if the segment has no length yet
        length = max(1, math.hypot(x2 - x1, y2 - y1))
        direction = ((x2 - x1) / length, (y2 - y1) / length)
        point = (x1 + (x2 - x1) * fraction, y1 + (y2 - y1) * fraction)
        return point, direction, side

    def draw(self, surface, base, plant):
        """Draw the main stem and its branches, which are thinner."""
        if self.is_present():
            colour = self.bark_colour if self.is_woody else self.colour
            for i, (start, end) in enumerate(self.calculate_segments(base)):
                width = self.thickness if i == 0 else max(2, round(self.thickness * 0.6))
                pygame.draw.line(surface, colour, start, end, width)
                # Round off the end
                pygame.draw.circle(surface, colour, end, width // 2)


class AttachedPart(PlantPart):
    """One thing that grows at a spot on the stem: a Leaf, a Flower or a Berry.

    The plant sets spot when it attaches the part (see Stem.choose_spot).
    """

    def __init__(self, full_size, growth=1.0):
        """Initialise an AttachedPart that is not attached to a stem yet."""
        self.spot = None
        self.age = 0  # steps since this part appeared
        self.full_size = full_size  # pixels
        self.growth = growth  # 0 is nothing, 1 is full size

    def calculate_size(self):
        """Calculate how big this part is now, in pixels."""
        return self.full_size * self.growth

    def grow(self):
        """Get one step older."""
        self.age += 1

    def calculate_position(self, base, plant):
        """Calculate where this part is now, as ((x, y), direction of the stem there, side).

        Return None if the part has not been attached to the stem.
        """
        if self.spot is None:
            return None
        return plant.stem.calculate_position(base, self.spot)


class Leaf(AttachedPart):
    """One leaf, which may be divided into three leaflets."""

    def __init__(self, full_size=30, width=0.5, number_of_leaflets=1, colour=(60, 160, 70), zone=(0.15, 0.9)):
        """Initialise a small new Leaf.

        width is a fraction of the leaf's length.
        zone is how far along a stem segment leaves grow, as (lowest, highest) fractions.
        """
        super().__init__(full_size, growth=LEAF_GROWTH_PER_STEP)
        self.width = width
        self.number_of_leaflets = number_of_leaflets
        self.colour = colour
        self.zone = zone

    def __str__(self):
        """Return how long the leaf is."""
        return f"{self.calculate_size():.0f} px long"

    def grow(self):
        """Get one step older and a bit bigger, until fully grown."""
        super().grow()
        self.growth = min(1.0, self.growth + LEAF_GROWTH_PER_STEP)

    def draw(self, surface, base, plant):
        """Draw the leaf (or its leaflets) pointing out from the side of the stem."""
        position = self.calculate_position(base, plant)
        if position is not None:
            point, (direction_x, direction_y), side = position
            leaf_angle = math.atan2(direction_y, direction_x) + side * math.radians(LEAF_ANGLE)
            vein_colour = mix_colour(self.colour, WHITE, 0.35)
            size = self.calculate_size()
            if self.number_of_leaflets == 1:
                leaflet_angles = [0]
            else:
                leaflet_angles = LEAFLET_ANGLES
            for leaflet_angle in leaflet_angles:
                # Side leaflets are a bit smaller than the middle one
                length = size if leaflet_angle == 0 else size * 0.8
                angle = leaf_angle + math.radians(leaflet_angle)
                outline = calculate_leaf_outline(point, angle, length, length * self.width)
                pygame.draw.polygon(surface, self.colour, outline)
                tip = (point[0] + math.cos(angle) * length, point[1] + math.sin(angle) * length)
                pygame.draw.line(surface, vein_colour, point, tip, 1)


class Flower(AttachedPart):
    """One flower, which starts as a closed bud and opens over a few steps."""

    def __init__(self, full_size=12, number_of_petals=5, petal_colour=WHITE, centre_colour=(250, 210, 40),
                 centre_size=0.3, steps_to_open=2, zone=(0.8, 1.0)):
        """Initialise a Flower as a closed bud.

        centre_size is a fraction of the flower's size.
        zone is how far along a stem segment flowers grow, as (lowest, highest) fractions.
        """
        # A flower does not get bigger like a leaf does; it opens instead
        super().__init__(full_size)
        self.number_of_petals = number_of_petals
        self.petal_colour = petal_colour
        self.centre_colour = centre_colour
        self.centre_size = centre_size
        self.steps_to_open = steps_to_open
        self.bloom = 0.0  # 0 is a closed bud, 1 is fully open
        self.zone = zone

    def __str__(self):
        """Return how far open the flower is."""
        if self.bloom == 0:
            return "bud"
        if self.bloom >= 1:
            return "open"
        return f"{self.bloom:.0%} open"

    def grow(self):
        """Get one step older and open a bit more, until fully open."""
        super().grow()
        self.bloom = min(1.0, self.bloom + 1 / self.steps_to_open)

    def is_finished(self):
        """Determine if the flower has been fully open for a step, so it can become a berry."""
        return self.age > self.steps_to_open

    def draw(self, surface, base, plant):
        """Draw the flower as a bud if it is closed, or as petals if it has started to open."""
        position = self.calculate_position(base, plant)
        if position is not None:
            point = position[0]
            if self.bloom == 0:
                self.draw_bud(surface, point)
            else:
                # A flower that has just started to open is 40% of its full size
                radius = self.calculate_size() * (0.4 + 0.6 * self.bloom)
                self.draw_flower(surface, point, radius)

    def draw_bud(self, surface, centre):
        """Draw a small green bud with a hint of the petal colour."""
        radius = max(3, self.calculate_size() * 0.25)
        pygame.draw.circle(surface, BUD_COLOUR, centre, radius)
        pygame.draw.circle(surface, self.petal_colour, (centre[0], centre[1] - radius * 0.4), radius * 0.5)

    def draw_flower(self, surface, centre, radius):
        """Draw a ring of petals around the flower's centre."""
        # Narrow the petals when there are many of them so they all fit around the ring
        petal_width = min(radius * 0.8, 2 * math.pi * radius / self.number_of_petals)
        edge_colour = mix_colour(self.petal_colour, BLACK, 0.15)
        for i in range(self.number_of_petals):
            angle = 2 * math.pi * i / self.number_of_petals
            outline = calculate_leaf_outline(centre, angle, radius, petal_width)
            pygame.draw.polygon(surface, self.petal_colour, outline)
            pygame.draw.polygon(surface, edge_colour, outline, 1)
        pygame.draw.circle(surface, self.centre_colour, centre, max(2, radius * self.centre_size))


class SunflowerHead(Flower):
    """A huge flower with lots of petals and a centre packed with seeds."""

    def __init__(self):
        """Initialise a SunflowerHead as a closed bud."""
        super().__init__(full_size=50, number_of_petals=22, petal_colour=(255, 200, 20),
                         centre_colour=(95, 60, 30), centre_size=0.45)

    def draw_flower(self, surface, centre, radius):
        """Draw the flower like any other, then add a spiral of seeds in its centre."""
        super().draw_flower(surface, centre, radius)
        number_of_seeds = int(60 * self.bloom)
        for i in range(number_of_seeds):
            distance = radius * self.centre_size * 0.9 * math.sqrt(i / number_of_seeds)
            angle = i * GOLDEN_ANGLE
            seed_position = (centre[0] + distance * math.cos(angle), centre[1] + distance * math.sin(angle))
            pygame.draw.circle(surface, (60, 38, 20), seed_position, 1.5)


class Berry(AttachedPart):
    """One berry, which grows and ripens in the spot where a flower was."""

    def __init__(self, full_size=8, unripe_colour=(120, 180, 70), ripe_colour=(200, 30, 40), steps_to_ripen=2,
                 random_generator=random):
        """Initialise a small, unripe Berry.

        random_generator is where the berry's random numbers come from, so a
        plant that has its own random.Random can pass that in.
        """
        super().__init__(full_size, growth=0.5)
        self.unripe_colour = unripe_colour
        self.ripe_colour = ripe_colour
        self.steps_to_ripen = steps_to_ripen
        self.ripeness = 0.0  # 0 is unripe, 1 is ripe
        # Each berry hangs a slightly different distance (x, y) from the stem
        self.hang_offset = (random_generator.uniform(3, 11), random_generator.uniform(4, 10))

    def __str__(self):
        """Return how big and how ripe the berry is."""
        return f"{self.calculate_size():.0f} px, {self.ripeness:.0%} ripe"

    def grow(self):
        """Get one step older, bigger and riper, until fully grown and ripe."""
        super().grow()
        self.growth = min(1.0, self.growth + 0.25)
        self.ripeness = min(1.0, self.ripeness + 1 / self.steps_to_ripen)

    def draw(self, surface, base, plant):
        """Draw the berry hanging a little below the stem on a short stalk."""
        position = self.calculate_position(base, plant)
        if position is not None:
            point, _, side = position
            centre = (point[0] + side * self.hang_offset[0],
                      point[1] + self.calculate_size() + self.hang_offset[1])
            pygame.draw.line(surface, STALK_COLOUR, point, centre, 1)
            colour = mix_colour(self.unripe_colour, self.ripe_colour, self.ripeness)
            self.draw_berry(surface, centre, colour)

    def draw_berry(self, surface, centre, colour):
        """Draw a round berry with a shiny highlight."""
        size = self.calculate_size()
        pygame.draw.circle(surface, colour, centre, size)
        shine_colour = mix_colour(colour, WHITE, 0.5)
        shine_centre = (centre[0] - size * 0.35, centre[1] - size * 0.35)
        pygame.draw.circle(surface, shine_colour, shine_centre, max(1, size * 0.25))


class StrawberryFruit(Berry):
    """A strawberry, which is cone-shaped with seeds on the outside."""

    def __init__(self):
        """Initialise a small, pale StrawberryFruit."""
        super().__init__(full_size=11, unripe_colour=(235, 240, 200), ripe_colour=(220, 30, 45))

    def draw_berry(self, surface, centre, colour):
        """Draw a cone-shaped berry with seeds and a leafy green top."""
        # Only the shape is different here; Berry.draw() still decides where the fruit hangs
        x, y = centre
        size = self.calculate_size()
        body = [(x - size, y - size * 0.6), (x + size, y - size * 0.6), (x + size * 0.7, y + size * 0.4),
                (x, y + size * 1.4), (x - size * 0.7, y + size * 0.4)]
        pygame.draw.polygon(surface, colour, body)
        for seed_x, seed_y in ((-0.4, -0.2), (0.4, -0.2), (0, 0.2), (-0.3, 0.6), (0.3, 0.6), (0, 1.0)):
            pygame.draw.circle(surface, (250, 225, 120), (x + seed_x * size, y + seed_y * size), 1)
        leafy_top = [(x - size, y - size * 0.8), (x, y - size * 0.4), (x + size, y - size * 0.8),
                     (x, y - size * 1.1)]
        pygame.draw.polygon(surface, (60, 140, 50), leafy_top)
