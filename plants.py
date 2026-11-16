"""
plants.py - the different kinds of plant.

INHERITANCE
    Plant                   the base class
    ├── Sunflower
    ├── Tomato
    │   └── CherryTomato    inherits from Tomato, which inherits from Plant
    ├── Strawberry
    ├── BlueberryBush
    └── RandomisedPlant     a different, made-up plant every time

COMPOSITION
    Every Plant HAS one Roots and one Stem, plus LISTS of Leaf, Flower
    and Berry objects that grow over time.

POLYMORPHISM
    Every kind of plant has a grow(step) method, but each one grows differently.
    The program just calls

        plant.grow(step)

    and Python picks the right grow() for whatever kind of plant it is.
    Plants also override new_leaf(), new_flower() and new_berry() to choose
    which kind of Leaf, Flower and Berry they make.
"""

import random

import pygame

from parts import Roots, Stem, Leaf, Flower, SunflowerHead, Berry, StrawberryFruit


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

    A Plant HAS-A Roots and a Stem, and lists of Leaf, Flower and Berry (composition).
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
        self.leaves = []        # Leaf objects
        self.flowers = []       # Flower objects
        self.berries = []       # Berry objects

    def parts(self):
        """Every part, in the order they should be drawn (back to front)."""
        return [self.roots, self.stem] + self.leaves + self.flowers + self.berries

    # ---- Which kind of leaf, flower and berry this plant makes.
    # ---- Subclasses override these to make their own kinds.

    def new_leaf(self):
        return Leaf()

    def new_flower(self):
        return Flower()

    def new_berry(self):
        return Berry()

    # ---- Helpers the subclasses use in grow()

    def add_leaves(self, count):
        for _ in range(count):
            leaf = self.new_leaf()
            leaf.spot = self.stem.spot_for(len(self.leaves), *leaf.zone)
            self.leaves.append(leaf)

    def add_flowers(self, count):
        for _ in range(count):
            flower = self.new_flower()
            index = len(self.flowers) + len(self.berries)  # berries took the old flowers' spots
            flower.spot = self.stem.spot_for(index, *flower.zone)
            self.flowers.append(flower)

    def flowers_become_berries(self):
        """Each flower that has finished blooming turns into a berry in the same spot."""
        for flower in list(self.flowers):
            if flower.is_finished():
                berry = self.new_berry()
                berry.spot = flower.spot
                self.flowers.remove(flower)
                self.berries.append(berry)

    # ---- Growing

    def grow(self, step):
        """Grow the plant to `step` (1 to max_steps).

        The things every plant does live here. Subclasses override grow()
        and call super().grow(step) first, then add their own growth.
        """
        self.roots.depth = self.max_root_depth * progress(step, 0, self.max_steps - 2)
        self.roots.branches = round(self.max_root_branches * progress(step, 1, self.max_steps - 2))
        for part in self.parts():
            part.grow()        # <-- polymorphism: each leaf, flower and berry grows its own way

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
        if self.berries:
            return "Fruiting"
        if self.flowers:
            if any(flower.bloom > 0 for flower in self.flowers):
                return "Flowering"
            return "Budding"
        if len(self.leaves) <= 2:
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

    def new_leaf(self):
        return Leaf(full_size=52, width=0.75, colour=(70, 150, 50))

    def new_flower(self):
        return SunflowerHead()             # a special kind of Flower

    def grow(self, step):
        super().grow(step)                 # roots grow, and every part grows a bit
        # One tall, thick stem with no branches.
        self.stem.height = 300 * progress(step, 1, 7)
        self.stem.thickness = 3 + step
        # Two new leaves every step until there are 12.
        if step >= 2 and len(self.leaves) < 12:
            self.add_leaves(2)
        # A single giant flower head appears at step 5.
        if step == 5:
            self.add_flowers(1)
        # Sunflowers make seeds, not berries, so flowers never become berries.


