"""
Modul tampilan papan (modul GUI, Bab 2.1.1 dan Gambar 3-4 proposal).

Menggambar papan 9x9, slot dinding, dinding, dan pion, serta menerjemahkan
posisi mouse menjadi tuple aksi yang sama dengan format MoveGenerator.
"""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pygame

CELL_SIZE = 68
ORIGIN = (32, 76)
WALL_THICKNESS = 8
TILE_INSET = 4
WALL_ZONE = 0.22  # bagian sel dari tepinya yang dianggap area slot dinding

COLOR_BOARD = (38, 31, 25)
COLOR_TILE = (84, 68, 52)
COLOR_GOAL_P0 = (66, 80, 88)
COLOR_GOAL_P1 = (108, 66, 52)
COLOR_WALL = (226, 205, 165)
COLOR_LEGAL = (150, 180, 100)
COLOR_INVALID = (236, 122, 100)
COLOR_PAWN_RING = (30, 25, 20)
PLAYER_COLORS = ((134, 168, 196), (214, 110, 82))


class BoardView:
    """Geometri dan penggambaran papan. Tidak menyimpan state permainan."""

    def __init__(self, cell_size: int = CELL_SIZE, origin: Tuple[int, int] = ORIGIN):
        self.cell = cell_size
        self.ox, self.oy = origin
        self.rect = pygame.Rect(self.ox, self.oy, 9 * cell_size, 9 * cell_size)

    def hit_test(self, pos: Tuple[int, int]) -> Optional[Tuple]:
        """
        Mengubah posisi mouse menjadi ('move', (r, c)) atau ('wall', (r, c, 'H'|'V')).
        Return None bila di luar papan.
        """
        if not self.rect.collidepoint(pos):
            return None
        x = (pos[0] - self.ox) / self.cell
        y = (pos[1] - self.oy) / self.cell
        col, row = int(x), int(y)
        fx, fy = x - col, y - row

        # Garis batas terdekat dan jaraknya; tepi luar papan bukan slot dinding
        row_line = row if fy < 0.5 else row + 1
        col_line = col if fx < 0.5 else col + 1
        dist_h = min(fy, 1 - fy)
        dist_v = min(fx, 1 - fx)
        near_h = 1 <= row_line <= 8 and dist_h < WALL_ZONE
        near_v = 1 <= col_line <= 8 and dist_v < WALL_ZONE

        if near_h and (not near_v or dist_h <= dist_v):
            c = max(0, min(7, int(x + 0.5) - 1))
            return ("wall", (row_line - 1, c, "H"))
        if near_v:
            r = max(0, min(7, int(y + 0.5) - 1))
            return ("wall", (r, col_line - 1, "V"))
        return ("move", (row, col))

    def _tile_rect(self, r: int, c: int) -> pygame.Rect:
        return pygame.Rect(
            self.ox + c * self.cell + TILE_INSET,
            self.oy + r * self.cell + TILE_INSET,
            self.cell - 2 * TILE_INSET,
            self.cell - 2 * TILE_INSET,
        )

    def _wall_rect(self, r: int, c: int, orient: str) -> pygame.Rect:
        half = WALL_THICKNESS // 2
        if orient == "H":
            return pygame.Rect(
                self.ox + c * self.cell + TILE_INSET,
                self.oy + (r + 1) * self.cell - half,
                2 * self.cell - 2 * TILE_INSET,
                WALL_THICKNESS,
            )
        return pygame.Rect(
            self.ox + (c + 1) * self.cell - half,
            self.oy + r * self.cell + TILE_INSET,
            WALL_THICKNESS,
            2 * self.cell - 2 * TILE_INSET,
        )

    def draw_board(self, screen) -> None:
        pygame.draw.rect(screen, COLOR_BOARD, self.rect.inflate(16, 16), border_radius=10)
        for r in range(9):
            for c in range(9):
                # Baris tujuan diberi warna pemain yang harus mencapainya
                color = COLOR_GOAL_P1 if r == 0 else COLOR_GOAL_P0 if r == 8 else COLOR_TILE
                pygame.draw.rect(screen, color, self._tile_rect(r, c), border_radius=8)

    def draw_legal_moves(self, screen, moves: Iterable[Tuple], hover: Optional[Tuple]) -> None:
        for action in moves:
            r, c = action[1]
            width = 3 if action == hover else 2
            pygame.draw.rect(screen, COLOR_LEGAL, self._tile_rect(r, c), width=width, border_radius=8)

    def draw_walls(self, screen, state, fresh: Optional[Tuple[Tuple, float]] = None) -> None:
        fresh_wall = fresh[0] if fresh else None
        for r in range(8):
            for c in range(8):
                for orient, grid in (("H", state.h_walls), ("V", state.v_walls)):
                    if not grid[r][c]:
                        continue
                    if (r, c, orient) == fresh_wall:
                        self.draw_translucent_wall(screen, r, c, orient, COLOR_WALL, int(255 * fresh[1]))
                    else:
                        pygame.draw.rect(screen, COLOR_WALL, self._wall_rect(r, c, orient), border_radius=3)

    def draw_translucent_wall(self, screen, r: int, c: int, orient: str, color, alpha: int) -> None:
        rect = self._wall_rect(r, c, orient)
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*color, alpha), surf.get_rect(), border_radius=3)
        screen.blit(surf, rect.topleft)

    def draw_wall_preview(self, screen, payload: Tuple, valid: bool) -> None:
        r, c, orient = payload
        self.draw_translucent_wall(screen, r, c, orient, COLOR_LEGAL if valid else COLOR_INVALID, 200)

    def draw_pawn(self, screen, pos: Tuple[float, float], player_idx: int) -> None:
        r, c = pos
        center = (
            int(self.ox + (c + 0.5) * self.cell),
            int(self.oy + (r + 0.5) * self.cell),
        )
        radius = int(self.cell * 0.32)
        pygame.draw.circle(screen, PLAYER_COLORS[player_idx], center, radius)
        pygame.draw.circle(screen, COLOR_PAWN_RING, center, radius, 2)
