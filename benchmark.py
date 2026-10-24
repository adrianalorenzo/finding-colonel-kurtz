"""
Benchmark of the automatic agents on randomly generated maps.

Runs each agent many times (one random map per run, fixed seeds for
reproducibility), silences the console output of the original scripts and
classifies every episode as win / death / stopped without a safe move /
step limit. It does not modify the original modules, it only imports them.

Usage:
    python benchmark.py            # 1000 runs per agent
    python benchmark.py --runs 200
"""
import argparse
import contextlib
import io
import os
import random
import statistics
import sys
from collections import Counter

# The agents live in one folder per part; make them importable from here.
ROOT = os.path.dirname(os.path.abspath(__file__))
for folder in ("part1_logic_bfs", "part2_bayes_astar", "part2_river_mdp"):
    sys.path.insert(0, os.path.join(ROOT, folder))

import kurtz  # noqa: E402
import palacio  # noqa: E402
import river_mdp  # noqa: E402


def run_silently(fn, *args, **kwargs):
    """Run fn while capturing everything it prints. Returns the captured text."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def classify(log):
    text = log.lower()
    if "has ganado" in text:
        return "win"
    if "has muerto" in text:
        return "death"
    if "max pasos" in text or "max_steps" in text:
        return "step limit"
    return "stopped (no safe move)"


def bench_part1(runs, seed):
    """Part 1: logical knowledge base + BFS over cells proven safe."""
    results = Counter()
    for i in range(runs):
        random.seed(seed + i)
        results[classify(run_silently(kurtz.run_search_bfs, n=6))] += 1
    return results


def bench_part2_palace(runs, seed, p=0.2):
    """Part 2.1: Bayesian probability maps + risk-aware A*."""
    results = Counter()
    for i in range(runs):
        random.seed(seed + i)
        results[classify(run_silently(palacio.run_auto_a, n=6, p=p))] += 1
    return results


def bench_part2_river(runs, seed, max_steps=80):
    """Part 2.2: MDP solved with Value Iteration, simulated with the optimal policy."""
    reached, steps, returns = 0, [], []
    for i in range(runs):
        random.seed(seed + i)
        env = river_mdp.RiverEnvironment(rows=7, cols=9, nislas=2)
        mdp = river_mdp.RiverMDP(env)
        _, policy = river_mdp.value_iteration(mdp)
        log = run_silently(river_mdp.simular, env, mdp, policy, max_pasos=max_steps)
        if mdp.estado_objetivo(env.agente_pos):
            reached += 1
            steps.append(log.count("Paso "))
        returns.append(int(log.rsplit("Retorno total:", 1)[1].split()[0]))
    return reached, steps, returns


def pct(x, n):
    return f"{100 * x / n:5.1f}%"


def print_counter(title, results, runs):
    print(f"\n{title}")
    for outcome in ["win", "death", "stopped (no safe move)", "step limit"]:
        if results[outcome]:
            print(f"  {outcome:<24} {results[outcome]:>5}  {pct(results[outcome], runs)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    n, s = args.runs, args.seed

    print(f"Benchmark: {n} random maps per agent (seeds {s}..{s + n - 1})")
    print_counter("Part 1 - Logic + BFS", bench_part1(n, s), n)
    print_counter("Part 2.1 - Bayes + A* (p=0.2)", bench_part2_palace(n, s), n)

    reached, steps, returns = bench_part2_river(n, s)
    print("\nPart 2.2 - River MDP (Value Iteration)")
    print(f"  reached the far bank     {reached:>5}  {pct(reached, n)}")
    if steps:
        print(f"  mean steps to cross      {statistics.mean(steps):5.1f}")
    print(f"  mean total return        {statistics.mean(returns):5.1f}")


if __name__ == "__main__":
    main()
