import matplotlib.pyplot as plt
import numpy as np

# Configurazione dello stile accademico per la tesi
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 0.8

# Nomi dei 4 dataset comuni a tutte le analisi
datasets = ['Eclipse', 'W3C', 'OpenOffice', 'Mozilla']
x = np.arange(len(datasets))
width = 0.23  # Larghezza delle barre affiancate
colors = ['#4A6984', '#96A8B3', '#D18A6A'] # All Features, Heuristic Full, SelectKBest

def add_classification_labels(ax):
    """Aggiunge il valore numerico decimale sopra ogni barra (F1-Score)"""
    for rect in ax.patches:
        height = rect.get_height()
        if height >= 0:
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),  # 4 punti di spazio sopra la barra
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=7.5, rotation=90)

def add_regression_labels(ax):
    """Aggiunge il valore numerico intero sopra ogni barra (MSE)"""
    for rect in ax.patches:
        height = rect.get_height()
        if height > 0:
            ax.annotate(f'{height:.0f}',  # Formato intero per non affollare le cifre dell'MSE
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5),  # 5 punti di spazio sopra la barra
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, rotation=90)


# =================================================================
# 1. PARTE FAST (CLASSE 1) - CLASSIFICAZIONE
# =================================================================

f1_fast_p50_all  = [0.87, 0.75, 0.84, 0.86]  
f1_fast_p50_heur = [0.89, 0.76, 0.79, 0.88]  
f1_fast_p50_skb  = [0.89, 0.80, 0.84, 0.88]  

f1_fast_p75_all  = [0.94, 0.85, 0.95, 0.94]  
f1_fast_p75_heur = [0.94, 0.87, 0.95, 0.94]  
f1_fast_p75_skb  = [0.94, 0.88, 0.96, 0.94]  

f1_fast_p90_all  = [0.97, 0.94, 0.98, 0.97]  
f1_fast_p90_heur = [0.98, 0.94, 0.99, 0.97]  
f1_fast_p90_skb  = [0.98, 0.94, 0.99, 0.97]  

fig_fast, axes_fast = plt.subplots(1, 3, figsize=(16, 5), sharey=True)

