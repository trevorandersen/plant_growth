"""
Plant Growth Simulator - a pygame demo of inheritance and polymorphism.

Pick a kind of plant on the left, then press "Grow one step" (or Space)
to grow it from a seed to a mature plant.

Files:
    parts.py   Roots, Stem, Leaf, Flower, Berry (and their base classes)
    plants.py  Plant and its subclasses, each with its own grow(step)
    main.py    this file: the window, buttons and drawing

Run with:
    pip install -r requirements.txt
    python main.py
"""

import random
import sys
from collections import Counter

import pygame

from plants import PLANT_TYPES

WIDTH, HEIGHT = 1100, 720
PANEL_WIDTH = 280
SCENE = pygame.Rect(PANEL_WIDTH, 0, WIDTH - PANEL_WIDTH, 520)
INFO = pygame.Rect(PANEL_WIDTH, SCENE.bottom, WIDTH - PANEL_WIDTH, HEIGHT - SCENE.bottom)
GROUND_Y = 370
PLANT_BASE = (SCENE.centerx, GROUND_Y)   # where the seed is planted

PANEL_BG = (245, 242, 232)
INFO_BG = (252, 250, 244)
TEXT = (40, 40, 40)
MUTED = (120, 115, 105)
ACCENT = (60, 140, 70)
BUTTON = (255, 255, 255)
BUTTON_HOVER = (232, 244, 228)
BORDER = (200, 195, 180)
DISABLED = (215, 212, 205)


class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, font, selected=False, enabled=True, primary=False):
        hovered = enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if not enabled:
            fill, text_colour = DISABLED, MUTED
        elif primary or selected:
            fill, text_colour = ACCENT, (255, 255, 255)
            if hovered:
                fill = (75, 160, 85)
        else:
            fill, text_colour = (BUTTON_HOVER if hovered else BUTTON), TEXT
        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        pygame.draw.rect(surface, ACCENT if selected else BORDER, self.rect, 2, border_radius=8)
        text = font.render(self.label, True, text_colour)
        surface.blit(text, text.get_rect(center=self.rect.center))


