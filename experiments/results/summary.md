# Hasil Turnamen Evaluasi Quoridor AI

Kedalaman AI: 2 ply | game per baseline: 50 | langkah pembuka acak: 4 ply | seed: 2026

## 1. Win Rate (Tabel 3)

| Baseline | M-K-S | Win Rate | Target | Tercapai | AI jalan 1 | AI jalan 2 |
|---|---|---|---|---|---|---|
| Random Agent | 50-0-0 | 100.0% | >= 90% | ya | 100.0% | 100.0% |
| Greedy Shortest-Path Agent | 50-0-0 | 100.0% | >= 70% | ya | 100.0% | 100.0% |
| Minimax tanpa Alpha-Beta | 25-25-0 | 50.0% | 40-60% | ya | 72.0% | 28.0% |

## 2. Pruning Efficiency

- Sampel state: 20 pada kedalaman 3
- Rata-rata node Alpha-Beta: 1071.9 vs Minimax murni: 15497.5
- **Pruning Efficiency rata-rata: 66.85%**
- Keputusan identik dengan Minimax murni: 100.0% sampel

## 3. Wall Effectiveness

- Dinding dipasang AI: 757
- **Rata-rata selisih jarak lawan: 1.855 langkah**
- Dinding yang memperpanjang jalur lawan: 93.7%
- Dinding yang justru merugikan AI (nilai negatif): 0

## 4. Kebenaran selama turnamen

- Langkah ilegal: **0** (target 0)
- Selisih A* vs BFS pada state permainan nyata: **0** (target 0)

Biaya pencarian AI: rata-rata 229.5 node dan 656.0 ms per langkah.
