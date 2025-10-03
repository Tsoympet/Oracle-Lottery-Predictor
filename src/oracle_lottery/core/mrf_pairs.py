
from __future__ import annotations
from typing import List, Tuple
import numpy as np
def fit_ising_pairs(history_rows: List[List[int]], pool: int, l1: float = 0.001) -> Tuple[np.ndarray, np.ndarray]:
    X = np.zeros((len(history_rows), pool), dtype=np.float64)
    for i, row in enumerate(history_rows):
        for n in row:
            if 1 <= n <= pool: X[i, n-1] = 1.0
    mu = X.mean(axis=0); sd = X.std(axis=0) + 1e-9; Z = (X-mu)/sd
    def sigm(a): return 1.0/(1.0+np.exp(-a))
    J = np.zeros((pool,pool)); h = np.zeros(pool)
    for j in range(pool):
        y = Z[:,j]; W = np.delete(Z, j, axis=1)
        beta = np.zeros(pool-1); b0 = 0.0; lr = 0.05
        for _ in range(120):
            p = sigm(b0 + W@beta)
            g_b0 = (p - (y>0)).mean(); g_b = W.T@(p - (y>0))/len(y)
            beta = np.sign(beta - lr*g_b) * np.maximum(0.0, np.abs(beta - lr*g_b) - lr*l1)
            b0 -= lr*g_b0
        left=list(range(pool)); left.pop(j); J[j,left]=beta; h[j]=b0
    J = 0.5*(J+J.T); return h,J
def mrf_ticket_energy(ticket: List[int], h, J) -> float:
    x = np.zeros(len(h)); 
    for n in ticket:
        if 1<=n<=len(h): x[n-1]=1.0
    e = -float(h @ x) - float(x @ J @ x); return -e
