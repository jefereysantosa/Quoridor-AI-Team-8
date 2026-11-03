# Quoridor AI - Team 8

Aplikasi permainan Quoridor berbasis Pygame untuk mata kuliah
Artificial Intelligence (IMT01307503), Universitas Ciputra.
Tersedia mode melawan AI dan melawan pemain lain.

## Tim
- Jeferey Teddy Santosa (0706012410039)
- Hans Vere Liem (0706012410013)
- Flabianos Jason Muljono (0706012410019)

## Algoritma
Minimax dengan Alpha-Beta Pruning, A* Search dan BFS untuk pathfinding,
serta Logical Constraint Engine berbasis BFS Reachability Test.

## Menjalankan
```bash
pip install -r requirements.txt
python -m src.main
```

## Cara Bermain
Bawa pion ke baris seberang sebelum lawan. Tiap giliran, pilih satu aksi:
- Klik sel bergaris hijau untuk menggerakkan pion.
- Klik celah antar sel untuk memasang dinding.

Fitur:
- **Ghost Step:** menampilkan prediksi balasan AI sebelum langkah dikonfirmasi.
- **Explainable Hint:** memberi saran langkah beserta alasan berupa angka.
- **Dynamic Playstyle:** gaya bermain AI, yaitu Aggressive, Defensive, atau Balanced.
- **Kesulitan 1-5:** level 3, 4, dan 5 berpikir maksimal 3, 5, dan 10 detik per langkah.

| Tombol | Fungsi |
|---|---|
| Enter | Konfirmasi langkah |
| Esc | Batalkan pilihan |
| H | Minta hint |
| U | Undo |
| R | Restart |
| G | Nyalakan atau matikan Ghost Step |
| F1 | Bantuan |

## Pengujian
```bash
python -m pytest
```

## Evaluasi (Bab 2.2 proposal)
Turnamen head-to-head melawan Random Agent, Greedy Shortest-Path Agent, dan
Minimax tanpa Alpha-Beta (50 game per baseline, pemain pertama bergantian):

```bash
python -m experiments.tournament                     # evaluasi penuh
python -m experiments.tournament --games 6 --quick   # uji cepat
```

Keluaran ada di `experiments/results/`: `games.csv`, `moves.csv`, `pruning.csv`,
`summary.json`, dan `summary.md` (Win Rate, Pruning Efficiency, Wall
Effectiveness, serta kebenaran: nol langkah ilegal dan A* sama dengan BFS).
Minimax murni tersedia lewat `QuoridorAI(max_depth=2, use_pruning=False)`.
Test suite Logical Constraint Engine (30 kasus) ada di `tests/test_rules.py`.
