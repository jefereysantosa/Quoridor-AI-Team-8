"""
Modul Evaluasi Heuristik untuk Quoridor.

Mengimplementasikan:
- Playstyle: preset bobot untuk Dynamic Playstyle (Bab 2.1.1 proposal).
- evaluate_state: rumus Eval(s) persis dari Bab 2.1.4 bagian A.
- evaluate_wall_placement: skor kandidat dinding (Bab 2.1.4 bagian B).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .pathfinding import astar_distance
from ..game.moves import MoveGenerator


@dataclass(frozen=True)
class Playstyle:
    """
    Preset vektor bobot untuk Dynamic Playstyle (inovasi pertama).
    Pemain manusia dapat memilih lewat GUI; bobot langsung memengaruhi
    perilaku strategis AI secara real-time (Bab 2.1.1 proposal).
    """

    AGGRESSIVE: Tuple[float, float, float] = (1.5, 0.2, 0.1)
    DEFENSIVE: Tuple[float, float, float] = (0.7, 0.9, 0.4)
    BALANCED: Tuple[float, float, float] = (1.0, 0.5, 0.25)

    # Bobot default sesuai rumus proposal
    DEFAULT = BALANCED


def _count_mobility(state, player_idx: int) -> int:
    """
    Menghitung jumlah langkah legal pion (variabel M dalam rumus).
    Catatan: hanya gerak pion, bukan penempatan dinding.
    """
    moves = MoveGenerator._get_pawn_moves(state, player_idx)
    return len(moves)


def evaluate_state(state, player_idx: int, playstyle: Tuple[float, float, float] = None) -> float:
    """
    Evaluasi heuristik state dari perspektif player_idx.

    Rumus dari Bab 2.1.4 bagian A proposal:
        Eval(s) = (D_Opp - D_AI) + 0.5(W_AI - W_Opp) + 0.25(M_AI - M_Opp)

    Dengan bobot yang dapat diatur lewat Dynamic Playstyle.

    Return: nilai float. Positif = menguntungkan AI, negatif = lawan.
    """
    if playstyle is None:
        w_d, w_w, w_m = Playstyle.DEFAULT
    else:
        w_d, w_w, w_m = playstyle

    opp_idx = 1 - player_idx

    # Variabel D: panjang jalur terpendek (A*)
    d_ai = astar_distance(state, player_idx)
    d_opp = astar_distance(state, opp_idx)

    # Jika salah satu pemain sudah menang, return nilai terminal
    if d_ai == 0:
        return float("inf")
    if d_opp == 0:
        return float("-inf")

    # Variabel W: sisa dinding
    w_ai = state.walls_remaining[player_idx]
    w_opp = state.walls_remaining[opp_idx]

    # Variabel M: mobilitas pion
    m_ai = _count_mobility(state, player_idx)
    m_opp = _count_mobility(state, opp_idx)

    # Rumus utama (persis seperti proposal)
    score = (
        w_d * (d_opp - d_ai)
        + w_w * (w_ai - w_opp)
        + w_m * (m_ai - m_opp)
    )

    return float(score)


def evaluate_wall_placement(
    state,
    r: int,
    c: int,
    orientation: str,
    player_idx: int,
) -> float:
    """
    Menghitung skor kandidat penempatan dinding (Bab 2.1.4 bagian B proposal).

    Kriteria:
    - Path Cutting bonus +5: dinding memperpanjang jalur lawan.
    - Self-Path Penalty -4 per langkah: dinding memperpanjang jalur sendiri.
    - Mobility Restriction +0.2 per langkah legal lawan yang hilang.
    - Edge Penalty -0.25 untuk dinding di tepi papan.

    Dinding disimulasikan sementara, dihitung efeknya, lalu dikembalikan.
    Catatan: pemanggil WAJIB memastikan dinding legal (Rules.is_wall_valid)
    sebelum memanggil fungsi ini.
    """
    opp_idx = 1 - player_idx

    # Snapshot sebelum simulasi
    d_opp_before = astar_distance(state, opp_idx)
    d_ai_before = astar_distance(state, player_idx)
    m_opp_before = _count_mobility(state, opp_idx)

    # Pasang dinding sementara
    if orientation == "H":
        state.h_walls[r][c] = True
    else:
        state.v_walls[r][c] = True

    d_opp_after = astar_distance(state, opp_idx)
    d_ai_after = astar_distance(state, player_idx)
    m_opp_after = _count_mobility(state, opp_idx)

    # Lepas dinding
    if orientation == "H":
        state.h_walls[r][c] = False
    else:
        state.v_walls[r][c] = False

    # Hitung skor
    score = 0.0

    # Path Cutting: dinding berhasil memperpanjang jalur lawan
    if d_opp_after > d_opp_before:
        score += 5.0

    # Self-Path Penalty: -4 per langkah yang ditambahkan ke jalur AI sendiri
    self_penalty = d_ai_after - d_ai_before
    if self_penalty > 0:
        score -= 4.0 * self_penalty

    # Mobility Restriction: bonus untuk setiap langkah legal lawan yang hilang
    mobility_reduced = m_opp_before - m_opp_after
    if mobility_reduced > 0:
        score += 0.2 * mobility_reduced

    # Edge Penalty: dinding di tepi papan (anchor r=0/6 atau c=0/6) kurang strategis
    if r == 0 or r == 6 or c == 0 or c == 6:
        score -= 0.25

    return score