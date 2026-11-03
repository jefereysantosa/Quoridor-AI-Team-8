"""Test M5: harness turnamen menghasilkan data yang valid (tanpa menjalankan 150 game)."""
from experiments.tournament import (
    is_legal, make_opponent, measure_pruning, play_game, random_opening, summarize,
)
from src.game.state import State
import argparse
import random


def test_game_selesai_tanpa_langkah_ilegal_dan_astar_sama_dengan_bfs():
    res = play_game(("greedy", 0, 1, 2, 123))
    g = res["game_row"]
    assert g["result"] in ("win", "loss", "draw")
    assert g["illegal_moves"] == 0
    assert g["astar_bfs_mismatch"] == 0
    assert res["move_rows"] and res["ai_states"]


def test_pergantian_pemain_pertama():
    assert play_game(("random", 0, 1, 0, 5))["game_row"]["ai_first"] == 1
    assert play_game(("random", 1, 1, 0, 5))["game_row"]["ai_first"] == 0


def test_game_berpasangan_identik_pada_minimax_vs_alpha_beta():
    a = play_game(("minimax", 0, 1, 2, 9))["game_row"]
    b = play_game(("minimax", 1, 1, 2, 9))["game_row"]
    assert a["plies"] == b["plies"]
    assert {a["result"], b["result"]} == {"win", "loss"}


def test_pruning_efficiency_dihitung_dan_keputusan_sama():
    s = State()
    raw = (s.pawns, s.walls_remaining, s.h_walls, s.v_walls, s.current_player)
    r = measure_pruning((raw, 0, 2))
    assert r["same_move"] == 1
    assert r["nodes_minimax"] >= r["nodes_alphabeta"]
    assert 0.0 <= r["pruning_efficiency"] < 100.0


def test_langkah_pembuka_acak_menjaga_state_legal():
    s = State()
    random_opening(s, random.Random(1), 4)
    assert s.current_player == 0
    assert is_legal(s, ("move", s.pawns[0]), 0) is False  # tidak boleh diam di tempat


def test_ringkasan_menandai_target_win_rate():
    games = [{"opponent": "random", "result": "win", "ai_first": i % 2, "plies": 20,
                "illegal_moves": 0, "astar_bfs_mismatch": 0} for i in range(10)]
    args = argparse.Namespace(opponents=["random"], pruning_depth=2)
    s = summarize(games, [], [], args)
    assert s["win_rate"]["random"]["win_rate_percent"] == 100.0
    assert s["win_rate"]["random"]["target_met"] is True
    assert s["correctness"]["illegal_moves_total"] == 0


def test_lawan_dikenali():
    for name in ("random", "greedy", "minimax"):
        assert callable(make_opponent(name, 1))
