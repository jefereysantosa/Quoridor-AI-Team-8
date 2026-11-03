"""
Turnamen evaluasi Quoridor AI (milestone M5, Bab 2.2 proposal).

Menjalankan QuoridorAI (Minimax + Alpha-Beta) melawan tiga baseline dan
mencatat metrik kuantitatif proposal:
  1. Win Rate (Tabel 3), pergantian pemain pertama dengan pembuka acak berpasangan.
  2. Pruning Efficiency = (Node_Minimax - Node_AlphaBeta) / Node_Minimax.
  3. Wall Effectiveness = Jarak_Lawan_Setelah - Jarak_Lawan_Sebelum.
  4. Kebenaran pathfinding (A* vs BFS) dan nol langkah ilegal.

Jalankan dari root proyek:
    python -m experiments.tournament                    # 50 game per baseline
    python -m experiments.tournament --games 6 --quick  # uji cepat

Keluaran di experiments/results/: games.csv, moves.csv, pruning.csv,
summary.json, dan summary.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.ai.baselines import GreedyAgent, RandomAgent
from src.ai.minimax import QuoridorAI
from src.ai.pathfinding import astar_distance, bfs_distance
from src.game.moves import MoveGenerator
from src.game.rules import Rules
from src.game.state import State

OPPONENTS = ("random", "greedy", "minimax")
OPPONENT_LABEL = {
    "random": "Random Agent",
    "greedy": "Greedy Shortest-Path Agent",
    "minimax": "Minimax tanpa Alpha-Beta",
}
# Target dari Tabel 3 proposal: (batas bawah, batas atas). "Sekitar 50%" = 40-60%.
TARGETS = {"random": (90.0, 100.0), "greedy": (70.0, 100.0), "minimax": (40.0, 60.0)}

MAX_PLIES = 200


def make_opponent(name: str, depth: int):
    """Mengembalikan fungsi (state, player_idx) -> aksi untuk lawan."""
    if name == "random":
        return RandomAgent().get_move
    if name == "greedy":
        return GreedyAgent().get_move
    if name == "minimax":
        return QuoridorAI(max_depth=depth, use_pruning=False).get_best_move
    raise ValueError(name)


def is_legal(state, action, player_idx: int) -> bool:
    kind, payload = action
    if kind == "move":
        return action in MoveGenerator._get_pawn_moves(state, player_idx)
    r, c, orient = payload
    return Rules.is_wall_valid(state, r, c, orient, player_idx)


def random_opening(state, rng: random.Random, plies: int) -> None:
    """Beberapa langkah pion acak agar game tidak identik (mesin deterministik)."""
    for _ in range(plies):
        p = state.current_player
        moves = MoveGenerator._get_pawn_moves(state, p)
        state.apply_move(rng.choice(moves), p)


def play_game(job: Tuple) -> Dict:
    """
    Satu game penuh. Berjalan di proses terpisah, jadi hanya memakai tipe sederhana.

    Desain berpasangan: game 2k dan 2k+1 memakai seed (jadi pembuka acak) yang
    sama dengan warna AI ditukar, sehingga keuntungan pembuka dan giliran
    pertama saling meniadakan.
    """
    opponent, game_idx, depth, opening_plies, seed = job
    rng = random.Random(seed)
    random.seed(seed)  # RandomAgent memakai modul random global

    ai_idx = game_idx % 2  # pergantian pemain pertama: genap -> AI jalan duluan
    ai = QuoridorAI(max_depth=depth)
    opp_move = make_opponent(opponent, depth)

    state = State()
    random_opening(state, rng, opening_plies)

    move_rows: List[Dict] = []
    ai_states: List[State] = []
    illegal = 0
    astar_mismatch = 0
    winner: Optional[int] = None
    t_start = time.perf_counter()
    plies = opening_plies

    while plies < MAX_PLIES:
        p = state.current_player
        if p == ai_idx:
            ai_states.append(state.clone())
            d_opp_before = astar_distance(state, 1 - p)
            action = ai.get_best_move(state, p)
            nodes, pruned, ms = ai.nodes_evaluated, ai.nodes_pruned, ai.last_search_time_ms
        else:
            action = opp_move(state, p)
            nodes = pruned = 0
            ms = 0.0
        if action is None or not is_legal(state, action, p):
            illegal += 1
            winner = 1 - p  # langkah ilegal dihitung kalah
            break

        wall_eff = ""
        if p == ai_idx and action[0] == "wall":
            r, c, o = action[1]
            trial = state.clone()
            trial.apply_move(action, p)
            wall_eff = astar_distance(trial, 1 - p) - d_opp_before

        state.apply_move(action, p)
        plies += 1
        # Pemeriksaan kebenaran A* terhadap BFS pada setiap state nyata
        for idx in (0, 1):
            if astar_distance(state, idx) != bfs_distance(state, idx):
                astar_mismatch += 1

        if p == ai_idx:
            move_rows.append({
                "opponent": opponent, "game": game_idx, "ply": plies,
                "action": action[0], "nodes": nodes, "cutoffs": pruned,
                "ms": round(ms, 2), "wall_effectiveness": wall_eff,
            })
        if state.is_winner(p):
            winner = p
            break

    walls = [m["wall_effectiveness"] for m in move_rows if m["wall_effectiveness"] != ""]
    return {
        "game_row": {
            "opponent": opponent, "game": game_idx,
            "ai_first": int(ai_idx == 0),
            "result": "win" if winner == ai_idx else ("loss" if winner is not None else "draw"),
            "plies": plies, "ai_walls_placed": len(walls),
            "illegal_moves": illegal, "astar_bfs_mismatch": astar_mismatch,
            "seconds": round(time.perf_counter() - t_start, 2),
        },
        "move_rows": move_rows,
        # Hanya state AI yang dibawa balik (dipakai untuk uji Pruning Efficiency)
        "ai_states": [(s.pawns, s.walls_remaining, s.h_walls, s.v_walls, s.current_player)
                    for s in ai_states],
        "ai_idx": ai_idx,
    }


def _rebuild(raw) -> State:
    s = State()
    s.pawns, s.walls_remaining, s.h_walls, s.v_walls, s.current_player = (
        list(raw[0]), list(raw[1]), [r[:] for r in raw[2]], [r[:] for r in raw[3]], raw[4])
    return s


def measure_pruning(job: Tuple) -> Dict:
    """Menjalankan Alpha-Beta dan Minimax murni pada state yang sama."""
    raw, ai_idx, depth = job
    state = _rebuild(raw)
    ab = QuoridorAI(max_depth=depth)
    plain = QuoridorAI(max_depth=depth, use_pruning=False)
    m_ab = ab.get_best_move(state, ai_idx)
    m_plain = plain.get_best_move(state, ai_idx)
    return {
        "depth": depth,
        "nodes_alphabeta": ab.nodes_evaluated, "nodes_minimax": plain.nodes_evaluated,
        "ms_alphabeta": round(ab.last_search_time_ms, 1), "ms_minimax": round(plain.last_search_time_ms, 1),
        "same_move": int(m_ab == m_plain),
        "pruning_efficiency": round(
            100.0 * (plain.nodes_evaluated - ab.nodes_evaluated) / plain.nodes_evaluated, 2),
    }


def write_csv(path: Path, rows: List[Dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def summarize(games, moves, pruning, args) -> Dict:
    summary: Dict = {"config": vars(args), "win_rate": {}}
    for opp in args.opponents:
        g = [x for x in games if x["opponent"] == opp]
        wins = sum(x["result"] == "win" for x in g)
        lo, hi = TARGETS[opp]
        rate = 100.0 * wins / len(g) if g else float("nan")
        first = [x for x in g if x["ai_first"]]
        second = [x for x in g if not x["ai_first"]]
        summary["win_rate"][opp] = {
            "games": len(g), "wins": wins, "losses": sum(x["result"] == "loss" for x in g),
            "draws": sum(x["result"] == "draw" for x in g),
            "win_rate_percent": round(rate, 1), "target_range": [lo, hi],
            "target_met": lo <= rate <= hi,
            "win_rate_ai_first": round(100.0 * sum(x["result"] == "win" for x in first) / max(1, len(first)), 1),
            "win_rate_ai_second": round(100.0 * sum(x["result"] == "win" for x in second) / max(1, len(second)), 1),
            "avg_plies": round(mean([x["plies"] for x in g]), 1),
        }
    wall = [m["wall_effectiveness"] for m in moves if m["wall_effectiveness"] != ""]
    summary["wall_effectiveness"] = {
        "walls_placed": len(wall), "mean": round(mean(wall), 3) if wall else None,
        "positive_share_percent": round(100.0 * sum(w > 0 for w in wall) / len(wall), 1) if wall else None,
        "negative_count": sum(w < 0 for w in wall),
    }
    summary["pruning"] = {
        "samples": len(pruning), "depth": args.pruning_depth,
        "mean_efficiency_percent": round(mean([p["pruning_efficiency"] for p in pruning]), 2) if pruning else None,
        "same_move_share_percent": round(100.0 * sum(p["same_move"] for p in pruning) / len(pruning), 1) if pruning else None,
        "mean_nodes_alphabeta": round(mean([p["nodes_alphabeta"] for p in pruning]), 1) if pruning else None,
        "mean_nodes_minimax": round(mean([p["nodes_minimax"] for p in pruning]), 1) if pruning else None,
    }
    ai_moves = [m for m in moves]
    summary["search_cost"] = {
        "mean_nodes_per_ai_move": round(mean([m["nodes"] for m in ai_moves]), 1),
        "mean_ms_per_ai_move": round(mean([m["ms"] for m in ai_moves]), 1),
    }
    summary["correctness"] = {
        "illegal_moves_total": sum(x["illegal_moves"] for x in games),
        "astar_bfs_mismatches": sum(x["astar_bfs_mismatch"] for x in games),
    }
    return summary


def render_markdown(s: Dict) -> str:
    L = ["# Hasil Turnamen Evaluasi Quoridor AI", ""]
    c = s["config"]
    L.append(f"Kedalaman AI: {c['depth']} ply | game per baseline: {c['games']} | "
            f"langkah pembuka acak: {c['opening_plies']} ply | seed: {c['seed']}")
    L += ["", "## 1. Win Rate (Tabel 3)", "",
        "| Baseline | M-K-S | Win Rate | Target | Tercapai | AI jalan 1 | AI jalan 2 |",
        "|---|---|---|---|---|---|---|"]
    for opp, w in s["win_rate"].items():
        lo, hi = w["target_range"]
        tgt = f"{lo:.0f}-{hi:.0f}%" if opp == "minimax" else f">= {lo:.0f}%"
        L.append(f"| {OPPONENT_LABEL[opp]} | {w['wins']}-{w['losses']}-{w['draws']} | "
                f"{w['win_rate_percent']}% | {tgt} | {'ya' if w['target_met'] else 'TIDAK'} | "
                f"{w['win_rate_ai_first']}% | {w['win_rate_ai_second']}% |")
    p = s["pruning"]
    L += ["", "## 2. Pruning Efficiency", ""]
    if p["samples"]:
        L += [f"- Sampel state: {p['samples']} pada kedalaman {p['depth']}",
            f"- Rata-rata node Alpha-Beta: {p['mean_nodes_alphabeta']} vs Minimax murni: {p['mean_nodes_minimax']}",
            f"- **Pruning Efficiency rata-rata: {p['mean_efficiency_percent']}%**",
            f"- Keputusan identik dengan Minimax murni: {p['same_move_share_percent']}% sampel"]
    else:
        L.append("Tidak diukur.")
    w = s["wall_effectiveness"]
    L += ["", "## 3. Wall Effectiveness", ""]
    if w["walls_placed"]:
        L += [f"- Dinding dipasang AI: {w['walls_placed']}",
            f"- **Rata-rata selisih jarak lawan: {w['mean']} langkah**",
            f"- Dinding yang memperpanjang jalur lawan: {w['positive_share_percent']}%",
            f"- Dinding yang justru merugikan AI (nilai negatif): {w['negative_count']}"]
    else:
        L.append("AI tidak memasang dinding pada sampel ini.")
    k = s["correctness"]
    L += ["", "## 4. Kebenaran selama turnamen", "",
            f"- Langkah ilegal: **{k['illegal_moves_total']}** (target 0)",
            f"- Selisih A* vs BFS pada state permainan nyata: **{k['astar_bfs_mismatches']}** (target 0)", "",
            f"Biaya pencarian AI: rata-rata {s['search_cost']['mean_nodes_per_ai_move']} node "
            f"dan {s['search_cost']['mean_ms_per_ai_move']} ms per langkah.", ""]
    return "\n".join(L)


def main(argv=None) -> Dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--games", type=int, default=50, help="game per baseline (default 50)")
    ap.add_argument("--depth", type=int, default=2, help="kedalaman AI dan Minimax murni")
    ap.add_argument("--opponents", default=",".join(OPPONENTS), help="daftar dipisah koma")
    ap.add_argument("--opening-plies", type=int, default=4, help="ply pembuka acak (pion saja)")
    ap.add_argument("--pruning-samples", type=int, default=20, help="jumlah state untuk Pruning Efficiency")
    ap.add_argument("--pruning-depth", type=int, default=3, help="kedalaman pengukuran pruning")
    ap.add_argument("--workers", type=int, default=0, help="proses paralel (0 = jumlah CPU)")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="experiments/results")
    ap.add_argument("--quick", action="store_true", help="kurangi sampel pruning untuk uji cepat")
    args = ap.parse_args(argv)
    args.opponents = [o.strip() for o in args.opponents.split(",") if o.strip()]
    if args.quick:
        args.pruning_samples = min(args.pruning_samples, 3)
        args.pruning_depth = min(args.pruning_depth, 2)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(opp, i, args.depth, args.opening_plies, args.seed * 1000 + 100 * k + i // 2)
            for k, opp in enumerate(args.opponents) for i in range(args.games)]
    t0 = time.perf_counter()
    results: List[Dict] = []
    with ProcessPoolExecutor(max_workers=args.workers or None) as pool:
        for n, res in enumerate(pool.map(play_game, jobs), 1):
            g = res["game_row"]
            print(f"[{n}/{len(jobs)}] vs {g['opponent']:<8} game {g['game']:>2} "
                    f"{g['result']:<4} plies={g['plies']:<3} {g['seconds']}s", flush=True)
            results.append(res)

    games = [r["game_row"] for r in results]
    moves = [m for r in results for m in r["move_rows"]]

    # Sampel state AI untuk Pruning Efficiency (acak, tetapi memakai seed)
    pool_states = [(raw, r["ai_idx"]) for r in results for raw in r["ai_states"][2:]]
    rng = random.Random(args.seed)
    rng.shuffle(pool_states)
    pjobs = [(raw, idx, args.pruning_depth) for raw, idx in pool_states[:args.pruning_samples]]
    pruning: List[Dict] = []
    if pjobs:
        print(f"Mengukur Pruning Efficiency pada {len(pjobs)} state (kedalaman {args.pruning_depth})...", flush=True)
        with ProcessPoolExecutor(max_workers=args.workers or None) as pool:
            pruning = list(pool.map(measure_pruning, pjobs))

    summary = summarize(games, moves, pruning, args)
    write_csv(out / "games.csv", games)
    write_csv(out / "moves.csv", moves)
    write_csv(out / "pruning.csv", pruning)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    md = render_markdown(summary)
    (out / "summary.md").write_text(md)
    print("\n" + md)
    print(f"Selesai dalam {time.perf_counter() - t0:.0f} s. Berkas ada di {out}/")
    return summary


if __name__ == "__main__":
    main()