# Pannello 1: P50 FAST
b1 = axes_fast[0].bar(x - width, f1_fast_p50_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
b2 = axes_fast[0].bar(x, f1_fast_p50_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
b3 = axes_fast[0].bar(x + width, f1_fast_p50_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)
axes_fast[0].set_title('Soglia Percentile $P_{50}$', fontsize=12, fontweight='bold', pad=10)
axes_fast[0].set_ylabel('$F_1$-Score (Classe 1 - FAST)')
axes_fast[0].set_xticks(x)
axes_fast[0].set_xticklabels(datasets)
axes_fast[0].grid(axis='y', linestyle='--', alpha=0.5)
add_classification_labels(axes_fast[0])

# Pannello 2: P75 FAST
axes_fast[1].bar(x - width, f1_fast_p75_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
axes_fast[1].bar(x, f1_fast_p75_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
axes_fast[1].bar(x + width, f1_fast_p75_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)
axes_fast[1].set_title('Soglia Percentile $P_{75}$', fontsize=12, fontweight='bold', pad=10)
axes_fast[1].set_xticks(x)
axes_fast[1].set_xticklabels(datasets)
axes_fast[1].grid(axis='y', linestyle='--', alpha=0.5)
add_classification_labels(axes_fast[1])

# Pannello 3: P90 FAST
axes_fast[2].bar(x - width, f1_fast_p90_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
axes_fast[2].bar(x, f1_fast_p90_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
axes_fast[2].bar(x + width, f1_fast_p90_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)
axes_fast[2].set_title('Soglia Percentile $P_{90}$', fontsize=12, fontweight='bold', pad=10)
axes_fast[2].set_xticks(x)
axes_fast[2].set_xticklabels(datasets)
axes_fast[2].grid(axis='y', linestyle='--', alpha=0.5)
add_classification_labels(axes_fast[2])

# Impostazione del limite Y per i pannelli FAST
for ax in axes_fast:
    ax.set_ylim(0, 1.18)

fig_fast.legend([b1, b2, b3], ['All Features', 'Heuristic Full', 'SelectKBest ($k=12$)'], 
                loc='lower center', bbox_to_anchor=(0.5, 0.01), ncol=3, frameon=True, edgecolor='gray')
fig_fast.subplots_adjust(bottom=0.15, left=0.06, right=0.98, top=0.88, wspace=0.18)

output_fast = 'out/plots/f1_score_fast_all_percentiles.pdf'
fig_fast.savefig(output_fast, dpi=300)
plt.close(fig_fast)
print(f"[OK] 1/3 Grafico Classificazione FAST salvato in: {output_fast}")


# =================================================================
# 2. PARTE SLOW (CLASSE 0) - CLASSIFICAZIONE
# =================================================================

f1_slow_p50_all  = [0.87, 0.62, 0.83, 0.86]  
f1_slow_p50_heur = [0.88, 0.69, 0.78, 0.87]  
f1_slow_p50_skb  = [0.89, 0.75, 0.84, 0.87]  

f1_slow_p75_all  = [0.81, 0.09, 0.83, 0.79]  
f1_slow_p75_heur = [0.82, 0.31, 0.83, 0.80]  
f1_slow_p75_skb  = [0.82, 0.32, 0.87, 0.80]  

f1_slow_p90_all  = [0.73, 0.00, 0.76, 0.63]  
f1_slow_p90_heur = [0.76, 0.00, 0.88, 0.69]  
f1_slow_p90_skb  = [0.78, 0.00, 0.88, 0.70]  

fig_slow, axes_slow = plt.subplots(1, 3, figsize=(16, 5), sharey=True)

# Pannello 1: P50 SLOW
b1 = axes_slow[0].bar(x - width, f1_slow_p50_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
b2 = axes_slow[0].bar(x, f1_slow_p50_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
b3 = axes_slow[0].bar(x + width, f1_slow_p50_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)
axes_slow[0].set_title('Soglia Percentile $P_{50}$', fontsize=12, fontweight='bold', pad=10)
axes_slow[0].set_ylabel('$F_1$-Score (Classe 0 - SLOW)')
axes_slow[0].set_xticks(x)
axes_slow[0].set_xticklabels(datasets)
axes_slow[0].grid(axis='y', linestyle='--', alpha=0.5)
add_classification_labels(axes_slow[0])

# Pannello 2: P75 SLOW
axes_slow[1].bar(x - width, f1_slow_p75_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
axes_slow[1].bar(x, f1_slow_p75_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
axes_slow[1].bar(x + width, f1_slow_p75_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)
axes_slow[1].set_title('Soglia Percentile $P_{75}$', fontsize=12, fontweight='bold', pad=10)
axes_slow[1].set_xticks(x)
axes_slow[1].set_xticklabels(datasets)
axes_slow[1].grid(axis='y', linestyle='--', alpha=0.5)
add_classification_labels(axes_slow[1])

# Pannello 3: P90 SLOW
axes_slow[2].bar(x - width, f1_slow_p90_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
axes_slow[2].bar(x, f1_slow_p90_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
axes_slow[2].bar(x + width, f1_slow_p90_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)
axes_slow[2].set_title('Soglia Percentile $P_{90}$', fontsize=12, fontweight='bold', pad=10)
axes_slow[2].set_xticks(x)
axes_slow[2].set_xticklabels(datasets)
axes_slow[2].grid(axis='y', linestyle='--', alpha=0.5)
add_classification_labels(axes_slow[2])

# Impostazione del limite Y per i pannelli SLOW
for ax in axes_slow:
    ax.set_ylim(0, 1.18)

fig_slow.legend([b1, b2, b3], ['All Features', 'Heuristic Full', 'SelectKBest ($k=12$)'], 
                loc='lower center', bbox_to_anchor=(0.5, 0.01), ncol=3, frameon=True, edgecolor='gray')
fig_slow.subplots_adjust(bottom=0.15, left=0.06, right=0.98, top=0.88, wspace=0.18)

output_slow = 'out/plots/f1_score_slow_all_percentiles.pdf'
fig_slow.savefig(output_slow, dpi=300)
plt.close(fig_slow)
print(f"[OK] 2/3 Grafico Classificazione SLOW salvato in: {output_slow}")


# =================================================================
# 3. PARTE REGRESSIONE (MSE) - NUOVA INTEGRAZIONE
# =================================================================

mse_all  = [29325.41, 17307.65, 65686.82, 28591.06]
mse_heur = [27978.32, 17146.29, 35555.84, 25659.88]
mse_skb  = [24080.97, 16103.41, 29849.55, 23915.99]

fig_mse, ax_mse = plt.subplots(figsize=(10, 6))

# Generazione delle barre per l'MSE
b1_mse = ax_mse.bar(x - width, mse_all, width, color=colors[0], edgecolor='black', linewidth=0.5)
b2_mse = ax_mse.bar(x, mse_heur, width, color=colors[1], edgecolor='black', linewidth=0.5)
b3_mse = ax_mse.bar(x + width, mse_skb, width, color=colors[2], edgecolor='black', linewidth=0.5)

ax_mse.set_title('Confronto del Mean Squared Error (MSE) nella Regressione SVR', fontsize=12, fontweight='bold', pad=15)
ax_mse.set_ylabel('Mean Squared Error (MSE)')
ax_mse.set_xticks(x)
ax_mse.set_xticklabels(datasets)
ax_mse.grid(axis='y', linestyle='--', alpha=0.5)

# Aggiunta etichette specifiche per la regressione
add_regression_labels(ax_mse)

# Alziamo il limite dell'asse Y per non tagliare le scritte sopra il picco di OpenOffice
ax_mse.set_ylim(0, max(mse_all) * 1.22)

# Legenda posizionata sul fondo in modo coerente
ax_mse.legend([b1_mse, b2_mse, b3_mse], ['All Features', 'Heuristic Full', 'SelectKBest ($k=12$)'], 
              loc='lower center', bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=True, edgecolor='gray')

fig_mse.subplots_adjust(bottom=0.18, left=0.10, right=0.95, top=0.90)

output_mse = 'out/plots/svr_mse_comparison.pdf'
fig_mse.savefig(output_mse, dpi=300)
plt.close(fig_mse)
print(f"[OK] 3/3 Grafico Regressione MSE salvato in: {output_mse}")


print("\n[FINISH] Tutti e tre i file PDF per la tesi sono stati generati correttamente!")