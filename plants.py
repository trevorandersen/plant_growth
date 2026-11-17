"""
Kinds of plant for the Plant Growth Simulator.

Inheritance:
    Plant                   the base class
    ├── Sunflower
    ├── Tomato
    │   └── CherryTomato    inherits from Tomato, which inherits from Plant
    ├── Strawberry
    ├── BlueberryBush
    └── RandomisedPlant     a different, made-up plant every time

Composition:
    Every Plant has one Roots and one Stem, plus lists of Leaf, Flower and
    Berry objects that grow over time.

Polymorphism:
    Every kind of plant has a grow(step) method, but each one grows differently.
    A program just calls

        plant.grow(step)        for step 1, then 2, then 3... up to max_steps

    and Python runs the right grow() for whatever kind of plant it is.
    Plants also override make_leaf(), make_flower() and make_berry() to choose
    which kind of Leaf, Flower and Berry they make.
"""

import random

import pygame

from parts import TapRoots, FibrousRoots, Stem, Leaf, Flower, SunflowerHead, Berry, StrawberryFruit

SEED_SPLIT_COLOUR = (60, 40, 20)
# The seed is used up once the plant has grown this many steps
LAST_STEP_WITH_SEED = 2


def calculate_progress(step, start_step, end_step):
    """Calculate how far through a growth phase a step is, from 0.0 to 1.0.

    The phase begins after start_step and is finished at end_step, so
    calculate_progress(step, 1, 7) grows something evenly from step 1 to step 7.
    """
    if step <= start_step:
        return 0.0
    if step >= end_step:
        return 1.0
    return (step - start_step) / (end_step - start_step)


def choose_random_colour(random_generator, hue_range=(0, 360), saturation_range=(40, 100), value_range=(70, 100)):
    """Choose a random colour with its hue (0-360), saturation and brightness (0-100) in the given ranges."""
    hue = random_generator.uniform(hue_range[0], hue_range[1])
    saturation = random_generator.uniform(saturation_range[0], saturation_range[1])
    value = random_generator.uniform(value_range[0], value_range[1])
    colour = pygame.Color(0)
    colour.hsva = (hue, saturation, value, 100)
    return colour.r, colour.g, colour.b


