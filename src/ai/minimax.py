"""
Modul Minimax dengan Alpha-Beta Pruning untuk Quoridor.

Mengimplementasikan algoritma adversarial search inti (Bab 2.1.4 Tabel 2),
dengan optimasi:
- Depth-Limited Search (default 3 ply, dapat diatur sebagai difficulty).
- Alpha-Beta Pruning untuk memangkas cabang yang tidak relevan (Bab 2.1.4).
- Candidate Filtering: hanya mempertimbangkan dinding yang berpotongan
  dengan jalur terpendek (Bab 2.1.5 Strategi Scaling).
- Node counting untuk panel statistik GUI.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .evaluation import (
    Playstyle,
    evaluate_state,
    evaluate_wall_placement,
)
from .pathfinding import get_shortest_path
from ..game.moves import MoveGenerator
from ..game.rules import Rules


class QuoridorAI:
    """
    Agen AI Quoridor berbasis Minimax + Alpha-Beta Pruning.

    Parameter:
    - max_depth: kedalaman pencarian (ply). 3 adalah default rekomendasi.
    - playstyle: vektor bobot evaluasi (AGGRESSIVE / DEFENSIVE / BALANCED).

    Atribut publik (untuk panel statistik GUI):
    - nodes_evaluated: jumlah node yang dievaluasi pada panggilan terakhir.
    - nodes_pruned: perkiraan jumlah node yang dipangkas Alpha-Beta.
    - last_search_time_ms: waktu pencarian dalam milidetik.
    """

    def __init__(self, max_depth: int = 3, playstyle=None):
        self.max_depth = max_depth
        self.playstyle = playstyle  # boleh str, Playstyle, tuple, atau None
        self.nodes_evaluated: int = 0
        self.nodes_pruned: int = 0
        self.last_search_time_ms: float = 0.0

    def set_playstyle(self, playstyle) -> None:
        """
        Dynamic Playstyle (Bab 2.1.1): ganti bobot evaluasi secara runtime
        tanpa membuat ulang objek AI. Dipanggil oleh tombol GUI.
        """
        self.playstyle = playstyle

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_best_move(self, state, player_idx: int) -> Optional[Tuple]:
        """
        Mengembalikan aksi terbaik untuk player_idx pada state saat ini.

        Return: tuple aksi seperti ('move', (r, c)) atau ('wall', (r, c, 'H')).
                None jika tidak ada aksi legal (seharusnya tidak terjadi).
        """
        import time

        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        t0 = time.perf_counter()

        # Dapatkan daftar aksi yang difilter (candidate filtering)
        moves = self._get_filtered_moves(state, player_idx)
        if not moves:
            return None

        # Urutkan aksi untuk meningkatkan efektivitas Alpha-Beta (move ordering)
        moves = self._order_moves(state, moves, player_idx)

        best_move = moves[0]
        best_value = float("-inf")
        alpha = float("-inf")
        beta = float("inf")

        for action in moves:
            child = state.clone()
            child.apply_move(action, player_idx)
            # Giliran berganti setelah apply_move; opponent jadi minimizer
            value = self._minimax(child, self.max_depth - 1, alpha, beta, False, player_idx)
            if value > best_value:
                best_value = value
                best_move = action
            alpha = max(alpha, value)

        self.last_search_time_ms = (time.perf_counter() - t0) * 1000.0
        return best_move

    # ------------------------------------------------------------------
    # Inti Minimax + Alpha-Beta
    # ------------------------------------------------------------------

    def _minimax(
        self,
        state,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        ai_player_idx: int,
    ) -> float:
        """
        Rekursi Minimax dengan Alpha-Beta Pruning.

        - maximizing True: giliran AI (maximizer)
        - maximizing False: giliran lawan (minimizer)
        - ai_player_idx: indeks pemain AI (tidak berubah selama pencarian)
        """
        self.nodes_evaluated += 1

        # Terminal test atau depth limit
        if depth == 0 or self._is_terminal(state):
            return evaluate_state(state, ai_player_idx, self.playstyle)

        current_player = state.current_player
        moves = self._get_filtered_moves(state, current_player)
        if not moves:
            return evaluate_state(state, ai_player_idx, self.playstyle)

        # Move ordering untuk mempercepat pruning
        moves = self._order_moves(state, moves, current_player)

        if maximizing:
            value = float("-inf")
            for action in moves:
                child = state.clone()
                child.apply_move(action, current_player)
                value = max(
                    value,
                    self._minimax(child, depth - 1, alpha, beta, False, ai_player_idx),
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    self.nodes_pruned += 1
                    break  # Beta cutoff
            return value
        else:
            value = float("inf")
            for action in moves:
                child = state.clone()
                child.apply_move(action, current_player)
                value = min(
                    value,
                    self._minimax(child, depth - 1, alpha, beta, True, ai_player_idx),
                )
                beta = min(beta, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break  # Alpha cutoff
            return value

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_terminal(self, state) -> bool:
        """Cek apakah state adalah terminal state (salah satu pemain menang)."""
        return state.is_winner(0) or state.is_winner(1)

    def _get_filtered_moves(self, state, player_idx: int) -> List:
        """
        Candidate Filtering (Bab 2.1.5): hanya mempertimbangkan penempatan
        dinding yang berpotongan dengan jalur terpendek salah satu pemain.
        Aksi pion selalu disertakan.

        Ini mengurangi branching factor dari ~132 menjadi ~20-30 per state,
        membuat depth 3 feasible secara real-time.
        """
        pawn_moves = MoveGenerator._get_pawn_moves(state, player_idx)

        if state.walls_remaining[player_idx] <= 0:
            return pawn_moves

        # Ambil sel-sel yang dilalui jalur terpendek kedua pemain
        path_ai = set(get_shortest_path(state, player_idx))
        path_opp = set(get_shortest_path(state, 1 - player_idx))
        critical_cells = path_ai.union(path_opp)

        # Jika salah satu pemain tidak punya jalur (kasus degenerate),
        # fallback ke semua kandidat
        if not critical_cells:
            return MoveGenerator.get_legal_moves(state, player_idx)

        wall_moves = []
        for r in range(8):
            for c in range(8):
                # Titik persimpangan (r,c) memotong sel-sel:
                # (r,c), (r,c+1), (r+1,c), (r+1,c+1)
                touched = {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}
                if not touched.intersection(critical_cells):
                    continue

                for orientation in ("H", "V"):
                    if Rules.is_wall_valid(state, r, c, orientation, player_idx):
                        wall_moves.append(("wall", (r, c, orientation)))

        return pawn_moves + wall_moves

    def _order_moves(self, state, moves: List, player_idx: int) -> List:
        """
        Move ordering sederhana: urutkan aksi berdasarkan skor heuristik
        cepat agar Alpha-Beta memangkas lebih banyak cabang di awal.

        Aksi pion diurutkan berdasarkan kedekatan ke target row.
        Aksi dinding diurutkan berdasarkan evaluate_wall_placement.
        """
        opp_idx = 1 - player_idx

        def score(action):
            kind, payload = action
            if kind == "move":
                r, c = payload
                # Lebih dekat ke target row = lebih baik
                target = 8 if player_idx == 0 else 0
                return -(abs(r - target))  # negate agar besar duluan
            else:
                r, c, orient = payload
                return evaluate_wall_placement(state, r, c, orient, player_idx)

        return sorted(moves, key=score, reverse=True)