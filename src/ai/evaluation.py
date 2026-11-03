"""
Modul Evaluasi Heuristik untuk Quoridor.
Rumus Eval(s) dari Bab 2.1.4 bagian A dan Wall Scoring dari bagian B.
"""

from __future__ import annotations

from typing import Dict

from .pathfinding import astar_distance
from .playstyle import Playstyle, resolve_weights
from .playstyle import PlaystyleLike
from ..game.moves import MoveGenerator

__all__ = [
    "Playstyle",
    "evaluate_state",
    "evaluate_wall_placement",
    "wall_placement_breakdown",
]


def _count_mobility(state, player_idx: int) -> int:
    """Variabel M: jumlah langkah legal pion."""
    return len(MoveGenerator._get_pawn_moves(state, player_idx))


def evaluate_state(state, player_idx: int, playstyle: PlaystyleLike = None) -> float:
    """
    Eval(s) = w_d*(D_Opp - D_AI) + w_w*(W_AI - W_Opp) + w_m*(M_AI - M_Opp)
    Positif menguntungkan player_idx, negatif menguntungkan lawan.
    """
    w_d, w_w, w_m = resolve_weights(playstyle)
    opp_idx = 1 - player_idx

    d_ai = astar_distance(state, player_idx)
    d_opp = astar_distance(state, opp_idx)
    if d_ai == 0:
        return float("inf")
    if d_opp == 0:
        return float("-inf")

    w_ai = state.walls_remaining[player_idx]
    w_opp = state.walls_remaining[opp_idx]
    m_ai = _count_mobility(state, player_idx)
    m_opp = _count_mobility(state, opp_idx)

    return float(
        w_d * (d_opp - d_ai) + w_w * (w_ai - w_opp) + w_m * (m_ai - m_opp)
    )


def wall_placement_breakdown(
    state, r: int, c: int, orientation: str, player_idx: int
) -> Dict:
    """
    Rincian skor kandidat dinding per kriteria Bab 2.1.4 bagian B.
    Dipakai oleh evaluate_wall_placement dan oleh Explainable Hint
    untuk menyusun alasan numerik yang dapat dibaca manusia.
    """
    opp_idx = 1 - player_idx

    d_opp_before = astar_distance(state, opp_idx)
    d_ai_before = astar_distance(state, player_idx)
    m_opp_before = _count_mobility(state, opp_idx)

    if orientation == "H":
        state.h_walls[r][c] = True
    else:
        state.v_walls[r][c] = True

    d_opp_after = astar_distance(state, opp_idx)
    d_ai_after = astar_distance(state, player_idx)
    m_opp_after = _count_mobility(state, opp_idx)

    if orientation == "H":
        state.h_walls[r][c] = False
    else:
        state.v_walls[r][c] = False

    path_cut_steps = max(0, d_opp_after - d_opp_before)
    self_penalty_steps = max(0, d_ai_after - d_ai_before)
    mobility_reduced = max(0, m_opp_before - m_opp_after)
    edge = r in (0, 6) or c in (0, 6)

    score_path_cut = 5.0 if path_cut_steps > 0 else 0.0
    score_self = -4.0 * self_penalty_steps
    score_mob = 0.2 * mobility_reduced
    score_edge = -0.25 if edge else 0.0

    return {
        "d_opp_before": d_opp_before,
        "d_opp_after": d_opp_after,
        "d_ai_before": d_ai_before,
        "d_ai_after": d_ai_after,
        "path_cut_steps": path_cut_steps,
        "self_penalty_steps": self_penalty_steps,
        "mobility_reduced": mobility_reduced,
        "edge": edge,
        "score_path_cut": score_path_cut,
        "score_self": score_self,
        "score_mob": score_mob,
        "score_edge": score_edge,
        "total": score_path_cut + score_self + score_mob + score_edge,
    }


def evaluate_wall_placement(
    state, r: int, c: int, orientation: str, player_idx: int
) -> float:
    """Skor total kandidat dinding (jumlah seluruh kriteria)."""
    return wall_placement_breakdown(state, r, c, orientation, player_idx)["total"]