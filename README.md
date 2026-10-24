# Finding Colonel Kurtz: Classical AI Agents

An intelligent agent that has to rescue Colonel Kurtz from a palace full of deadly traps and then escape across a dangerous river, using only what it can perceive. Inspired by *Apocalypse Now*.

The project walks through the core toolkit of classical AI, with **one environment and increasingly realistic assumptions**:

| Part | Problem | Technique | Folder |
|---|---|---|---|
| **1** | Explore a 6×6 palace with pits and an enemy soldier, find Kurtz, reach the exit | **Propositional knowledge base** + **BFS** over cells proven safe | [`part1_logic_bfs/`](part1_logic_bfs) |
| **2.1** | Same palace, but with three different traps that can share a cell, and only noisy perceptions | **Bayesian inference** (probability maps per hazard) + **risk-aware A\*** | [`part2_bayes_astar/`](part2_bayes_astar) |
| **2.2** | Cross a river whose current randomly pushes the boat downstream | **Markov Decision Process** solved with **Value Iteration** | [`part2_river_mdp/`](part2_river_mdp) |

> Final project for *Fundamentals of Artificial Intelligence*, BSc in Mathematical Engineering & AI, Universidad Pontificia Comillas (2025/26).

---

## Results

`benchmark.py` runs every automatic agent on **1,000 randomly generated maps** (fixed seeds, fully reproducible):

| Agent | Win rate | Other outcomes |
|---|---|---|
| **Part 1:** Logic + BFS | **19.2%** | **0% deaths**, 80.8% stops when no cell can be proven safe |
| **Part 2.1:** Bayes + A* (risk threshold p = 0.2) | **69.3%** | 11.8% deaths, 18.9% step limit |
| **Part 2.2:** MDP + Value Iteration | **99.7%** reach the far bank | 26.1 steps on average, mean return 74.5 |

**How to read these numbers.** The two palace agents sit at opposite ends of the safety vs. success trade-off:

- The **logical agent never dies**, because it only moves to cells it can *prove* are safe. The price is that it often gets stuck. In 22% of maps, the starting cell already senses a breeze or a snore, so nothing can be proven safe from the very first move.
- The **Bayesian agent accepts calculated risk.** It moves through cells whose estimated danger is below a threshold, which multiplies the win rate by 3.6× at the cost of some deaths. Changing `p` moves the agent along that trade-off.
- In the river, Value Iteration finds a policy that crosses almost every map, despite stochastic currents of up to 94% per column.

---

## How each part works

### Part 1: Logical agent + BFS
- **Environment** (`map.py`): 6×6 grid with 3 pits, a sleeping soldier, Kurtz and a hidden exit. The agent perceives *breeze* (pit nearby), *snore* (soldier nearby), *glow* (exit nearby), walls and the soldier's scream. It carries one grenade.
- **Knowledge base** (`knowledgeBase.py`): updates safe, possible and confirmed pit and soldier cells from each perception, using propositional inference rules.
- **Two modes:** (A) manual play, with the knowledge base suggesting safe moves; (B) fully automatic play, picking the closest provably safe unvisited cell and reaching it by BFS (`search.py`).

```
VIS (0,0)  VIS (0,1)  VIS (0,2)  VIS (0,3)  A (0,4)   s (0,5)
VIS (1,0)  VIS (1,1)  VIS (1,2)  VIS (1,3)  P! (1,4)  . (1,5)
VIS (2,0)  VIS (2,1)  VIS (2,2)  P! (2,3)   . (2,4)   . (2,5)
...
HAs ganado! Has salido correctamente
```

### Part 2.1: Bayesian agent + A*
- **Environment** (`palacio_environment.py`): three distinct traps (fire, spikes, poison darts), each with its own stimulus. Traps may share a cell, and the soldier, Kurtz and the exit may share a cell too.
- **Bayesian inference** (`palacio_bayes.py`): keeps a probability map for every hazard and objective (fire, spikes, darts, soldier, exit, Kurtz). Each map starts from a uniform prior and is updated with Bayes' rule after every perception.
- **Planning** (`palacio_search.py`): the risk of a cell is P(any trap) + P(soldier). A\* uses the cost `1 + α·risk` with a Manhattan heuristic, only through cells with risk below a threshold `p`, plus a fallback to the safest neighbour.

### Part 2.2: Crossing the river (MDP)
- **Environment** (`river_mdp.py`): a 7×9 river with two random islands. Each column has a current strength drawn from U(0.06, 0.94).
- **MDP:** states are cells, and the actions are up, down, left, right and stay. Any action other than *down* succeeds with probability `1 − strength` and drifts downstream otherwise. Rewards are −1 per step and +100 at the exit.
- **Value Iteration** (γ = 0.95, convergence at 1e-6) gives the optimal policy, which is then simulated step by step:

```
→ → → → → → → → ↓
→ → → → → → → → ↓
→ → → → → → ↓ I ↓
→ → → → → → → → E
→ → → → → → → → ↑
→ → → → ↑ I → → ↑
→ → → → → → → → ↑
```

---

## How to run

Pure Python 3, with no external dependencies.

```bash
git clone https://github.com/adrianalorenzo/finding-colonel-kurtz.git
cd finding-colonel-kurtz

python part1_logic_bfs/kurtz.py        # Part 1   → choose A (manual) or B (automatic BFS)
python part2_bayes_astar/palacio.py    # Part 2.1 → choose A (manual) or B (automatic A*)
python part2_river_mdp/river_mdp.py    # Part 2.2 → optimal policy + simulated crossing
python benchmark.py                    # win rates over 1,000 random maps (~1 min)
```

Manual controls: `WASD` to move, `IJKL` to throw the grenade, `E` to exit.

## Repository structure

```
├── part1_logic_bfs/
│   ├── kurtz.py                 # main script (manual / BFS)
│   ├── map.py                   # palace environment
│   ├── knowledgeBase.py         # propositional knowledge base
│   └── search.py                # BFS over safe cells
├── part2_bayes_astar/
│   ├── palacio.py               # main script (manual / A*)
│   ├── palacio_environment.py   # environment with 3 trap types
│   ├── palacio_bayes.py         # Bayesian probability maps
│   └── palacio_search.py        # risk-aware A*
├── part2_river_mdp/
│   └── river_mdp.py             # river environment, MDP, Value Iteration, simulation
└── benchmark.py                 # evaluation over random maps
```

## Possible extensions

- Let the logical agent use its grenade, or take a single minimum-risk guess when stuck, instead of stopping.
- Sweep the risk threshold `p` to plot the full win-rate vs. death-rate curve.
- Add hazardous river cells to the MDP and compare Value Iteration with Q-learning.

---

**Adriana Lorenzo Mingorance** · Mathematical Engineering & AI, Universidad Pontificia Comillas