class Plant:
    """Base class for every kind of plant.

    A Plant has one Roots and one Stem, and lists of Leaf, Flower and Berry
    objects (composition). A Sunflower is a Plant (inheritance).
    """

    name = "Plant"
    max_steps = 8  # from seed to fully grown
    max_root_depth = 120  # pixels
    max_root_branches = 6
    max_leaves = 12
    seed_colour = (140, 105, 60)
    seed_size = 6
    seed_depth = 12  # pixels below the ground

    def __init__(self):
        """Initialise a Plant as a seed that has not started to grow."""
        self.step = 0
        self.roots = TapRoots()
        self.stem = Stem()
        self.leaves = []
        self.flowers = []
        self.berries = []

    def __str__(self):
        """Return the plant's name and how far it has grown."""
        return f"{self.name} at step {self.step} of {self.max_steps}"

    def get_parts(self):
        """Return every part of the plant in the order they are drawn, from back to front."""
        return [self.roots, self.stem] + self.leaves + self.flowers + self.berries

    def make_leaf(self):
        """Make one new leaf. Subclasses override this to make their own kind of leaf."""
        return Leaf()

    def make_flower(self):
        """Make one new flower. Subclasses override this to make their own kind of flower."""
        return Flower()

    def make_berry(self):
        """Make one new berry. Subclasses override this to make their own kind of berry."""
        return Berry()

    def add_leaves(self, number_of_leaves):
        """Grow new leaves on the stem, but never more than max_leaves altogether."""
        number_to_add = min(number_of_leaves, self.max_leaves - len(self.leaves))
        for _ in range(number_to_add):
            leaf = self.make_leaf()
            taken_spots = [other_leaf.spot for other_leaf in self.leaves]
            lowest, highest = leaf.zone
            leaf.spot = self.stem.choose_spot(taken_spots, lowest, highest)
            self.leaves.append(leaf)

    def add_flowers(self, number_of_flowers):
        """Grow new flower buds on the stem."""
        for _ in range(number_of_flowers):
            flower = self.make_flower()
            # Berries count too, because they hang in the spots where flowers used to be
            taken_spots = [part.spot for part in self.flowers + self.berries]
            lowest, highest = flower.zone
            flower.spot = self.stem.choose_spot(taken_spots, lowest, highest)
            self.flowers.append(flower)

    def turn_flowers_into_berries(self):
        """Replace each flower that has finished blooming with a berry in the same spot."""
        finished_flowers = [flower for flower in self.flowers if flower.is_finished()]
        for flower in finished_flowers:
            berry = self.make_berry()
            berry.spot = flower.spot
            self.flowers.remove(flower)
            self.berries.append(berry)

    def grow(self, step):
        """Do the growing for one step, where step is the number of that step.

        The steps go in order (1, 2, 3... up to max_steps) because each one
        builds on the one before: leaves get bigger, buds open and flowers
        become berries. Skipping or repeating a step raises a ValueError.

        The growing that every plant does is here. Subclasses override grow()
        and call super().grow(step) first, then add their own growing.
        """
        if step != self.step + 1 or step > self.max_steps:
            raise ValueError(f"{self} cannot grow step {step}")
        self.step = step
        self.roots.depth = self.max_root_depth * calculate_progress(step, 0, self.max_steps - 2)
        self.roots.number_of_branches = round(self.max_root_branches * calculate_progress(step, 1, self.max_steps - 2))
        # Polymorphism: each part grows in its own way
        for part in self.get_parts():
            part.grow()

    def grow_one_step(self):
        """Grow the next step, unless the plant is already fully grown."""
        if not self.is_mature():
            # Polymorphism: this runs Sunflower.grow(), Tomato.grow()... whichever kind of plant this is
            self.grow(self.step + 1)

    def is_mature(self):
        """Determine if the plant is fully grown."""
        return self.step >= self.max_steps

    def determine_stage(self):
        """Determine the name of the plant's stage of growth from its step and its parts."""
        if self.step == 0:
            stage = "Seed"
        elif self.is_mature():
            stage = "Mature"
        elif not self.stem.is_present():
            stage = "Germinating"
        elif self.berries:
            stage = "Fruiting"
        elif any(flower.bloom > 0 for flower in self.flowers):
            stage = "Flowering"
        elif self.flowers:
            stage = "Budding"
        elif len(self.leaves) <= 2:
            stage = "Sprout"
        else:
            stage = "Growing"
        return stage

    def draw(self, surface, base):
        """Draw the plant, where base is the (x, y) point at which the stem meets the soil."""
        if self.step <= LAST_STEP_WITH_SEED:
            self.draw_seed(surface, base)
        # Polymorphism: each part draws itself in its own way
        for part in self.get_parts():
            part.draw(surface, base, self)

    def draw_seed(self, surface, base):
        """Draw the seed under the ground, with a split in it once it has started to grow."""
        x = base[0]
        y = base[1] + self.seed_depth
        size = self.seed_size
        pygame.draw.ellipse(surface, self.seed_colour, (x - size, y - size * 0.65, size * 2, size * 1.3))
        if self.step > 0:
            pygame.draw.line(surface, SEED_SPLIT_COLOUR, (x - size * 0.6, y), (x + size * 0.6, y), 1)


class Sunflower(Plant):
    """A tall plant with one thick stem and a single giant flower head."""

    name = "Sunflower"
    max_root_depth = 135
    seed_colour = (70, 70, 70)
    seed_size = 7

    def make_leaf(self):
        """Make a big, broad leaf."""
        return Leaf(full_size=52, width=0.75, colour=(70, 150, 50))

    def make_flower(self):
        """Make a sunflower head, which is a special kind of Flower."""
        return SunflowerHead()

    def grow(self, step):
        """Grow a taller, thicker stem with more leaves, then one flower head."""
        super().grow(step)
        self.stem.height = 300 * calculate_progress(step, 1, 7)
        self.stem.thickness = 3 + step
        if step >= 2:
            self.add_leaves(2)
        if step == 5:
            self.add_flowers(1)
        # Sunflowers make seeds, not berries, so the flower never turns into a berry


class Tomato(Plant):
    """A bushy plant with side branches, yellow flowers and red fruit."""

    name = "Tomato"
    max_steps = 10
    max_leaves = 24
    flower_step = 5
    seed_colour = (225, 200, 140)
    seed_size = 4

    def __init__(self):
        """Initialise a Tomato seed whose branches will spread out widely."""
        super().__init__()
        self.stem.branch_angle = 50

    def make_leaf(self):
        """Make a medium-sized leaf."""
        return Leaf(full_size=34)

    def make_flower(self):
        """Make a yellow flower that can grow anywhere along the top half of a branch."""
        return Flower(petal_colour=(250, 215, 40), centre_colour=(220, 160, 20), zone=(0.45, 1.0))

    def make_berry(self):
        """Make a tomato, which is a big red berry."""
        return Berry(full_size=11, ripe_colour=(215, 40, 30))

    def grow(self, step):
        """Grow a bushy stem with more leaves, then flowers that turn into tomatoes."""
        super().grow(step)
        self.stem.height = 190 * calculate_progress(step, 1, 7)
        self.stem.thickness = 2 + step // 2
        # Send out one more side branch each step from step 3, until there are 4
        self.stem.number_of_branches = max(0, min(4, step - 2))
        if step >= 2:
            self.add_leaves(3)
        if step == self.flower_step:
            self.add_flowers(5)
        self.turn_flowers_into_berries()