class Tomato(Plant):
    name = "Tomato"
    max_steps = 10
    seed_colour = (225, 200, 140)
    seed_size = 4

    def __init__(self):
        super().__init__()
        self.stem.branch_angle = 50

    def new_leaf(self):
        return Leaf(full_size=34)

    def new_flower(self):
        flower = Flower(petal_colour=(250, 215, 40), centre_colour=(220, 160, 20))
        flower.zone = (0.45, 1.0)          # flowers (and later fruit) all along the branches
        return flower

    def new_berry(self):
        return Berry(full_size=11, ripe_colour=(215, 40, 30))

    def grow(self, step):
        super().grow(step)
        # A bushy stem that sends out side branches from step 3.
        self.stem.height = 190 * progress(step, 1, 7)
        self.stem.thickness = 2 + step // 2
        self.stem.branches = max(0, min(4, step - 2))
        if step >= 2 and len(self.leaves) < 24:
            self.add_leaves(3)
        # Five flower buds at step 5. Once they finish blooming they turn into tomatoes.
        if step == 5:
            self.add_flowers(5)
        self.flowers_become_berries()


class CherryTomato(Tomato):
    """A Tomato that makes lots of small fruit.

    Only the differences are written here; everything else is inherited.
    """

    name = "Cherry tomato"

    def new_berry(self):
        berry = super().new_berry()        # make a tomato like a Tomato does...
        berry.full_size = 5                # ...but much smaller
        return berry

    def grow(self, step):
        super().grow(step)                 # grow exactly like a Tomato...
        if step == 5:
            self.add_flowers(10)           # ...with extra flowers, so extra fruit


class Strawberry(Plant):
    name = "Strawberry"
    max_steps = 8
    max_root_depth = 70
    max_root_branches = 9
    seed_colour = (230, 200, 90)
    seed_size = 3

    def __init__(self):
        super().__init__()
        self.roots.style = "fibrous"
        # A short crown with leaf stalks fanning out from it.
        self.stem.branch_start = self.stem.branch_end = 0.5
        self.stem.branch_angle = 30
        self.stem.branch_fan = 25
        self.stem.branch_length = 2.0

    def new_leaf(self):
        leaf = Leaf(full_size=38, width=0.6, leaflets=3)
        leaf.zone = (0.85, 1.0)            # leaves at the ends of the stalks
        return leaf

    def new_flower(self):
        flower = Flower(size=14, open_steps=1)
        flower.zone = (0.55, 0.7)          # flowers part-way along, so fruit hangs low
        return flower

    def new_berry(self):
        return StrawberryFruit()           # a special kind of Berry

    def grow(self, step):
        super().grow(step)
        self.stem.height = 45 * progress(step, 1, 3)
        self.stem.branches = min(6, step)
        if step >= 2:
            self.add_leaves(1)
        if step == 3:
            self.add_flowers(3)
        if step == 4:
            self.add_flowers(1)
        self.flowers_become_berries()


class BlueberryBush(Plant):
    name = "Blueberry bush"
    max_steps = 11
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

    def new_leaf(self):
        leaf = Leaf(full_size=30, width=0.45, colour=(50, 130, 80))
        leaf.zone = (0.3, 0.95)
        return leaf

    def new_flower(self):
        flower = Flower(size=10, petal_colour=(255, 238, 242), centre_colour=(225, 170, 185),
                        centre=0.45, open_steps=1)
        flower.zone = (0.6, 1.0)
        return flower

    def new_berry(self):
        return Berry(full_size=8, unripe_colour=(170, 200, 120), ripe_colour=(55, 65, 150))

    def grow(self, step):
        super().grow(step)
        self.stem.height = 230 * progress(step, 1, 8)
        self.stem.thickness = 2 + step // 2
        self.stem.branches = max(0, min(6, step - 2))
        self.stem.woody = step >= 4                    # green shoot -> brown bark
        if step >= 2 and len(self.leaves) < 36:
            self.add_leaves(4)
        # Two batches of flowers, so the berries ripen at different times.
        if step == 6:
            self.add_flowers(8)
        if step == 7:
            self.add_flowers(6)
        self.flowers_become_berries()


def random_colour(rng, hue=(0, 360), saturation=(40, 100), value=(70, 100)):
    """A random colour, picked by hue (0-360), saturation and brightness (0-100)."""
    colour = pygame.Color(0)
    colour.hsva = (rng.uniform(*hue), rng.uniform(*saturation), rng.uniform(*value), 100)
    return (colour.r, colour.g, colour.b)


