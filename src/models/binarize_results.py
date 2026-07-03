import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.metrics import classification_report

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------
MODELS = ['All_Features', 'Heuristic_Alta', 'Heuristic_Full', 'SelectKBest', 'Lasso']
LABELS_SHORT = ['All\nFeatures', 'Heur.\nAlta', 'Heur.\nFull', 'Select\nKBest', 'Lasso']
THRESHOLDS = ['P50', 'P75', 'P90']
THR_TITLES = {
    'P50': 'P50 — soglia mediana',
    'P75': 'P75 — 75° percentile',
    'P90': 'P90 — 90° percentile',
}

# Colori e Stili
BLUE  = '#3266AD'
CORAL = '#D85A30'
BG    = '#FAFAF8'
GRID  = '#E8E6E0'

def binarizza_risultati(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Errore: Il file {input_path} non è stato trovato!")
        return

    df = pd.read_csv(input_path)

    # Calcolo soglie percentili
    soglie = {
        'P50': df['real_time'].quantile(0.50),
        'P75': df['real_time'].quantile(0.75),
        'P90': df['real_time'].quantile(0.90),
    }

    bin_df = pd.DataFrame({'real_time': df['real_time']})
    cols_to_bin = [c for c in df.columns if c != 'real_time']

    for nome_soglia, valore in soglie.items():
        bin_df[f'real_{nome_soglia}'] = (df['real_time'] <= valore).astype(int)
        for col in cols_to_bin:
            bin_df[f'{col}_{nome_soglia}'] = (df[col] <= valore).astype(int)

    bin_df.to_csv(output_path, index=False)
    print(f"Binarizzazione completata. File salvato in: {output_path}")

    # Creazione cartella per i grafici
    plot_dir = os.path.join('out', 'plots')
    os.makedirs(plot_dir, exist_ok=True)  
    
    _genera_grafici(bin_df, plot_dir)

def _raccogli_metriche(bin_df):
    metriche = {thr: {'recall': {}, 'precision': {}, 'f1': {}} for thr in THRESHOLDS}
    for thr in THRESHOLDS:
        real_col = f'real_{thr}'
        for classe, key in [('1', 'fast'), ('0', 'slow')]:
            recalls, precisions, f1s = [], [], []
            for model in MODELS:
                pred_col = f'pred_{model}_{thr}'
                rep = classification_report(
                    bin_df[real_col], bin_df[pred_col],
                    output_dict=True, zero_division=0
                )
                recalls.append(rep[classe]['recall'])
                precisions.append(rep[classe]['precision'])
                f1s.append(rep[classe]['f1-score'])
            metriche[thr]['recall'][key]    = recalls
            metriche[thr]['precision'][key] = precisions
            metriche[thr]['f1'][key]        = f1s
    return metriche

def _disegna_grafico(metriche, metrica_key, titolo, filename, output_dir):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)
    fig.patch.set_facecolor(BG)
    fig.suptitle(titolo, fontsize=13, fontweight='bold', y=1.01, color='#1a1a18')

    x = range(len(MODELS))

    for ax, thr in zip(axes, THRESHOLDS):
        ax.set_facecolor(BG)
        fast = metriche[thr][metrica_key]['fast']
        slow = metriche[thr][metrica_key]['slow']

        ax.plot(x, fast, color=BLUE,  linewidth=2, marker='o',  markersize=6, label='Fast (1)', zorder=3)
        ax.plot(x, slow, color=CORAL, linewidth=2, marker='^',  markersize=7, linestyle='--', label='Slow (0)', zorder=3)

        for xi, (f, s) in enumerate(zip(fast, slow)):
            ax.text(xi, f + 0.008, f'{f:.2f}', ha='center', va='bottom', fontsize=8, color=BLUE)
            ax.text(xi, s - 0.015, f'{s:.2f}', ha='center', va='top', fontsize=8, color=CORAL)

        ax.set_title(THR_TITLES[thr], fontsize=10, color='#444441', pad=8)
        ax.set_xticks(list(x))
        ax.set_xticklabels(LABELS_SHORT, fontsize=8.5, color='#444441')
        ax.set_ylim(0.60, 1.05)
        ax.tick_params(axis='y', labelsize=8, colors='#888780')
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color=GRID, linewidth=0.8, zorder=0)

    handles, lgs = axes[0].get_legend_handles_labels()
    fig.legend(handles, lgs, loc='lower center', ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.06))

    plt.tight_layout()
    out_path = os.path.join(output_dir, filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f"Grafico salvato in: {out_path}")

def _genera_grafici(bin_df, output_dir):
    metriche = _raccogli_metriche(bin_df)
    _disegna_grafico(metriche, 'recall', 'Recall per classe: Fast vs Slow', 'recall_fast_vs_slow.png', output_dir)
    _disegna_grafico(metriche, 'precision', 'Precision per classe: Fast vs Slow', 'precision_fast_vs_slow.png', output_dir)
    _disegna_grafico(metriche, 'f1', 'F1-score per classe: Fast vs Slow', 'f1_fast_vs_slow.png', output_dir)

if __name__ == "__main__":
    binarizza_risultati(
        'data/processed/confronto_modelli.csv',
        'data/processed/confronto_binarizzato.csv'
    )