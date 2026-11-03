"""
Widget pygame untuk tiga fitur inovasi M4.

Dirancang agar main.py milik Jason cukup memanggil tiga kelas ini
tanpa mengubah modul game maupun ai:
- GhostOverlay      : render bayangan transparan balasan AI
- HintPanel         : panel teks alasan Explainable Hint
- PlaystyleButtons  : tombol pemilih Dynamic Playstyle
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from ..ai.explain import format_hint_text
from ..ai.ghost import GhostPrediction
from ..ai.playstyle import list_playstyles


class GhostOverlay:
    """Menggambar bayangan semi-transparan (Ghost Step) di atas papan."""

    ALPHA = 100

    def __init__(self, cell_size: int = 64, origin: Tuple[int, int] = (40, 40)):
        self.cell = cell_size
        self.ox, self.oy = origin

    def _cell_rect(self, r: int, c: int) -> pygame.Rect:
        return pygame.Rect(
            self.ox + c * self.cell, self.oy + r * self.cell, self.cell, self.cell
        )

    def draw_pawn_ghost(self, screen, pos: Tuple[int, int], color=(220, 70, 70)):
        rect = self._cell_rect(*pos)
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        center = (rect.width // 2, rect.height // 2)
        radius = int(self.cell * 0.36)
        pygame.draw.circle(surf, (*color, self.ALPHA), center, radius)
        pygame.draw.circle(surf, (*color, 210), center, radius, 2)
        screen.blit(surf, rect.topleft)

    def draw_wall_ghost(self, screen, r: int, c: int, orient: str, color=(220, 70, 70)):
        if orient == "H":
            rect = pygame.Rect(
                self.ox + c * self.cell, self.oy + (r + 1) * self.cell - 4,
                2 * self.cell, 8,
            )
        else:
            rect = pygame.Rect(
                self.ox + (c + 1) * self.cell - 4, self.oy + r * self.cell,
                8, 2 * self.cell,
            )
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill((*color, self.ALPHA))
        screen.blit(surf, rect.topleft)

    def draw_prediction(self, screen, prediction: Optional[GhostPrediction]):
        if prediction is None or prediction.ai_response is None:
            return
        kind, payload = prediction.ai_response
        if kind == "move":
            self.draw_pawn_ghost(screen, payload)
        else:
            r, c, orient = payload
            self.draw_wall_ghost(screen, r, c, orient)


class HintPanel:
    """Panel teks untuk alasan numerik Explainable Hint."""

    def __init__(self, rect: pygame.Rect, font: Optional[pygame.font.Font] = None):
        self.rect = rect
        self.font = font or pygame.font.SysFont("consolas", 16)
        self.lines: List[str] = []

    def set_hint(self, hint) -> None:
        self.lines = format_hint_text(hint)

    def clear(self) -> None:
        self.lines = []

    def draw(self, screen):
        pygame.draw.rect(screen, (24, 26, 34), self.rect, border_radius=8)
        pygame.draw.rect(screen, (90, 95, 110), self.rect, width=1, border_radius=8)
        y = self.rect.top + 10
        for i, line in enumerate(self.lines):
            color = (255, 214, 102) if i == 0 else (225, 228, 235)
            surf = self.font.render(line, True, color)
            screen.blit(surf, (self.rect.left + 12, y))
            y += surf.get_height() + 4
            if y > self.rect.bottom - 20:
                break


class PlaystyleButtons:
    """Tiga tombol Dynamic Playstyle: Aggressive, Defensive, Balanced."""

    def __init__(self, rect: pygame.Rect, font: Optional[pygame.font.Font] = None):
        self.rect = rect
        self.font = font or pygame.font.SysFont("consolas", 14, bold=True)
        styles = list_playstyles()
        w = rect.width // len(styles)
        self.buttons = []
        for i, st in enumerate(styles):
            r = pygame.Rect(rect.left + i * w, rect.top, w, rect.height)
            self.buttons.append((st.name.lower(), st.name, r))

    def handle_event(self, event) -> Optional[str]:
        """Return kunci playstyle bila ada tombol diklik, selain itu None."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        for key, _name, rect in self.buttons:
            if rect.collidepoint(event.pos):
                return key
        return None

    def draw(self, screen, active_key: str):
        for key, name, rect in self.buttons:
            active = key == active_key
            fill = (70, 120, 200) if active else (45, 48, 60)
            pygame.draw.rect(screen, fill, rect, border_radius=6)
            pygame.draw.rect(screen, (120, 126, 145), rect, width=1, border_radius=6)
            label = self.font.render(name, True, (240, 240, 245))
            screen.blit(label, label.get_rect(center=rect.center))