# Quoridor AI - Team 8

Aplikasi permainan Quoridor player-versus-AI berbasis Pygame untuk mata kuliah
Artificial Intelligence (IMT01307503), Universitas Ciputra.

## Tim
- Jeferey Teddy Santosa (0706012410039)
- Hans Vere Liem (0706012410013)
- Flabianos Jason Muljono (0706012410019)

## Algoritma
Minimax dengan Alpha-Beta Pruning, A* Search dan BFS untuk pathfinding,
serta Logical Constraint Engine berbasis BFS Reachability Test.

## Menjalankan
pip install -r requirements.txt
python -m src.main

## Pengujian
pytest

## Evaluasi (Bab 2.2 proposal)
Turnamen head-to-head melawan Random Agent, Greedy Shortest-Path Agent, dan
Minimax tanpa Alpha-Beta (50 game per baseline, pemain pertama bergantian):

    python -m experiments.tournament                     # evaluasi penuh
    python -m experiments.tournament --games 6 --quick   # uji cepat

Keluaran ada di `experiments/results/`: `games.csv`, `moves.csv`, `pruning.csv`,
`summary.json`, dan `summary.md` (Win Rate, Pruning Efficiency, Wall
Effectiveness, serta kebenaran: nol langkah ilegal dan A* sama dengan BFS).
Minimax murni tersedia lewat `QuoridorAI(max_depth=2, use_pruning=False)`.
Test suite Logical Constraint Engine (30 kasus) ada di `tests/test_rules.py`.