class RandomisedPlant(Plant):
    """A made-up plant whose features are chosen at random.

    The rest of the program can't tell the difference: it still just calls
    plant.grow(step) and plant.draw(...). That's polymorphism.

    Every random choice comes from self.rng, which starts from `seed`, so
    RandomisedPlant(seed=1234) grows into the same plant every time.
    """

    name = "Random plant"

    def __init__(self, seed=None):
        super().__init__()
        if seed is None:
            seed = random.randint(1000, 9999)
        self.seed = seed
        self.rng = rng = random.Random(seed)
        self.name = f"Random plant #{seed}"    # this object's name hides the class's name

        # These are class attributes in the other plants. Setting them on
        # self gives THIS plant its own values.
        self.max_steps = rng.randint(8, 12)
        self.max_root_depth = rng.randint(60, 160)
        self.max_root_branches = rng.randint(4, 12)
        self.seed_colour = random_colour(rng, hue=(20, 50), value=(30, 80))
        self.seed_size = rng.randint(3, 7)
        self.roots.style = rng.choice(["tap", "fibrous"])

        # Stem shape
        self.stem_height = rng.randint(80, 300)
        self.max_branches = rng.randint(0, 6)
        self.stem.branch_angle = rng.randint(25, 60)
        self.stem.branch_fan = rng.randint(0, 15)
        self.stem.branch_length = rng.uniform(0.3, 0.8)
        self.stem.branch_start = rng.uniform(0.1, 0.4)
        self.stem.branch_end = rng.uniform(0.6, 0.85)
        self.stem.colour = random_colour(rng, hue=(80, 130), saturation=(40, 70), value=(50, 65))
        self.woody = rng.random() < 0.4

        # Leaves
        self.leaf_size = rng.randint(15, 50)
        self.leaf_width = rng.uniform(0.3, 0.8)
        self.leaflets = rng.choice([1, 1, 3])
        self.leaf_colour = random_colour(rng, hue=(80, 150), saturation=(45, 75), value=(45, 70))
        self.max_new_leaves = rng.randint(1, 4)
        self.max_leaves = rng.randint(8, 30)

        # Flowers: when they appear must leave time for berries to ripen
        self.flower_open_steps = rng.randint(1, 2)
        self.flower_step = rng.randint(3, self.max_steps - self.flower_open_steps - 3)
        self.flower_count = rng.randint(1, 10)
        self.flower_size = rng.randint(8, 22)
        self.petals = rng.randint(4, 12)
        self.petal_colour = random_colour(rng, saturation=(20, 90), value=(85, 100))
        self.centre_colour = random_colour(rng, value=(50, 100))

        # Berries: not every plant makes them
        self.makes_berries = rng.random() < 0.75
        self.berry_size = rng.randint(4, 12)
        self.ripe_colour = random_colour(rng, saturation=(60, 100), value=(40, 90))

    def new_leaf(self):
        return Leaf(full_size=self.leaf_size, width=self.leaf_width,
                    leaflets=self.leaflets, colour=self.leaf_colour)

    def new_flower(self):
        return Flower(size=self.flower_size, petals=self.petals, petal_colour=self.petal_colour,
                      centre_colour=self.centre_colour, open_steps=self.flower_open_steps)

    def new_berry(self):
        return Berry(full_size=self.berry_size, ripe_colour=self.ripe_colour)

    def grow(self, step):
        super().grow(step)
        self.stem.height = self.stem_height * progress(step, 1, self.max_steps - 1)
        self.stem.thickness = 2 + step // 2
        self.stem.branches = min(self.max_branches, max(0, step - 2))
        self.stem.woody = self.woody and step >= self.max_steps // 2
        # A random number of new leaves each step.
        if step >= 2 and len(self.leaves) < self.max_leaves:
            self.add_leaves(self.rng.randint(1, self.max_new_leaves))
        if step == self.flower_step:
            self.add_flowers(self.flower_count)
        if self.makes_berries:
            self.flowers_become_berries()


# The plants the user can choose from. Add a new class here and it appears in the menu.
PLANT_TYPES = [Sunflower, Tomato, CherryTomato, Strawberry, BlueberryBush, RandomisedPlant]
