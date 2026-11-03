"""
Modul Explainable Hint (Inovasi 3, Bab 2.1.1 dan Glossary butir 7).

Menghasilkan saran langkah disertai alasan numerik yang diturunkan
langsung dari perhitungan heuristik, sehingga keputusan AI transparan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .evaluation import evaluate_state, wall_placement_breakdown
from .minimax import QuoridorAI
from .pathfinding import astar_distance


@dataclass
class Hint:
    action: Tuple
    score: float
    reasons: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


def _fmt(v: float) -> str:
    if v == float("inf"):
        return "MENANG"
    if v == float("-inf"):
        return "KALAH"
    return f"{v:+.2f}"


def describe_action(action: Tuple) -> str:
    """Deskripsi aksi dalam bahasa manusia untuk panel hint."""
    kind, payload = action
    if kind == "move":
        r, c = payload
        return f"gerak pion ke sel (baris {r + 1}, kolom {c + 1})"
    r, c, orient = payload
    nama = "horizontal" if orient == "H" else "vertikal"
    return f"pasang dinding {nama} di slot persimpangan ({r + 1}, {c + 1})"


def generate_hint(
    state, player_idx: int, depth: int = 3, playstyle=None
) -> Hint:
    """
    Menjalankan pencarian penuh lalu merangkai alasan numerik.
    Contoh keluaran alasan:
      "Memotong jalur terpendek lawan sebanyak 3 langkah (dari 5 menjadi 8)."
      "Jalur Anda sendiri tidak terpengaruh oleh dinding ini."
    """
    ai = QuoridorAI(max_depth=depth, playstyle=playstyle)
    action = ai.get_best_move(state, player_idx)
    if action is None:
        return Hint(action=None, score=0.0, reasons=["Tidak ada aksi legal."])

    reasons: List[str] = []
    metrics: Dict = {}
    opp_idx = 1 - player_idx
    kind, payload = action

    if kind == "move":
        d_self_before = astar_distance(state, player_idx)
        d_opp_before = astar_distance(state, opp_idx)
        child = state.clone()
        child.apply_move(action, player_idx)
        d_self_after = astar_distance(child, player_idx)
        d_opp_after = astar_distance(child, opp_idx)
        metrics.update(
            d_self_before=d_self_before,
            d_self_after=d_self_after,
            d_opp_before=d_opp_before,
            d_opp_after=d_opp_after,
        )
        reasons.append(
            f"Jarak Anda ke garis tujuan berubah dari {d_self_before} "
            f"menjadi {d_self_after} langkah."
        )
        reasons.append(
            f"Posisi perlombaan jalur setelah langkah: Anda {d_self_after} "
            f"vs lawan {d_opp_after}."
        )
        if d_self_after <= d_opp_after:
            reasons.append(
                "Langkah ini menjaga atau merebut keunggulan jalur atas lawan."
            )
    else:
        r, c, orient = payload
        bd = wall_placement_breakdown(state, r, c, orient, player_idx)
        metrics.update(bd)
        if bd["path_cut_steps"] > 0:
            reasons.append(
                f"Memotong jalur terpendek lawan sebanyak {bd['path_cut_steps']} "
                f"langkah (dari {bd['d_opp_before']} menjadi {bd['d_opp_after']})."
            )
        if bd["self_penalty_steps"] > 0:
            reasons.append(
                f"Biaya sendiri: jalur Anda bertambah {bd['self_penalty_steps']} langkah."
            )
        else:
            reasons.append("Jalur Anda sendiri tidak terpengaruh oleh dinding ini.")
        if bd["mobility_reduced"] > 0:
            reasons.append(
                f"Menghilangkan {bd['mobility_reduced']} langkah legal lawan."
            )
        if bd["edge"]:
            reasons.append(
                "Penalti tepi diterapkan karena slot berada di pinggiran papan."
            )
        child = state.clone()
        child.apply_move(action, player_idx)

    score = evaluate_state(child, player_idx, playstyle)
    metrics.update(nodes=ai.nodes_evaluated, pruned=ai.nodes_pruned, ms=ai.last_search_time_ms)
    reasons.append(f"Skor evaluasi sesaat setelah aksi: {_fmt(score)}.")
    reasons.append(
        f"Pencarian: {ai.nodes_evaluated} node, {ai.nodes_pruned} dipangkas, "
        f"{ai.last_search_time_ms:.0f} ms."
    )

    return Hint(action=action, score=score, reasons=reasons, metrics=metrics)


def format_hint_text(hint: Hint) -> List[str]:
    """Baris teks siap tampil untuk HintPanel di GUI."""
    if hint.action is None:
        return list(hint.reasons)
    return [f"Saran terbaik: {describe_action(hint.action)}."] + hint.reasons