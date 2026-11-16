"""
plants.py - the different kinds of plant.

INHERITANCE
    Plant                   the base class: has Roots, Stem, Leaves, Flowers, Berries
    ├── Sunflower
    ├── Tomato
    │   └── CherryTomato    inherits from Tomato, which inherits from Plant
    ├── Strawberry
    └── BlueberryBush

POLYMORPHISM
    Every kind of plant has a grow(step) method, but each one grows differently.
    The program just calls

        plant.grow(step)

    and Python picks the right grow() for whatever kind of plant it is.
"""

import pygame

from parts import Roots, Stem, Leaves, Flowers, SunflowerHead, Berries, Strawberries


def progress(step, start, end):
    """How far through a growth phase we are: 0.0 up to `start`,
    1.0 from `end` onwards, and evenly in between.

    e.g. progress(step, 1, 7) grows something from step 1 to step 7.
    """
    if step <= start:
        return 0.0
    if step >= end:
        return 1.0
    return (step - start) / (end - start)


class Plant:
    """Base class for every plant.

    A Plant HAS-A Roots, Stem, Leaves, Flowers and Berries (composition).
    A Sunflower IS-A Plant (inheritance).
    """

    name = "Plant"
    max_steps = 8               # steps from seed to fully grown
    max_root_depth = 120        # pixels
    max_root_branches = 6
    seed_colour = (140, 105, 60)
    seed_size = 6
    seed_depth = 12             # how deep the seed is planted

    def __init__(self):
        self.step = 0
        self.roots = Roots()
        self.stem = Stem()
        self.leaves = Leaves()
        self.flowers = Flowers()
        self.berries = Berries()

    def parts(self):
        """All the parts, in the order they should be drawn (back to front)."""
        return [self.roots, self.stem, self.leaves, self.flowers, self.berries]

    def grow(self, step):
        """Grow the plant to `step` (1 to max_steps).

        Roots grow the same way in every plant, so that code lives here.
        Subclasses override grow() and call super().grow(step) to keep it.
        """
        self.roots.depth = self.max_root_depth * progress(step, 0, self.max_steps - 2)
        self.roots.branches = round(self.max_root_branches * progress(step, 1, self.max_steps - 2))

    def grow_one_step(self):
        """Move on to the next step, unless the plant is already fully grown."""
        if self.is_mature():
            return
        self.step += 1
        self.grow(self.step)   # <-- polymorphism: runs Sunflower.grow, Tomato.grow, ...

    def is_mature(self):
        return self.step >= self.max_steps

    def stage(self):
        """A name for the current stage, worked out from the parts."""
        if self.step == 0:
            return "Seed"
        if self.is_mature():
            return "Mature"
        if not self.stem.is_present():
            return "Germinating"
        if self.berries.is_present():
            return "Fruiting"
        if self.flowers.is_present():
            return "Flowering" if self.flowers.bloom > 0 else "Budding"
        if self.leaves.count <= 2:
            return "Sprout"
        return "Growing"

    def draw(self, surface, base):
        if self.step <= 2:  # the seed is used up once the plant gets going
            x, y = base[0], base[1] + self.seed_depth
            s = self.seed_size
            pygame.draw.ellipse(surface, self.seed_colour, (x - s, y - s * 0.65, s * 2, s * 1.3))
            if self.step > 0:  # the seed coat splits open
                pygame.draw.line(surface, (60, 40, 20), (x - s * 0.6, y), (x + s * 0.6, y), 1)
        for part in self.parts():
            part.draw(surface, base, self)   # <-- polymorphism again


# --------------------------------------------------------------------------
# The kinds of plant
# --------------------------------------------------------------------------

class Sunflower(Plant):
    name = "Sunflower"
    max_steps = 8
    max_root_depth = 150
    seed_colour = (70, 70, 70)
    seed_size = 7

    def __init__(self):
        super().__init__()
        self.flowers = SunflowerHead()     # a special kind of Flowers
        self.leaves.width = 0.75
        self.leaves.colour = (70, 150, 50)

    def grow(self, step):
        super().grow(step)                 # roots grow like any plant's
        # One tall, thick stem with no branches.
        self.stem.height = 300 * progress(step, 1, 7)
        self.stem.thickness = 3 + step
        # Two more big leaves every step.
        self.leaves.count = min(12, 2 * (step - 1))
        self.leaves.size = 20 + 4 * step
        # A single giant flower head that opens from step 5 to step 7.
        if step >= 5:
            self.flowers.count = 1
            self.flowers.size = 50
            self.flowers.bloom = progress(step, 5, 7)
        # Sunflowers make seeds, not berries, so berries stay at 0.


