"""Test M3: Minimax, Alpha-Beta, evaluasi, dan Candidate Filtering."""
from src.game.state import State
from src.game.moves import MoveGenerator
from src.ai import QuoridorAI, Playstyle
from src.ai.evaluation import evaluate_state


def test_ai_memilih_aksi_legal():
    s = State()
    ai = QuoridorAI(max_depth=2)
    move = ai.get_best_move(s, 0)
    assert move in MoveGenerator.get_legal_moves(s, 0)


def test_ai_mengambil_kemenangan_satu_langkah():
    s = State()
    s.pawns[0] = (7, 4)
    ai = QuoridorAI(max_depth=2)
    # (8, 4) ditempati pion lawan, jadi kemenangan lewat lompatan diagonal
    kind, (r, _c) = ai.get_best_move(s, 0)
    assert kind == "move" and r == 8


def test_evaluasi_bersifat_zero_sum():
    s = State()
    s.pawns[0] = (3, 4)
    v0 = evaluate_state(s, 0)
    v1 = evaluate_state(s, 1)
    assert v0 > 0
    assert abs(v0 + v1) < 1e-9


def test_candidate_filtering_mengurangi_kandidat_dinding():
    s = State()
    ai = QuoridorAI(max_depth=1)
    filtered = ai._get_filtered_moves(s, 0)
    all_moves = MoveGenerator.get_legal_moves(s, 0)
    assert 0 < len(filtered) < len(all_moves)


def test_statistik_pencarian_tercatat():
    s = State()
    ai = QuoridorAI(max_depth=3)
    ai.get_best_move(s, 0)
    assert ai.nodes_evaluated > 0
    assert ai.last_search_time_ms >= 0.0