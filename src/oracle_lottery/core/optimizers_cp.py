
from __future__ import annotations
from typing import List
from ortools.sat.python import cp_model

def _hamming(a: List[int], b: List[int]) -> int:
    return len(set(a) ^ set(b))

def select_with_cpsat(tickets: List[List[int]], scores: List[float],
                      max_select: int, min_diversity: int) -> List[List[int]]:
    n = len(tickets)
    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x_{i}") for i in range(n)]
    model.Add(sum(x) == max_select)
    for i in range(n):
        for j in range(i+1, n):
            if _hamming(tickets[i], tickets[j]) < min_diversity:
                model.Add(x[i] + x[j] <= 1)
    scale = 10000
    int_scores = [int(round(s*scale)) for s in scores]
    model.Maximize(sum(int_scores[i] * x[i] for i in range(n)))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    solver.parameters.num_search_workers = 8
    res = solver.Solve(model)
    if res not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return []
    return [tickets[i] for i in range(n) if solver.Value(x[i]) == 1]
