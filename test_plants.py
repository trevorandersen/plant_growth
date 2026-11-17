"""
Tests for the Plant Growth Simulator.

Run the tests with:
    python -m unittest

Many of the tests loop over every kind of plant. That only works because of
polymorphism: a test does not care which class of plant it has, it just calls
grow_one_step(), get_parts(), draw() and so on.
"""

import unittest

import pygame

from main import HEIGHT, PLANT_BASE, SCENE, WIDTH, list_grow_methods
from parts import Berry, FibrousRoots, Roots, StrawberryFruit, TapRoots
from plants import PLANT_TYPES, CherryTomato, RandomisedPlant, Strawberry, Sunflower, Tomato

RANDOM_SEEDS = range(50)


def make_plants():
    """Make a new seed of every kind of plant, plus a batch of random plants."""
    plants = [plant_type() for plant_type in PLANT_TYPES]
    random_plants = [RandomisedPlant(seed) for seed in RANDOM_SEEDS]
    return plants + random_plants


def grow_fully(plant):
    """Grow plant all the way from where it is now to mature, and return it."""
    while not plant.is_mature():
        plant.grow_one_step()
    return plant


def summarise_parts(plant):
    """Summarise each part of plant as (class name, description, spot)."""
    return [(type(part).__name__, part.describe(), getattr(part, "spot", None)) for part in plant.get_parts()]


def draw_picture(plant):
    """Draw plant on a see-through surface the size of the window and return the surface."""
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    plant.draw(surface, PLANT_BASE)
    return surface


class GrowingTests(unittest.TestCase):
    """Tests of how plants grow from a seed to mature."""

    def test_new_plant_is_seed(self):
        """Test that a new plant is a seed with no parts grown."""
        for plant in make_plants():
            with self.subTest(plant.name):
                self.assertEqual(plant.step, 0)
                self.assertEqual(plant.determine_stage(), "Seed")
                self.assertEqual(plant.roots.describe(), "not grown yet")
                self.assertEqual(plant.stem.describe(), "not grown yet")
                self.assertEqual(plant.leaves + plant.flowers + plant.berries, [])

    def test_plant_matures_in_max_steps(self):
        """Test that every plant is mature after exactly max_steps steps."""
        for plant in make_plants():
            with self.subTest(plant.name):
                for step in range(1, plant.max_steps + 1):
                    self.assertFalse(plant.is_mature())
                    plant.grow_one_step()
                    self.assertEqual(plant.step, step)
                self.assertTrue(plant.is_mature())
                self.assertEqual(plant.determine_stage(), "Mature")
                self.assertTrue(plant.roots.is_present())
                self.assertTrue(plant.stem.is_present())
                self.assertGreater(len(plant.leaves), 0)

    def test_mature_plant_stops_growing(self):
        """Test that growing a mature plant changes nothing."""
        plant = grow_fully(Tomato())
        parts_before = summarise_parts(plant)
        plant.grow_one_step()
        self.assertEqual(plant.step, plant.max_steps)
        self.assertEqual(summarise_parts(plant), parts_before)

    def test_grow_step_by_step(self):
        """Test that calling grow(step) for each step in order grows the same plant as grow_one_step()."""
        for plant_type in (Sunflower, Tomato, CherryTomato, Strawberry):
            with self.subTest(plant_type.__name__):
                plant = plant_type()
                for step in range(1, plant.max_steps + 1):
                    plant.grow(step)
                self.assertTrue(plant.is_mature())
                self.assertEqual(summarise_parts(plant), summarise_parts(grow_fully(plant_type())))

    def test_grow_refuses_steps_out_of_order(self):
        """Test that grow(step) raises a ValueError for a skipped, repeated or extra step."""
        with self.assertRaises(ValueError):
            Tomato().grow(10)
        plant = Tomato()
        plant.grow(1)
        with self.assertRaises(ValueError):
            plant.grow(1)
        self.assertEqual(plant.step, 1)
        mature_plant = grow_fully(Tomato())
        with self.assertRaises(ValueError):
            mature_plant.grow(mature_plant.max_steps + 1)

    def test_str(self):
        """Test that a plant's string shows its name and how far it has grown."""
        plant = Tomato()
        plant.grow_one_step()
        self.assertEqual(str(plant), "Tomato at step 1 of 10")