def make_background():
    """Sky, sun and soil. Drawn once, then copied to the screen every frame."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(SCENE.top, GROUND_Y):            # sky gets paler towards the ground
        t = (y - SCENE.top) / (GROUND_Y - SCENE.top)
        colour = [round(a + (b - a) * t) for a, b in zip((140, 195, 240), (220, 238, 250))]
        pygame.draw.line(bg, colour, (SCENE.left, y), (SCENE.right, y))
    pygame.draw.circle(bg, (255, 236, 150), (SCENE.right - 80, 70), 46)
    pygame.draw.circle(bg, (255, 220, 90), (SCENE.right - 80, 70), 36)
    for y in range(GROUND_Y, SCENE.bottom):         # soil gets darker the deeper it goes
        t = (y - GROUND_Y) / (SCENE.bottom - GROUND_Y)
        colour = [round(a + (b - a) * t) for a, b in zip((125, 90, 58), (80, 56, 38))]
        pygame.draw.line(bg, colour, (SCENE.left, y), (SCENE.right, y))
    rng = random.Random(1)
    for _ in range(500):                            # specks of grit in the soil
        x, y = rng.randint(SCENE.left, SCENE.right), rng.randint(GROUND_Y + 8, SCENE.bottom)
        pygame.draw.circle(bg, (100, 72, 48) if rng.random() < 0.5 else (145, 110, 75), (x, y), rng.randint(1, 2))
    pygame.draw.rect(bg, (95, 160, 70), (SCENE.left, GROUND_Y - 3, SCENE.width, 7))
    for x in range(SCENE.left, SCENE.right, 7):     # tufts of grass
        h = rng.randint(4, 11)
        pygame.draw.line(bg, (80, 145, 60), (x, GROUND_Y), (x + rng.randint(-3, 3), GROUND_Y - h), 2)
    return bg


class App:
    def __init__(self):
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

        self.plant_buttons = [Button((20, 112 + i * 48, PANEL_WIDTH - 40, 40), cls.name)
                              for i, cls in enumerate(PLANT_TYPES)]
        grow_top = self.plant_buttons[-1].rect.bottom + 45
        self.grow_button = Button((20, grow_top, PANEL_WIDTH - 40, 54), "Grow one step")
        self.reset_button = Button((20, grow_top + 64, PANEL_WIDTH - 40, 36), "Start again from seed")
        self.select(0)

    # ------------------------------------------------------------- actions

    def select(self, index):
        """Plant a new seed of the chosen type."""
        self.selected = index
        plant_class = PLANT_TYPES[index]
        self.plant = plant_class()     # we only know the exact class at run time
        self.message = f"plant = {plant_class.__name__}()"

    def grow(self):
        if self.plant.is_mature():
            return
        self.plant.grow_one_step()
        # Show which grow() methods actually ran: the subclass's first, then
        # each super().grow(step) call up the inheritance chain.
        ran = [f"{cls.__name__}.grow" for cls in type(self.plant).__mro__ if "grow" in vars(cls)]
        self.message = f"plant.grow({self.plant.step}) ran " + " → ".join(ran)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.plant_buttons):
                if button.is_clicked(event.pos):
                    self.select(i)
            if self.grow_button.is_clicked(event.pos):
                self.grow()
            if self.reset_button.is_clicked(event.pos):
                self.select(self.selected)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.grow()
            elif event.key == pygame.K_r:
                self.select(self.selected)
            elif pygame.K_1 <= event.key < pygame.K_1 + len(PLANT_TYPES):
                self.select(event.key - pygame.K_1)

    # ------------------------------------------------------------- drawing

    def draw(self):
        screen = self.screen
        screen.blit(self.background, (0, 0))

        # The plant draws itself - this works the same for every kind of plant.
        screen.set_clip(SCENE)
        self.plant.draw(screen, PLANT_BASE)
        screen.set_clip(None)

        self.draw_side_panel()
        self.draw_info_panel()

    def text(self, words, pos, font=None, colour=TEXT):
        surface = (font or self.font).render(words, True, colour)
        self.screen.blit(surface, pos)
        return surface.get_rect(topleft=pos)

    def draw_side_panel(self):
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, PANEL_WIDTH, HEIGHT))
        pygame.draw.line(self.screen, BORDER, (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, HEIGHT), 2)
        self.text("Plant Growth", (20, 18), self.title_font)
        self.text("Inheritance & polymorphism", (20, 54), self.small_font, MUTED)

        self.text("1. Choose a plant", (20, 85), self.heading_font)
        for i, button in enumerate(self.plant_buttons):
            button.draw(self.screen, self.font, selected=(i == self.selected))

        self.text("2. Grow it", (20, self.grow_button.rect.top - 27), self.heading_font)
        mature = self.plant.is_mature()
        self.grow_button.label = "Fully grown!" if mature else "Grow one step"
        self.grow_button.draw(self.screen, self.heading_font, enabled=not mature, primary=True)
        self.reset_button.draw(self.screen, self.small_font)

        # The class hierarchy of the current plant, straight from Python.
        y = self.reset_button.rect.bottom + 22
        self.text("Class hierarchy", (20, y), self.heading_font)
        y += 26
        for cls in type(self.plant).__mro__:
            if cls is object:
                break
            parent = cls.__bases__[0]
            line = f"class {cls.__name__}" + ("" if parent is object else f"({parent.__name__})")
            self.text(line, (20, y), self.code_font, ACCENT if cls is type(self.plant) else TEXT)
            y += 20

        self.text("Keys: Space = grow, R = restart,", (20, HEIGHT - 46), self.small_font, MUTED)
        self.text("1-5 = choose a plant", (20, HEIGHT - 28), self.small_font, MUTED)

    def draw_info_panel(self):
        plant = self.plant
        pygame.draw.rect(self.screen, INFO_BG, INFO)
        pygame.draw.line(self.screen, BORDER, INFO.topleft, INFO.topright, 2)
        left, top = INFO.left + 20, INFO.top + 10

        name = self.text(plant.name, (left, top), self.heading_font)
        self.text(f"Stage: {plant.stage()}", (name.right + 20, top + 1), self.font, ACCENT)
        step_text = self.font.render(f"Step {plant.step} of {plant.max_steps}", True, MUTED)
        self.screen.blit(step_text, step_text.get_rect(topright=(INFO.right - 20, top + 1)))

        bar = pygame.Rect(left, top + 28, INFO.width - 40, 8)
        pygame.draw.rect(self.screen, DISABLED, bar, border_radius=4)
        filled = bar.copy()
        filled.width = round(bar.width * plant.step / plant.max_steps)
        if filled.width:
            pygame.draw.rect(self.screen, ACCENT, filled, border_radius=4)

        # Every part answers describe() in its own way. Parts of the same class
        # are grouped, e.g.  Leaf   8 × 52 px long,  2 × 35 px long
        groups = {}
        for part in plant.parts():
            groups.setdefault(type(part).__name__, []).append(part)
        y = top + 46
        for class_name, parts in groups.items():
            counts = Counter(part.describe() for part in parts)
            summary = ",  ".join(text if n == 1 else f"{n} × {text}" for text, n in counts.items())
            self.text(class_name, (left, y + 1), self.code_font, MUTED)
            self.text(summary, (left + 140, y), self.font)
            y += 20

        self.text(self.message, (left, INFO.bottom - 24), self.code_font, ACCENT)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_event(event)
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)


if __name__ == "__main__":
    App().run()
