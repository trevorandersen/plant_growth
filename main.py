"""
Plant Growth Simulator - a pygame demonstration of inheritance and polymorphism.

Choose a kind of plant, then press "Grow one step" (or Space) to grow it from
a seed to a mature plant.

Files:
    main.py         the window, buttons and drawing (this file)
    plants.py       Plant and its subclasses, each with its own grow(step)
    parts.py        Roots, Stem, Leaf, Flower and Berry, and their subclasses
    test_plants.py  tests that the plants grow properly

Run the program with:
    pip install -r requirements.txt
    python main.py

Run the tests with:
    python -m unittest
"""

import random
from collections import Counter

import pygame

from parts import mix_colour
from plants import PLANT_TYPES

WIDTH = 1100
HEIGHT = 720
PANEL_WIDTH = 280
MARGIN = 20
SCENE = pygame.Rect(PANEL_WIDTH, 0, WIDTH - PANEL_WIDTH, 520)
INFO = pygame.Rect(PANEL_WIDTH, SCENE.bottom, WIDTH - PANEL_WIDTH, HEIGHT - SCENE.bottom)
GROUND_Y = 370
PLANT_BASE = (SCENE.centerx, GROUND_Y)  # where the plant's stem meets the soil
SUN_CENTRE = (SCENE.right - 80, 70)
FRAMES_PER_SECOND = 30
LEFT_MOUSE_BUTTON = 1
NUMBER_OF_PLANT_KEYS = min(9, len(PLANT_TYPES))  # the keys 1 to 9 choose a plant

# Side panel layout, in pixels
BUTTON_WIDTH = PANEL_WIDTH - 2 * MARGIN
PLANT_BUTTONS_TOP = 112
MAX_PLANT_BUTTON_SPACING = 48
PLANT_BUTTON_GAP = 8
SECTION_GAP = 45
HEADING_OFFSET = 27  # how far a section's heading is above its first button
GROW_BUTTON_HEIGHT = 54
RESET_BUTTON_HEIGHT = 36
BUTTON_GAP = 10
HIERARCHY_GAP = 22
HEADING_HEIGHT = 26
LINE_HEIGHT = 20
KEY_HINTS_TOP = HEIGHT - 46
KEY_HINTS_GAP = 12

# Info panel layout, in pixels
PART_NAME_WIDTH = 140
PROGRESS_BAR_HEIGHT = 8

PANEL_COLOUR = (245, 242, 232)
INFO_COLOUR = (252, 250, 244)
TEXT_COLOUR = (40, 40, 40)
MUTED_COLOUR = (120, 115, 105)
ACCENT_COLOUR = (60, 140, 70)
ACCENT_HOVER_COLOUR = (75, 160, 85)
BUTTON_COLOUR = (255, 255, 255)
BUTTON_HOVER_COLOUR = (232, 244, 228)
BUTTON_TEXT_COLOUR = (255, 255, 255)
BORDER_COLOUR = (200, 195, 180)
DISABLED_COLOUR = (215, 212, 205)
SKY_TOP_COLOUR = (140, 195, 240)
SKY_BOTTOM_COLOUR = (220, 238, 250)
SUN_COLOUR = (255, 220, 90)
SUN_GLOW_COLOUR = (255, 236, 150)
SOIL_TOP_COLOUR = (125, 90, 58)
SOIL_BOTTOM_COLOUR = (80, 56, 38)
DARK_GRIT_COLOUR = (100, 72, 48)
LIGHT_GRIT_COLOUR = (145, 110, 75)
GRASS_COLOUR = (95, 160, 70)
GRASS_TUFT_COLOUR = (80, 145, 60)


def main():
    """Run the Plant Growth Simulator until its window is closed."""
    app = App()
    app.run()