class CherryTomato(Tomato):
    """A Tomato that makes lots of small fruit.

    Only the differences are written here; everything else is inherited from Tomato.
    """

    name = "Cherry tomato"

    def make_berry(self):
        """Make a tomato the way a Tomato does, but much smaller."""
        berry = super().make_berry()
        berry.full_size = 5
        return berry

    def grow(self, step):
        """Grow like a Tomato, with extra flowers so there is more fruit."""
        super().grow(step)
        if step == self.flower_step:
            self.add_flowers(10)


class Strawberry(Plant):
    """A low plant with three-part leaves on long stalks and fruit that hangs near the ground."""

    name = "Strawberry"
    max_root_depth = 70
    max_root_branches = 9
    max_leaves = 7
    seed_colour = (230, 200, 90)
    seed_size = 3

    def __init__(self):
        """Initialise a Strawberry seed with fibrous roots and a short crown of leaf stalks."""
        super().__init__()
        self.roots = FibrousRoots()
        # Fan long leaf stalks out from the middle of a short stem
        self.stem.branch_start = 0.5
        self.stem.branch_end = 0.5
        self.stem.branch_angle = 30
        self.stem.branch_fan = 25
        self.stem.branch_length = 2.0

    def make_leaf(self):
        """Make a leaf with three leaflets that grows at the end of a stalk."""
        return Leaf(full_size=38, width=0.6, number_of_leaflets=3, zone=(0.85, 1.0))

    def make_flower(self):
        """Make a white flower that grows part-way along a stalk, so the fruit hangs low."""
        return Flower(full_size=14, steps_to_open=1, zone=(0.55, 0.7))

    def make_berry(self):
        """Make a strawberry, which is a special kind of Berry."""
        return StrawberryFruit()

    def grow(self, step):
        """Grow more leaf stalks with a leaf on each, then flowers that turn into strawberries."""
        super().grow(step)
        self.stem.height = 45 * calculate_progress(step, 1, 3)
        self.stem.number_of_branches = min(6, step)
        if step >= 2:
            self.add_leaves(1)
        if step == 3:
            self.add_flowers(3)
        if step == 4:
            self.add_flowers(1)
        self.turn_flowers_into_berries()


class BlueberryBush(Plant):
    """A woody bush with lots of branches, small leaves and blue berries."""

    name = "Blueberry bush"
    max_steps = 11
    max_root_depth = 90
    max_root_branches = 12
    max_leaves = 36
    seed_colour = (110, 80, 60)
    seed_size = 3

    def __init__(self):
        """Initialise a BlueberryBush seed with fibrous roots and a stem that branches from low down."""
        super().__init__()
        self.roots = FibrousRoots()
        self.stem.branch_start = 0.15
        self.stem.branch_end = 0.7
        self.stem.branch_angle = 35
        self.stem.branch_fan = 8
        self.stem.branch_length = 0.75

    def make_leaf(self):
        """Make a small, narrow, dark leaf."""
        return Leaf(full_size=30, width=0.45, colour=(50, 130, 80), zone=(0.3, 0.95))

    def make_flower(self):
        """Make a small, pale pink flower that opens in one step."""
        return Flower(full_size=10, petal_colour=(255, 238, 242), centre_colour=(225, 170, 185), centre_size=0.45,
                      steps_to_open=1, zone=(0.6, 1.0))

    def make_berry(self):
        """Make a blueberry, which ripens from green to blue."""
        return Berry(full_size=8, unripe_colour=(170, 200, 120), ripe_colour=(55, 65, 150))

    def grow(self, step):
        """Grow a woody, branching stem with more leaves, then two batches of flowers."""
        super().grow(step)
        self.stem.height = 230 * calculate_progress(step, 1, 8)
        self.stem.thickness = 2 + step // 2
        self.stem.number_of_branches = max(0, min(6, step - 2))
        # The green shoot turns into brown bark
        self.stem.is_woody = step >= 4
        if step >= 2:
            self.add_leaves(4)
        # Flower in two batches so the berries ripen at different times
        if step == 6:
            self.add_flowers(8)
        if step == 7:
            self.add_flowers(6)
        self.turn_flowers_into_berries()


