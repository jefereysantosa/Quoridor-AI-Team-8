"""
Modul Baseline Agent untuk evaluasi M5.

Mengimplementasikan:
- RandomAgent: memilih aksi legal secara acak (lower bound).
- GreedyAgent: selalu bergerak meminimalkan jalur terpendeknya sendiri (A*),
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
    jalur terpendeknya sendiri ke target row. Tidak pernah memasang dinding.

    Mudah dieksploitasi oleh QuoridorAI (target win rate >= 70%
    pada Tabel 3 proposal).
    """

    def get_move(self, state, player_idx: int) -> Optional[Tuple]:
        pawn_moves = MoveGenerator._get_pawn_moves(state, player_idx)
        if not pawn_moves:
            return None

        # Pilih aksi pion yang membuat jalur terpendek (A*) paling singkat,
        # sehingga agen tetap benar saat dinding lawan memaksa memutar.
        def remaining_distance(action):
            child = state.clone()
            child.apply_move(action, player_idx)
            return astar_distance(child, player_idx)

        return min(pawn_moves, key=remaining_distance)