class Button:
    """A rectangle with a label that can be clicked."""

    def __init__(self, rect, label):
        """Initialise a Button, where rect is (left, top, width, height)."""
        self.rect = pygame.Rect(rect)
        self.label = label

    def is_clicked(self, position):
        """Determine if a click at the (x, y) position is on this button."""
        return self.rect.collidepoint(position)

    def draw(self, surface, font, is_selected=False, is_enabled=True, is_primary=False):
        """Draw the button, highlighted if the mouse is over it."""
        is_hovered = is_enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        text_colour = TEXT_COLOUR
        if not is_enabled:
            fill_colour = DISABLED_COLOUR
            text_colour = MUTED_COLOUR
        elif is_primary or is_selected:
            fill_colour = ACCENT_HOVER_COLOUR if is_hovered else ACCENT_COLOUR
            text_colour = BUTTON_TEXT_COLOUR
        elif is_hovered:
            fill_colour = BUTTON_HOVER_COLOUR
        else:
            fill_colour = BUTTON_COLOUR
        border_colour = ACCENT_COLOUR if is_selected else BORDER_COLOUR
        pygame.draw.rect(surface, fill_colour, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_colour, self.rect, 2, border_radius=8)
        text = font.render(self.label, True, text_colour)
        surface.blit(text, text.get_rect(center=self.rect.center))


