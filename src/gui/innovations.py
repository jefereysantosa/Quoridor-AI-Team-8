"""
Widget pygame untuk tiga fitur inovasi M4.

Dirancang agar main.py milik Jason cukup memanggil tiga kelas ini
tanpa mengubah modul game maupun ai:
- GhostOverlay      : render bayangan transparan balasan AI
- HintPanel         : panel teks alasan Explainable Hint
- PlaystyleButtons  : tombol pemilih Dynamic Playstyle
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import pygame

from ..ai.explain import format_hint_text
from ..ai.ghost import GhostPrediction
from ..ai.playstyle import list_playstyles
from .panels import wrap_text


class GhostOverlay:
    """Menggambar bayangan semi-transparan (Ghost Step) di atas papan."""

    ALPHA = 100
    DASHES = 10

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
        # Garis putus-putus sesuai Gambar 4 proposal
        for i in range(0, self.DASHES * 2, 2):
            a0 = 2 * math.pi * i / (self.DASHES * 2)
            a1 = 2 * math.pi * (i + 1) / (self.DASHES * 2)
            p0 = (center[0] + radius * math.cos(a0), center[1] + radius * math.sin(a0))
            p1 = (center[0] + radius * math.cos(a1), center[1] + radius * math.sin(a1))
            pygame.draw.line(surf, (*color, 230), p0, p1, 2)
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
        # Tepi putus-putus pada sisi panjang dinding
        w, h = rect.size
        for start in range(0, max(w, h), 12):
            end = min(start + 6, max(w, h))
            if orient == "H":
                pygame.draw.line(surf, (*color, 230), (start, 0), (end, 0))
                pygame.draw.line(surf, (*color, 230), (start, h - 1), (end, h - 1))
            else:
                pygame.draw.line(surf, (*color, 230), (0, start), (0, end))
                pygame.draw.line(surf, (*color, 230), (w - 1, start), (w - 1, end))
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
        self.hint = None

    def set_hint(self, hint) -> None:
        self.hint = hint
        self.lines = []
        for text in format_hint_text(hint):
            self.lines.extend(wrap_text(text, self.font, self.rect.width - 24))

    def clear(self) -> None:
        self.hint = None
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