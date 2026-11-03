"""Test M4: Dynamic Playstyle, Ghost Step, Explainable Hint."""
from src.game.state import State
from src.game.moves import MoveGenerator
from src.ai import (
    QuoridorAI, PLAYSTYLES, get_playstyle,
    evaluate_state, predict_response, generate_hint, format_hint_text,
)


def test_registry_playstyle_lengkap():
    assert set(PLAYSTYLES) == {"aggressive", "defensive", "balanced"}
    assert get_playstyle("aggressive").weights == (1.5, 0.2, 0.1)


def test_set_playstyle_mengubah_perilaku_evaluasi():
    s = State()
    s.walls_remaining[0] = 8
    s.walls_remaining[1] = 2
    v_agg = evaluate_state(s, 0, "aggressive")
    v_def = evaluate_state(s, 0, "defensive")
    assert v_def > v_agg  # selisih dinding diberi bobot lebih besar


def test_ghost_response_adalah_langkah_legal():
    s = State()
    human_action = ("move", (1, 4))
    pred = predict_response(s, human_action, 0, depth=1)
    child = s.clone()
    child.apply_move(human_action, 0)
    assert pred.ai_response in MoveGenerator.get_legal_moves(child, 1)


def test_hint_legal_dan_memuat_alasan_numerik():
    s = State()
    hint = generate_hint(s, 0, depth=2)
    assert hint.action in MoveGenerator.get_legal_moves(s, 0)
    text = " ".join(format_hint_text(hint))
    assert len(hint.reasons) >= 2
    assert any(ch.isdigit() for ch in text)