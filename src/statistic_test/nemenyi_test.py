# !pip install scikit-posthocs scipy pandas numpy matplotlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scikit_posthocs as sp
from scipy import stats



# -----------------------------
# 1) Dati: Sostituire i dati con i risultati da confrontare per f1 fast, slow e mse
# -----------------------------


#NO PHONEME
data = {
    "All_Features": [
        0.87,  # Eclipse P50
        0.81,  # Eclipse P75
        0.73,  # Eclipse P90
        0.91,  # KDE P50
        0.81,  # KDE P75
        0.63,  # KDE P90
        0.74,  # OpenXchange P50
        0.35,  # OpenXchange P75
        0.00,  # OpenXchange P90
        0.84,  # Novell P50
        0.72,  # Novell P75
        0.61   # Novell P90
    ],
    "Heuristic_Alta": [
        0.89,  # Eclipse P50
        0.82,  # Eclipse P75
        0.79,  # Eclipse P90
        0.91,  # KDE P50
        0.85,  # KDE P75
        0.65,  # KDE P90
        0.78,  # OpenXchange P50
        0.48,  # OpenXchange P75
        0.00,  # OpenXchange P90
        0.83,  # Novell P50
        0.75,  # Novell P75
        0.62   # Novell P90
    ],
    "Lasso": [
        0.85,  # Eclipse P50
        0.80,  # Eclipse P75
        0.72,  # Eclipse P90
        0.92,  # KDE P50
        0.85,  # KDE P75
        0.74,  # KDE P90
        0.72,  # OpenXchange P50
        0.38,  # OpenXchange P75
        0.00,  # OpenXchange P90
        0.84,  # Novell P50
        0.74,  # Novell P75
        0.64   # Novell P90
    ]
}

indici_righe = [
    "Eclipse_P50", "Eclipse_P75", "Eclipse_P90",
    "KDE_P50", "KDE_P75", "KDE_P90",
    "OpenXchange_P50", "OpenXchange_P75", "OpenXchange_P90",
    "Novell_P50", "Novell_P75", "Novell_P90"
]

df = pd.DataFrame(data, index=indici_righe)

# -----------------------------
# 2) Test globale di Friedman
# -----------------------------
fried_stat, fried_p = stats.friedmanchisquare(*[df[c] for c in df.columns])
print(f"Friedman Test: Chi-square={fried_stat:.3f}, p-value={fried_p:.5f}")

# -----------------------------
# 3) Post-hoc Nemenyi
# -----------------------------
test_results = sp.posthoc_nemenyi_friedman(df.values)
test_results.index = df.columns
test_results.columns = df.columns

# -----------------------------
# 4) Ranks e average ranks
# -----------------------------
# rank su ogni dataset (1 = miglior F1)
ranks = df.rank(axis=1, method="average", ascending=False)
avg_rank = ranks.mean(axis=0).sort_values()

print("\nAverage ranks (più basso = migliore):")
print(avg_rank.round(3))

# -----------------------------
# 5) Critical Difference Diagram
# -----------------------------
plt.figure(figsize=(10, 2.2), dpi=300)
#plt.title("Critical Difference Diagram (Friedman + Nemenyi)")
sp.critical_difference_diagram(avg_rank, test_results)
plt.tight_layout()
#plt.savefig("nemenyi_nemeny_test_f1_Fuzzy_VIT.png", dpi=300)
plt.savefig("out/plots/nemenyi_nemeny_test_f1_fast.png", dpi=300)