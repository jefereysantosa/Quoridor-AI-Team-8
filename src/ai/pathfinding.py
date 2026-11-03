"""
Modul Pathfinding untuk Quoridor.

Mengimplementasikan dua algoritma pencarian jalur terpendek:
- BFS (Breadth First Search): digunakan sebagai ground-truth eksak
  untuk memverifikasi kebenaran A* (Bab 2.2 bagian B.2 proposal).
- A* Search: algoritma utama dengan heuristik Manhattan Distance
  yang admissible dan consistent (Bab 2.1.4 bagian A proposal).

Kedua algoritma memperhitungkan matriks dinding h_walls dan v_walls
dari representasi State Hans, dengan konvensi anchor persimpangan 8x8.
"""

from __future__ import annotations

from collections import deque
from typing import List, Optional, Tuple

# Tipe alias untuk kejelasan
Position = Tuple[int, int]


def _neighbors(state, r: int, c: int) -> List[Position]:
    """
    Mengembalikan daftar tetangga yang dapat dicapai dari sel (r, c),
    dengan memperhitungkan dinding yang terpasang.

    Logika blokir dinding konsisten dengan Rules._bfs_has_path milik Hans:
    dinding H pada anchor (r,c) menutupi persimpangan (r,c) dan (r,c+1).
    """
    result: List[Position] = []

    # ATAS (r-1, c)
    if r > 0:
        blocked = state.h_walls[r - 1][c] or (c > 0 and state.h_walls[r - 1][c - 1])
        if not blocked:
            result.append((r - 1, c))

    # BAWAH (r+1, c)
    if r < 8:
        blocked = state.h_walls[r][c] or (c > 0 and state.h_walls[r][c - 1])
        if not blocked:
            result.append((r + 1, c))

    # KIRI (r, c-1)
    if c > 0:
        blocked = state.v_walls[r][c - 1] or (r > 0 and state.v_walls[r - 1][c - 1])
        if not blocked:
            result.append((r, c - 1))

    # KANAN (r, c+1)
    if c < 8:
        blocked = state.v_walls[r][c] or (r > 0 and state.v_walls[r - 1][c])
        if not blocked:
            result.append((r, c + 1))

    return result


def _target_row(player_idx: int) -> int:
    """Baris tujuan: Player 0 (bawah) -> 8, Player 1 (atas) -> 0."""
    return 8 if player_idx == 0 else 0


def _heuristic(pos: Position, player_idx: int) -> int:
    """
    Heuristik Manhattan untuk A*.

    Karena target adalah SELURUH BARIS (bukan satu titik), cukup hitung
    selisih baris. Ini admissible (tidak melebih-lebihkan) dan consistent
    (h(n) <= h(n') + c) seperti dijelaskan di Bab 2.1.4 bagian A proposal.
    """
    r, _ = pos
    return abs(r - _target_row(player_idx))


def bfs_distance(state, player_idx: int) -> int:
    """
    BFS murni untuk menghitung jarak terpendek (jumlah langkah) dari pion
    ke garis tujuan.

    Digunakan sebagai ground-truth eksak saat memverifikasi A*
    (Bab 2.2 bagian B.2: target kesesuaian 100 persen).

    Return: jumlah langkah minimum, atau -1 jika tidak ada jalur.
    """
    start = state.pawns[player_idx]
    target_row = _target_row(player_idx)

    # Early exit: sudah menang
    if start[0] == target_row:
        return 0

    queue = deque([(start, 0)])
    visited = {start}

    while queue:
        (r, c), dist = queue.popleft()
        for nxt in _neighbors(state, r, c):
            if nxt in visited:
                continue
            if nxt[0] == target_row:
                return dist + 1
            visited.add(nxt)
            queue.append((nxt, dist + 1))

    return -1  # tidak ada jalur (seharusnya tidak terjadi jika Rules benar)


def astar_distance(state, player_idx: int) -> int:
    """
    A* Search dengan heuristik |r - target_row|.

    Algoritma utama untuk perhitungan jarak pada fungsi evaluasi
    (variabel D dalam rumus Eval(s) di Bab 2.1.4 bagian A).
    Pada biaya seragam, A* dan BFS menghasilkan hasil identik, tetapi
    A* biasanya mengeksplorasi lebih sedikit node karena heuristik
    mengarahkan pencarian ke target.

    Return: jarak minimum, atau -1 jika tidak ada jalur.
    """
    import heapq

    start = state.pawns[player_idx]
    target_row = _target_row(player_idx)

    if start[0] == target_row:
        return 0

    # Priority queue: (f, g, position)
    h0 = _heuristic(start, player_idx)
    open_set = [(h0, 0, start)]
    g_score = {start: 0}

    while open_set:
        f, g, (r, c) = heapq.heappop(open_set)

        # Sudah sampai tujuan?
        if r == target_row:
            return g

        # Skip jika kita sudah menemukan jalur lebih pendek
        if g > g_score.get((r, c), float("inf")):
            continue

        for nxt in _neighbors(state, r, c):
            tentative_g = g + 1
            if tentative_g < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative_g
                f_new = tentative_g + _heuristic(nxt, player_idx)
                heapq.heappush(open_set, (f_new, tentative_g, nxt))

    return -1


def get_shortest_path(state, player_idx: int) -> List[Position]:
    """
    Mengembalikan urutan sel dari posisi pion hingga garis tujuan.

    Digunakan oleh Candidate Filtering di modul minimax (Bab 2.1.5 proposal):
    hanya dinding yang berpotongan dengan jalur ini yang dipertimbangkan
    sebagai kandidat, sehingga branching factor turun drastis.

    Return: list posisi [(r0,c0), (r1,c1), ...]. List kosong jika tidak ada jalur.
    """
    import heapq

    start = state.pawns[player_idx]
    target_row = _target_row(player_idx)

    if start[0] == target_row:
        return [start]

    h0 = _heuristic(start, player_idx)
    open_set = [(h0, 0, start)]
    g_score = {start: 0}
    came_from: dict = {}

    while open_set:
        f, g, (r, c) = heapq.heappop(open_set)

        if r == target_row:
            # Rekonstruksi jalur
            path = [(r, c)]
            cur = (r, c)
            while cur in came_from:
                cur = came_from[cur]
                path.append(cur)
            path.reverse()
            return path

        if g > g_score.get((r, c), float("inf")):
            continue

        for nxt in _neighbors(state, r, c):
            tentative_g = g + 1
            if tentative_g < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative_g
                came_from[nxt] = (r, c)
                f_new = tentative_g + _heuristic(nxt, player_idx)
                heapq.heappush(open_set, (f_new, tentative_g, nxt))

    return []  # tidak ada jalur