class PartsTests(unittest.TestCase):
    """Tests of the roots, leaves, flowers and berries that plants grow."""

    def test_kinds_of_roots(self):
        """Test that each plant has its own kind of Roots, which describes itself the same way."""
        self.assertIsInstance(Sunflower().roots, TapRoots)
        self.assertIsInstance(Strawberry().roots, FibrousRoots)
        for plant in make_plants():
            with self.subTest(plant.name):
                self.assertIsInstance(plant.roots, Roots)
                plant.grow_one_step()
                self.assertIn("px deep", plant.roots.describe())

    def test_random_plants_have_both_kinds_of_roots(self):
        """Test that some random plants have tap roots and some have fibrous roots."""
        root_class_names = {type(RandomisedPlant(seed).roots).__name__ for seed in RANDOM_SEEDS}
        self.assertEqual(root_class_names, {"TapRoots", "FibrousRoots"})

    def test_never_more_than_max_leaves(self):
        """Test that no plant ever has more leaves than its max_leaves."""
        for plant in make_plants():
            with self.subTest(plant.name):
                while not plant.is_mature():
                    plant.grow_one_step()
                    self.assertLessEqual(len(plant.leaves), plant.max_leaves)

    def test_leaves_on_both_sides(self):
        """Test that every stem segment with two or more leaves has leaves on both sides."""
        for plant in make_plants():
            with self.subTest(plant.name):
                segment_index_to_sides = {}
                for leaf in grow_fully(plant).leaves:
                    segment_index, _, side = leaf.spot
                    if segment_index not in segment_index_to_sides:
                        segment_index_to_sides[segment_index] = []
                    segment_index_to_sides[segment_index].append(side)
                for segment_index, sides in segment_index_to_sides.items():
                    if len(sides) >= 2:
                        self.assertEqual(set(sides), {1, -1}, f"segment {segment_index}")

    def test_flowers_turn_into_berries(self):
        """Test that every tomato flower becomes a ripe berry in the same spot."""
        plant = Tomato()
        while not plant.flowers:
            plant.grow_one_step()
        flower_spots = [flower.spot for flower in plant.flowers]
        grow_fully(plant)
        self.assertEqual(plant.flowers, [])
        self.assertEqual([berry.spot for berry in plant.berries], flower_spots)
        for berry in plant.berries:
            self.assertEqual(str(berry), "11 px, 100% ripe")

    def test_sunflower_makes_no_berries(self):
        """Test that a sunflower keeps its one open flower and never makes a berry."""
        plant = grow_fully(Sunflower())
        self.assertEqual(len(plant.flowers), 1)
        self.assertEqual(str(plant.flowers[0]), "open")
        self.assertEqual(plant.berries, [])

    def test_cherry_tomato_fruit(self):
        """Test that a cherry tomato has more and smaller fruit than a tomato, but is otherwise the same."""
        tomato = grow_fully(Tomato())
        cherry_tomato = grow_fully(CherryTomato())
        self.assertGreater(len(cherry_tomato.berries), len(tomato.berries))
        self.assertLess(cherry_tomato.berries[0].calculate_size(), tomato.berries[0].calculate_size())
        self.assertEqual(len(cherry_tomato.leaves), len(tomato.leaves))

    def test_make_berry(self):
        """Test that every kind of plant makes a Berry, and a strawberry makes its own kind."""
        for plant_type in PLANT_TYPES:
            with self.subTest(plant_type.__name__):
                self.assertIsInstance(plant_type().make_berry(), Berry)
        self.assertIsInstance(Strawberry().make_berry(), StrawberryFruit)


class RandomisedPlantTests(unittest.TestCase):
    """Tests that random plants are repeatable when given a seed."""

    def test_same_seed_grows_same_plant(self):
        """Test that two plants with the same seed have the same parts and look the same."""
        for seed in RANDOM_SEEDS:
            with self.subTest(seed=seed):
                first_plant = grow_fully(RandomisedPlant(seed))
                second_plant = grow_fully(RandomisedPlant(seed))
                self.assertEqual(summarise_parts(first_plant), summarise_parts(second_plant))
                self.assertEqual(pygame.image.tobytes(draw_picture(first_plant), "RGBA"),
                                 pygame.image.tobytes(draw_picture(second_plant), "RGBA"))

    def test_different_seeds_grow_different_plants(self):
        """Test that no two seeds grow plants with exactly the same parts."""
        summaries = {str(summarise_parts(grow_fully(RandomisedPlant(seed)))) for seed in RANDOM_SEEDS}
        self.assertEqual(len(summaries), len(RANDOM_SEEDS))

    def test_no_seed_chooses_one(self):
        """Test that plants made without a seed choose different seeds for themselves."""
        seeds = {RandomisedPlant().seed for _ in range(20)}
        self.assertGreater(len(seeds), 1)


class DrawingTests(unittest.TestCase):
    """Tests of how plants are drawn."""

    def test_plant_fits_in_scene(self):
        """Test that every plant is drawn completely inside the scene at every step."""
        for plant in make_plants():
            for step in range(plant.max_steps + 1):
                with self.subTest(plant.name, step=step):
                    drawn_area = draw_picture(plant).get_bounding_rect()
                    self.assertTrue(SCENE.contains(drawn_area), f"{drawn_area} is outside {SCENE}")
                plant.grow_one_step()


class GrowMethodsTests(unittest.TestCase):
    """Tests of which grow() methods run when a plant grows."""

    def test_lists_every_grow_method(self):
        """Test that each class's grow() is listed, from the plant's own class up to Plant."""
        self.assertEqual(list_grow_methods(Sunflower()), ["Sunflower.grow", "Plant.grow"])
        self.assertEqual(list_grow_methods(CherryTomato()), ["CherryTomato.grow", "Tomato.grow", "Plant.grow"])

    def test_missing_super_call_does_not_count_step(self):
        """Test that a grow() that does not call super().grow(step) leaves the plant's step unchanged."""

        class ForgetfulTomato(Tomato):
            """A Tomato whose grow() forgets to call super().grow(step)."""

            def grow(self, step):
                """Grow a leaf, but none of the things a Tomato or a Plant grows."""
                self.add_leaves(1)

        plant = ForgetfulTomato()
        plant.grow_one_step()
        self.assertEqual(plant.step, 0)
        self.assertEqual(len(plant.leaves), 1)
        self.assertFalse(plant.roots.is_present())


if __name__ == "__main__":
    unittest.main()
