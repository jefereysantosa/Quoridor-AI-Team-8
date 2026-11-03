"""
Modul Ghost Step (Inovasi 2, Bab 2.1.1 dan Glossary butir 5).

Memprediksi balasan terbaik AI terhadap kandidat langkah yang SEDANG
dipertimbangkan pemain manusia, sebelum langkah itu dikonfirmasi.
Hasilnya dirender semi-transparan oleh src/gui/innovations.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .evaluation import evaluate_state
from .minimax import QuoridorAI


@dataclass
class GhostPrediction:
    human_action: Tuple
    ai_response: Optional[Tuple]
    depth: int
    eval_setelah_langkah_manusia: float
    eval_setelah_balasan_ai: float
    nodes: int
    ms: float


_CACHE: Dict[Tuple, GhostPrediction] = {}


def _state_key(state) -> Tuple:
    """Kunci hashable untuk cache prediksi."""
    return (
        tuple(state.pawns),
        tuple(state.walls_remaining),
        state.current_player,
        tuple(tuple(row) for row in state.h_walls),
        tuple(tuple(row) for row in state.v_walls),
    )


def predict_response(
    state,
    human_action: Tuple,
    human_idx: int,
    depth: int = 1,
    playstyle=None,
    use_cache: bool = True,
) -> GhostPrediction:
    """
    Mensimulasikan langkah manusia, lalu mencari balasan terbaik AI
    dengan Minimax kedalaman `depth` (default 1 agar responsif di GUI).

    Nilai evaluasi dilaporkan dari perspektif manusia, sehingga GUI dapat
    menampilkan peringatan bila balasan AI membuat posisi manusia memburuk.
    """
    key = (_state_key(state), human_action, human_idx, depth)
    if use_cache and key in _CACHE:
        return _CACHE[key]

    child = state.clone()
    child.apply_move(human_action, human_idx)
    ai_idx = 1 - human_idx

    ai = QuoridorAI(max_depth=depth, playstyle=playstyle)
    response = ai.get_best_move(child, ai_idx)

    eval_human = evaluate_state(child, human_idx, playstyle)
    if response is not None:
        grand = child.clone()
        grand.apply_move(response, ai_idx)
        eval_after = evaluate_state(grand, human_idx, playstyle)
    else:
        eval_after = eval_human

    pred = GhostPrediction(
        human_action=human_action,
        ai_response=response,
        depth=depth,
        eval_setelah_langkah_manusia=eval_human,
        eval_setelah_balasan_ai=eval_after,
        nodes=ai.nodes_evaluated,
        ms=ai.last_search_time_ms,
    )
    if use_cache:
        _CACHE[key] = pred
    return pred


def clear_ghost_cache() -> None:
    """Wajib dipanggil setiap state benar-benar berubah (langkah dikonfirmasi)."""
    _CACHE.clear()