"""Test M3: kebenaran pathfinding BFS dan A* (Bab 2.2 bagian B.2)."""
import random

from src.game.state import State
from src.game.rules import Rules
from src.ai.pathfinding import bfs_distance, astar_distance, get_shortest_path


def test_jarak_awal_papan_kosong():
    s = State()
    assert bfs_distance(s, 0) == 8
    assert astar_distance(s, 0) == 8
    assert bfs_distance(s, 1) == 8
    assert astar_distance(s, 1) == 8


def test_konsistensi_bfs_dan_astar_50_konfigurasi():
    random.seed(42)
    for _ in range(50):
        s = State()
        for i in range(6):
            r = random.randrange(8)
            c = random.randrange(8)
            orient = random.choice(["H", "V"])
            if Rules.is_wall_valid(s, r, c, orient, i % 2):
                if orient == "H":
                    s.h_walls[r][c] = True
                else:
                    s.v_walls[r][c] = True
        assert bfs_distance(s, 0) == astar_distance(s, 0)
        assert bfs_distance(s, 1) == astar_distance(s, 1)


def test_jalur_dimulai_dari_pion_dan_berakhir_di_target():
    s = State()
    path = get_shortest_path(s, 0)
    assert path[0] == s.pawns[0]
    assert path[-1][0] == 8
    assert len(path) == 9