class Tomato(Plant):
    name = "Tomato"
    max_steps = 10
    seed_colour = (225, 200, 140)
    seed_size = 4

    def __init__(self):
        super().__init__()
        self.stem.branch_angle = 50
        self.flowers.petal_colour = (250, 215, 40)
        self.flowers.centre_colour = (220, 160, 20)
        self.berries.ripe_colour = (215, 40, 30)

    def grow(self, step):
        super().grow(step)
        # A bushy stem that sends out side branches from step 4.
        self.stem.height = 190 * progress(step, 1, 7)
        self.stem.thickness = 2 + step // 2
        self.stem.branches = max(0, min(4, step - 3))
        self.leaves.count = max(0, min(18, 2 * (step - 1)))
        self.leaves.size = 14 + 2 * step
        # Flowers come first, then turn into tomatoes.
        #                 step: 0  1  2  3  4  5  6  7  8  9  10
        self.flowers.count = [0, 0, 0, 0, 0, 5, 5, 3, 0, 0, 0][step]
        self.berries.count = [0, 0, 0, 0, 0, 0, 0, 2, 5, 5, 5][step]
        self.flowers.size = 12
        self.flowers.bloom = 0.0 if step <= 5 else 1.0
        self.berries.size = max(0, min(11, 2 * (step - 4)))
        self.berries.ripeness = progress(step, 8, 10)  # green -> red


class CherryTomato(Tomato):
    """A Tomato that makes lots of small fruit.

    Only the differences are written here; everything else is inherited.
    """

    name = "Cherry tomato"

    def grow(self, step):
        super().grow(step)                 # grow exactly like a Tomato...
        self.berries.count *= 3            # ...but with three times as many fruit...
        self.berries.size //= 2            # ...that are half the size


class Strawberry(Plant):
    name = "Strawberry"
    max_steps = 8
    max_root_depth = 70
    max_root_branches = 9
    seed_colour = (230, 200, 90)
    seed_size = 3

    def __init__(self):
        super().__init__()
        self.berries = Strawberries()      # a special kind of Berries
        self.roots.style = "fibrous"
        # A short crown with leaf stalks fanning out from it.
        self.stem.branch_start = self.stem.branch_end = 0.5
        self.stem.branch_angle = 30
        self.stem.branch_fan = 25
        self.stem.branch_length = 2.0
        self.leaves.leaflets = 3
        self.leaves.width = 0.6
        self.leaves.zone = (0.85, 1.0)
        self.flowers.zone = (0.55, 0.7)
        self.berries.zone = (0.5, 0.7)

    def grow(self, step):
        super().grow(step)
        self.stem.height = 45 * progress(step, 1, 3)
        self.stem.branches = min(6, step)
        self.leaves.count = min(7, step)
        self.leaves.size = 14 + 3 * step
        #                 step: 0  1  2  3  4  5  6  7  8
        self.flowers.count = [0, 0, 0, 0, 3, 4, 2, 0, 0][step]
        self.berries.count = [0, 0, 0, 0, 0, 0, 3, 4, 4][step]
        self.flowers.size = 14
        self.flowers.bloom = 0.0 if step <= 4 else 1.0
        self.berries.size = 11
        self.berries.ripeness = progress(step, 6, 8)   # white -> red


class BlueberryBush(Plant):
    name = "Blueberry bush"
    max_steps = 10
    max_root_depth = 90
    max_root_branches = 12
    seed_colour = (110, 80, 60)
    seed_size = 3

    def __init__(self):
        super().__init__()
        self.roots.style = "fibrous"
        # Lots of woody branches from low down make it a bush.
        self.stem.branch_start = 0.15
        self.stem.branch_end = 0.7
        self.stem.branch_angle = 35
        self.stem.branch_fan = 8
        self.stem.branch_length = 0.75
        self.leaves.width = 0.45
        self.leaves.colour = (50, 130, 80)
        self.leaves.zone = (0.3, 0.95)
        self.flowers.petal_colour = (255, 238, 242)
        self.flowers.centre_colour = (225, 170, 185)
        self.flowers.centre = 0.45
        self.flowers.zone = (0.6, 1.0)
        self.berries.unripe_colour = (170, 200, 120)
        self.berries.ripe_colour = (55, 65, 150)
        self.berries.zone = (0.5, 0.95)

    def grow(self, step):
        super().grow(step)
        self.stem.height = 230 * progress(step, 1, 8)
        self.stem.thickness = 2 + step // 2
        self.stem.branches = max(0, min(6, step - 2))
        self.stem.woody = step >= 4                    # green shoot -> brown bark
        self.leaves.count = max(0, min(30, 3 * (step - 1)))
        self.leaves.size = 12 + 2 * step
        #                 step: 0  1  2  3  4  5  6  7   8   9  10
        self.flowers.count = [0, 0, 0, 0, 0, 0, 8, 12, 6, 0, 0][step]
        self.berries.count = [0, 0, 0, 0, 0, 0, 0, 6, 14, 18, 18][step]
        self.flowers.size = 10
        self.flowers.bloom = 0.0 if step <= 6 else 1.0
        self.berries.size = 7
        self.berries.ripeness = progress(step, 7, 10)  # green -> blue


# The plants the user can choose from. Add a new class here and it appears in the menu.
PLANT_TYPES = [Sunflower, Tomato, CherryTomato, Strawberry, BlueberryBush]
