import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.metrics import classification_report, confusion_matrix

def analizza_modelli(input_path, output_dir='out/confusion_matrices'):
    # Crea la cartella per le matrici se non esiste
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = pd.read_csv(input_path)
    
    soglie = ['P50', 'P75', 'P90']
    modelli = [c.replace('_P50', '') for c in df.columns if '_P50' in c and 'real' not in c]

    for soglia in soglie:
        print(f"\n" + "="*50)
        print(f"--- REPORT CLASSIFICAZIONE: SOGLIA {soglia} ---")
        print("="*50)
        
        real_col = f'real_{soglia}'
        
        for modello in modelli:
            pred_col = f'{modello}_{soglia}'
            
            # 1. Stampa il Classification Report
            print(f"\nModello: {modello}")
            print(classification_report(df[real_col], df[pred_col]))
            
            # 2. Genera e salva la Matrice di Confusione
            cm = confusion_matrix(df[real_col], df[pred_col])
            
            plt.figure(figsize=(5, 4))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                        xticklabels=['Slow (0)', 'Fast (1)'], 
                        yticklabels=['Slow (0)', 'Fast (1)'])
            plt.title(f'Matrice di Confusione: {modello} ({soglia})')
            plt.ylabel('Reale')
            plt.xlabel('Predizione')
            
            plt.savefig(f'{output_dir}/cm_{modello}_{soglia}.png')
            plt.close()
            
    print(f"\nAnalisi completata. Le 15 matrici di confusione sono state salvate in: {output_dir}/")

if __name__ == "__main__":
    analizza_modelli('data/processed/confronto_binarizzato.csv')