class RandomisedPlant(Plant):
    """A made-up plant whose features are chosen at random.

    The rest of the program cannot tell the difference: it still just calls
    plant.grow(step) and plant.draw(surface, base). That is polymorphism.

    Every random choice comes from the plant's own random_generator, which
    starts from seed, so RandomisedPlant(seed=1234) grows into the same plant
    every time. Leave the seed out to get a different plant each time.
    """

    name = "Random plant"

    def __init__(self, seed=None):
        """Initialise a RandomisedPlant seed and choose what it will grow into."""
        super().__init__()
        self.seed = seed if seed is not None else random.randint(1000, 9999)
        self.random_generator = random.Random(self.seed)
        random_generator = self.random_generator
        # This object's name hides the class's name
        self.name = f"Random plant #{self.seed}"

        # These are class variables in the other plants; setting them on self
        # gives this one plant its own values
        self.max_steps = random_generator.randint(8, 12)
        self.max_root_depth = random_generator.randint(60, 135)
        self.max_root_branches = random_generator.randint(4, 12)
        self.max_leaves = random_generator.randint(8, 30)
        self.seed_colour = choose_random_colour(random_generator, hue_range=(20, 50), value_range=(30, 80))
        self.seed_size = random_generator.randint(3, 7)

        self.roots = random_generator.choice([TapRoots(), FibrousRoots()])

        self.max_stem_height = random_generator.randint(80, 300)
        self.max_branches = random_generator.randint(0, 6)
        self.becomes_woody = random_generator.random() < 0.4
        self.stem.branch_angle = random_generator.randint(25, 60)
        self.stem.branch_fan = random_generator.randint(0, 15)
        self.stem.branch_length = random_generator.uniform(0.3, 0.8)
        self.stem.branch_start = random_generator.uniform(0.1, 0.4)
        self.stem.branch_end = random_generator.uniform(0.6, 0.85)
        self.stem.colour = choose_random_colour(random_generator, hue_range=(80, 130), saturation_range=(40, 70),
                                                value_range=(50, 65))

        self.leaf_size = random_generator.randint(15, 50)
        self.leaf_width = random_generator.uniform(0.3, 0.8)
        self.number_of_leaflets = random_generator.choice([1, 1, 3])
        self.leaf_colour = choose_random_colour(random_generator, hue_range=(80, 150), saturation_range=(45, 75),
                                                value_range=(45, 70))
        self.max_new_leaves = random_generator.randint(1, 4)

        self.steps_to_open = random_generator.randint(1, 2)
        # Flower early enough to leave time for the berries to ripen
        self.flower_step = random_generator.randint(3, self.max_steps - self.steps_to_open - 3)
        self.number_of_flowers = random_generator.randint(1, 10)
        self.flower_size = random_generator.randint(8, 22)
        self.number_of_petals = random_generator.randint(4, 12)
        self.petal_colour = choose_random_colour(random_generator, saturation_range=(20, 90), value_range=(85, 100))
        self.centre_colour = choose_random_colour(random_generator, value_range=(50, 100))

        # Not every plant makes berries
        self.makes_berries = random_generator.random() < 0.75
        self.berry_size = random_generator.randint(4, 12)
        self.ripe_colour = choose_random_colour(random_generator, saturation_range=(60, 100), value_range=(40, 90))

    def make_leaf(self):
        """Make a leaf with this plant's size, shape and colour."""
        return Leaf(full_size=self.leaf_size, width=self.leaf_width, number_of_leaflets=self.number_of_leaflets,
                    colour=self.leaf_colour)

    def make_flower(self):
        """Make a flower with this plant's size, petals and colours."""
        return Flower(full_size=self.flower_size, number_of_petals=self.number_of_petals,
                      petal_colour=self.petal_colour, centre_colour=self.centre_colour,
                      steps_to_open=self.steps_to_open)

    def make_berry(self):
        """Make a berry with this plant's size and colour."""
        return Berry(full_size=self.berry_size, ripe_colour=self.ripe_colour, random_generator=self.random_generator)

    def grow(self, step):
        """Grow the stem with a random number of new leaves, then flowers and perhaps berries."""
        super().grow(step)
        self.stem.height = self.max_stem_height * calculate_progress(step, 1, self.max_steps - 1)
        self.stem.thickness = 2 + step // 2
        self.stem.number_of_branches = min(self.max_branches, max(0, step - 2))
        self.stem.is_woody = self.becomes_woody and step >= self.max_steps // 2
        if step >= 2:
            self.add_leaves(self.random_generator.randint(1, self.max_new_leaves))
        if step == self.flower_step:
            self.add_flowers(self.number_of_flowers)
        if self.makes_berries:
            self.turn_flowers_into_berries()


# The kinds of plant a user can choose from (this must come after the classes it lists)
PLANT_TYPES = [Sunflower, Tomato, CherryTomato, Strawberry, BlueberryBush, RandomisedPlant]
