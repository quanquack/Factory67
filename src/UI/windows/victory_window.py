import pygame

from src.registry import theme_registry
from .base_window import BaseWindow
from .window_frame import WindowFrame


class VictoryWindow(BaseWindow):
    def __init__(self, screen_w, screen_h):
        frame = WindowFrame(
            screen_w,
            screen_h,
            720,
            420,
            "VICTORY!"
        )

        super().__init__(frame)

        self.continue_rect = None
        self.hovered = False

    def open(self):
        self.frame.open()

    def handle_event(self, event):
        if self.handle_close_event(event):
            return True

        if event.type == pygame.MOUSEMOTION:
            self.hovered = (
                self.continue_rect is not None
                and self.continue_rect.collidepoint(event.pos)
            )

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if (
                self.continue_rect
                and self.continue_rect.collidepoint(event.pos)
            ):
                self.close()
                return True

        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)

        y = (
            self.frame.y
            + self.frame.HEADER_H
            + self.frame.PADDING
            + 10
        )

        text_lines = [
            "CONGRATULATIONS, ENGINEER!",
            "",
            "You have successfully automated the production",
            "and achieved the rate of 10 robots produced per second.",
            "Your factory is a masterpiece of logistics.",
            "",
            "You can stop now, or continue expanding your factory.",
        ]

        for line in text_lines:
            if line.startswith("CONGRATULATIONS"):
                surface = self.frame.font_title.render(
                    line,
                    True,
                    (255, 215, 0)
                )
                y_step = 28
            else:
                surface = self.frame.font.render(
                    line,
                    True,
                    theme_registry.get_color(
                        "windows",
                        "text"
                    )
                )
                y_step = 20

            screen.blit(
                surface,
                (
                    self.frame.x
                    + (
                        self.frame.width
                        - surface.get_width()
                    ) // 2,
                    y
                )
            )

            y += y_step

        y += 15

        button_width = 200

        self.continue_rect = pygame.Rect(
            self.frame.x
            + (self.frame.width - button_width) // 2,
            y,
            button_width,
            self.frame.BTN_H
        )

        self.frame.draw_button(
            screen,
            self.continue_rect,
            "CONTINUE PLAYING",
            hovered=self.hovered
        )