class App:
    """The Plant Growth Simulator window, with its buttons and the plant being grown."""

    def __init__(self):
        """Initialise the window, fonts and buttons, then plant a seed of the first kind of plant."""
        pygame.init()
        pygame.display.set_caption("Plant Growth Simulator")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("helvetica,arial", 30, bold=True)
        self.heading_font = pygame.font.SysFont("helvetica,arial", 18, bold=True)
        self.font = pygame.font.SysFont("helvetica,arial", 17)
        self.small_font = pygame.font.SysFont("helvetica,arial", 14)
        self.code_font = pygame.font.SysFont("menlo,consolas,courier new", 14)
        self.background = make_background()

        # Shrink the plant buttons if there are so many kinds of plant that the side panel would overflow.
        # Every class has object at the end of its __mro__, which the class hierarchy does not show.
        number_of_hierarchy_lines = max(len(plant_type.__mro__) for plant_type in PLANT_TYPES) - 1
        height_below_plant_buttons = (SECTION_GAP + GROW_BUTTON_HEIGHT + BUTTON_GAP + RESET_BUTTON_HEIGHT
                                      + HIERARCHY_GAP + HEADING_HEIGHT + LINE_HEIGHT * number_of_hierarchy_lines)
        available_height = KEY_HINTS_TOP - KEY_HINTS_GAP - PLANT_BUTTONS_TOP - height_below_plant_buttons
        spacing = min(MAX_PLANT_BUTTON_SPACING, available_height // len(PLANT_TYPES))
        self.plant_buttons = []
        for i, plant_type in enumerate(PLANT_TYPES):
            rect = (MARGIN, PLANT_BUTTONS_TOP + i * spacing, BUTTON_WIDTH, spacing - PLANT_BUTTON_GAP)
            self.plant_buttons.append(Button(rect, plant_type.name))
        grow_top = self.plant_buttons[-1].rect.bottom + SECTION_GAP
        self.grow_button = Button((MARGIN, grow_top, BUTTON_WIDTH, GROW_BUTTON_HEIGHT), "Grow one step")
        reset_top = self.grow_button.rect.bottom + BUTTON_GAP
        self.reset_button = Button((MARGIN, reset_top, BUTTON_WIDTH, RESET_BUTTON_HEIGHT), "Plant a new seed")

        self.selected_index = 0
        self.plant = None
        self.message = ""
        self.select(self.selected_index)

    def run(self):
        """Handle events and redraw the window until it is closed."""
        is_running = True
        while is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT_MOUSE_BUTTON:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
            self.draw()
            pygame.display.flip()
            self.clock.tick(FRAMES_PER_SECOND)
        pygame.quit()

    def select(self, index):
        """Plant a new seed of the kind of plant at index in PLANT_TYPES."""
        self.selected_index = index
        plant_type = PLANT_TYPES[index]
        # The exact class of the plant is only known when the program is running
        self.plant = plant_type()
        self.message = f"plant = {plant_type.__name__}()"

    def grow(self):
        """Grow the plant one step, unless it is fully grown, and show which grow() methods ran."""
        if not self.plant.is_mature():
            step = self.plant.step + 1
            self.plant.grow_one_step()
            if self.plant.step == step:
                self.message = f"plant.grow({step}) ran " + " → ".join(list_grow_methods(self.plant))
            else:
                # Plant.grow() counts the step, so if the step was not counted then it did not run
                self.message = f"plant.grow({step}) never reached Plant.grow() - is a super().grow(step) call missing?"

    def handle_click(self, position):
        """Respond to a mouse click at the (x, y) position."""
        for i, button in enumerate(self.plant_buttons):
            if button.is_clicked(position):
                self.select(i)
        if self.grow_button.is_clicked(position):
            self.grow()
        if self.reset_button.is_clicked(position):
            self.select(self.selected_index)

    def handle_key(self, key):
        """Respond to a key being pressed."""
        if key in (pygame.K_SPACE, pygame.K_RETURN):
            self.grow()
        elif key == pygame.K_r:
            self.select(self.selected_index)
        elif pygame.K_1 <= key < pygame.K_1 + NUMBER_OF_PLANT_KEYS:
            self.select(key - pygame.K_1)

    def draw(self):
        """Draw the scene with the plant in it, then the two panels."""
        self.screen.blit(self.background, (0, 0))
        # Polymorphism: the plant draws itself, and this line is the same for every kind of plant
        self.screen.set_clip(SCENE)
        self.plant.draw(self.screen, PLANT_BASE)
        self.screen.set_clip(None)
        self.draw_side_panel()
        self.draw_info_panel()

    def draw_text(self, text, position, font, colour=TEXT_COLOUR):
        """Draw text with its top-left corner at position and return the rectangle it covers."""
        text_surface = font.render(text, True, colour)
        self.screen.blit(text_surface, position)
        return text_surface.get_rect(topleft=position)

    def draw_side_panel(self):
        """Draw the panel with the buttons, the plant's class hierarchy and the key hints."""
        pygame.draw.rect(self.screen, PANEL_COLOUR, (0, 0, PANEL_WIDTH, HEIGHT))
        pygame.draw.line(self.screen, BORDER_COLOUR, (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, HEIGHT), 2)
        self.draw_text("Plant Growth", (MARGIN, 18), self.title_font)
        self.draw_text("Inheritance & polymorphism", (MARGIN, 54), self.small_font, MUTED_COLOUR)

        self.draw_text("1. Choose a plant", (MARGIN, PLANT_BUTTONS_TOP - HEADING_OFFSET), self.heading_font)
        for i, button in enumerate(self.plant_buttons):
            button.draw(self.screen, self.font, is_selected=i == self.selected_index)

        self.draw_text("2. Grow it", (MARGIN, self.grow_button.rect.top - HEADING_OFFSET), self.heading_font)
        is_mature = self.plant.is_mature()
        self.grow_button.label = "Fully grown!" if is_mature else "Grow one step"
        self.grow_button.draw(self.screen, self.heading_font, is_enabled=not is_mature, is_primary=True)
        self.reset_button.draw(self.screen, self.small_font)

        y = self.reset_button.rect.bottom + HIERARCHY_GAP
        self.draw_text("Class hierarchy", (MARGIN, y), self.heading_font)
        y += HEADING_HEIGHT
        # Show every class the plant inherits from, except object, which is always last
        plant_type = type(self.plant)
        for plant_class in plant_type.__mro__[:-1]:
            parent_class = plant_class.__bases__[0]
            if parent_class is object:
                line = f"class {plant_class.__name__}"
            else:
                line = f"class {plant_class.__name__}({parent_class.__name__})"
            colour = ACCENT_COLOUR if plant_class is plant_type else TEXT_COLOUR
            self.draw_text(line, (MARGIN, y), self.code_font, colour)
            y += LINE_HEIGHT

        self.draw_text("Keys: Space = grow, R = restart,", (MARGIN, KEY_HINTS_TOP), self.small_font, MUTED_COLOUR)
        key_hint = f"1-{NUMBER_OF_PLANT_KEYS} = choose a plant"
        self.draw_text(key_hint, (MARGIN, KEY_HINTS_TOP + 18), self.small_font, MUTED_COLOUR)

    def draw_info_panel(self):
        """Draw the panel that describes the plant: its stage, its step and each kind of part."""
        plant = self.plant
        pygame.draw.rect(self.screen, INFO_COLOUR, INFO)
        pygame.draw.line(self.screen, BORDER_COLOUR, INFO.topleft, INFO.topright, 2)
        left = INFO.left + MARGIN
        top = INFO.top + 10

        name_rect = self.draw_text(plant.name, (left, top), self.heading_font)
        stage_text = f"Stage: {plant.determine_stage()}"
        self.draw_text(stage_text, (name_rect.right + MARGIN, top + 1), self.font, ACCENT_COLOUR)
        step_surface = self.font.render(f"Step {plant.step} of {plant.max_steps}", True, MUTED_COLOUR)
        self.screen.blit(step_surface, step_surface.get_rect(topright=(INFO.right - MARGIN, top + 1)))

        progress_bar = pygame.Rect(left, top + 28, INFO.width - 2 * MARGIN, PROGRESS_BAR_HEIGHT)
        pygame.draw.rect(self.screen, DISABLED_COLOUR, progress_bar, border_radius=4)
        filled_width = round(progress_bar.width * plant.step / plant.max_steps)
        if filled_width > 0:
            filled_bar = pygame.Rect(progress_bar.left, progress_bar.top, filled_width, PROGRESS_BAR_HEIGHT)
            pygame.draw.rect(self.screen, ACCENT_COLOUR, filled_bar, border_radius=4)

        # Polymorphism: every part describes itself in its own way.
        # Group parts of the same class, like "Leaf   8 × 52 px long,  2 × 35 px long"
        class_name_to_descriptions = {}
        for part in plant.get_parts():
            class_name = type(part).__name__
            if class_name not in class_name_to_descriptions:
                class_name_to_descriptions[class_name] = []
            class_name_to_descriptions[class_name].append(part.describe())
        y = top + 46
        for class_name, descriptions in class_name_to_descriptions.items():
            description_to_count = Counter(descriptions)
            summaries = []
            for description, count in description_to_count.items():
                summaries.append(description if count == 1 else f"{count} × {description}")
            self.draw_text(class_name, (left, y + 1), self.code_font, MUTED_COLOUR)
            self.draw_text(",  ".join(summaries), (left + PART_NAME_WIDTH, y), self.font)
            y += LINE_HEIGHT

        self.draw_text(self.message, (left, INFO.bottom - 24), self.code_font, ACCENT_COLOUR)


def make_background():
    """Make a picture of the sky, sun and soil, to be copied to the screen every frame."""
    background = pygame.Surface((WIDTH, HEIGHT))
    draw_gradient(background, SCENE.top, GROUND_Y, SKY_TOP_COLOUR, SKY_BOTTOM_COLOUR)
    pygame.draw.circle(background, SUN_GLOW_COLOUR, SUN_CENTRE, 46)
    pygame.draw.circle(background, SUN_COLOUR, SUN_CENTRE, 36)
    draw_gradient(background, GROUND_Y, SCENE.bottom, SOIL_TOP_COLOUR, SOIL_BOTTOM_COLOUR)

    # Start from the same seed every time so the background always looks the same
    random_generator = random.Random(1)
    number_of_grit_specks = 500
    for _ in range(number_of_grit_specks):
        x = random_generator.randint(SCENE.left, SCENE.right)
        y = random_generator.randint(GROUND_Y + 8, SCENE.bottom)
        colour = random_generator.choice([DARK_GRIT_COLOUR, LIGHT_GRIT_COLOUR])
        pygame.draw.circle(background, colour, (x, y), random_generator.randint(1, 2))

    pygame.draw.rect(background, GRASS_COLOUR, (SCENE.left, GROUND_Y - 3, SCENE.width, 7))
    for x in range(SCENE.left, SCENE.right, 7):
        tuft_top = (x + random_generator.randint(-3, 3), GROUND_Y - random_generator.randint(4, 11))
        pygame.draw.line(background, GRASS_TUFT_COLOUR, (x, GROUND_Y), tuft_top, 2)
    return background


def draw_gradient(surface, top, bottom, top_colour, bottom_colour):
    """Draw a band across the scene that blends from top_colour down to bottom_colour."""
    for y in range(top, bottom):
        fraction = (y - top) / (bottom - top)
        colour = mix_colour(top_colour, bottom_colour, fraction)
        pygame.draw.line(surface, colour, (SCENE.left, y), (SCENE.right, y))


def list_grow_methods(plant):
    """List the names of the grow() methods that run when plant grows, in order.

    For a CherryTomato, that is ["CherryTomato.grow", "Tomato.grow", "Plant.grow"].
    Each class's grow() calls super().grow(step), which runs the grow() of the
    next class up that has one, so the order is from the plant's own class up to Plant.
    """
    method_names = []
    for plant_class in type(plant).__mro__:
        if "grow" in vars(plant_class):
            method_names.append(f"{plant_class.__name__}.grow")
    return method_names


if __name__ == "__main__":
    main()
