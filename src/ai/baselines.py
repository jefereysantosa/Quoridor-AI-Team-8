"""
Modul Baseline Agent untuk evaluasi M5.

Mengimplementasikan:
- RandomAgent: memilih aksi legal secara acak (lower bound).
- GreedyAgent: selalu bergerak meminimalkan jalurnya sendiri,
               tanpa memasang dinding (Bab 2.2 bagian A.1 proposal).

Baseline ini BUKAN otak AI utama; hanya dipakai untuk turnamen evaluasi
di milestone M5 melawan QuoridorAI.
"""

from __future__ import annotations

import random
from typing import Optional, Tuple

from .pathfinding import astar_distance
from ..game.moves import MoveGenerator


class RandomAgent:
    """Baseline lower bound. Pilih aksi legal secara acak."""

    def get_move(self, state, player_idx: int) -> Optional[Tuple]:
        moves = MoveGenerator.get_legal_moves(state, player_idx)
        if not moves:
            return None
        return random.choice(moves)


class GreedyAgent:
    """
    Baseline naif: selalu mengambil aksi pion yang paling memperpendek
    jalurnya sendiri ke target row. Tidak pernah memasang dinding.

    Mudah dieksploitasi oleh QuoridorAI (target win rate >= 70%
    pada Tabel 3 proposal).
    """

    def get_move(self, state, player_idx: int) -> Optional[Tuple]:
        pawn_moves = MoveGenerator._get_pawn_moves(state, player_idx)
        if not pawn_moves:
            return None

        target = 8 if player_idx == 0 else 0

        def closeness(action):
            _, (r, c) = action
            return abs(r - target)

        # Pilih yang paling dekat target
        return min(pawn_moves, key=closeness)