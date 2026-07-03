import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import Lasso


def get_predictions(X_train, X_test, y_train, y_test, experiment_name):
    # Standardizzazione
    #SVR si basa sulla distanza euclidea: calcola quanto sono lontani i punti nello spazio
    #Porta tutte le feature ad avere media 0 e varianza 1. In questo modo, ogni feature parte 
    #dalla stessa linea di partenza e nessuna "soverchia" le altre a causa della sua scala.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Addestramento
    # il kernel permetto al modello di gestire relazioni non lineari 

    svr = SVR(kernel='rbf')
    svr.fit(X_train_scaled, y_train)

    # === RIGHE AGGIUNTE PER IL SALVATAGGIO ===
    joblib.dump(scaler, f'data/models/scaler_{experiment_name}.joblib')
    joblib.dump(svr, f'data/models/svr_{experiment_name}.joblib')
    # ========================================
    
    # Predizione (ritorno al dominio reale)
    y_pred = np.expm1(svr.predict(X_test_scaled))
    y_pred = np.maximum(y_pred, 0)
    
    return pd.Series(y_pred, name=f'pred_{experiment_name}', index=y_test.index)   

def get_intelligent_feature_groups(csv_path):
    df = pd.read_csv(csv_path)

    df['abs_corr'] = df['correlation'].abs()
    val_media = df['abs_corr'].mean()
    val_std = df['abs_corr'].std()
    soglia_alta = val_media + (0.5 * val_std)
    soglia_media = val_media
    
    alta_cols = df[df['abs_corr'] >= soglia_alta]['feature'].tolist()
    media_cols = df[(df['abs_corr'] < soglia_alta) & (df['abs_corr'] >= soglia_media)]['feature'].tolist()
    return alta_cols, media_cols

def main():
    # 1. Caricamento dati
    df = pd.read_csv('data/processed/features.csv').drop(columns=['bug_id'])
    #Il tempo di fixing è una feature a coda lunga, questo significa che la maggior parte 
    #dei bug ha un tempo di risoluzione di pochi giorni
    #se non appplicassimo il logaritmo il modello verrebbe distratto dai pochi valori alti
    #Il logaritmo schiaccia i valori alti ed espande quelli bassi    
    y = np.log1p(df['fixing_time'])
    X_all = df.drop(columns=['fixing_time'])
    feature_names = X_all.columns

    # 2. Split unico per tutti i modelli (fondamentale per il confronto)
    X_train, X_test, y_train, y_test = train_test_split(X_all, y, test_size=0.2, random_state=42)

    X_train = X_train.fillna(0.0)
    X_test = X_test.fillna(0.0)
    
    # Inizializza dataframe risultati con il valore reale
    results_df = pd.DataFrame({'real_time': np.expm1(y_test)})

    # 3. Ottenimento gruppi feature
    alta_cols, media_cols = get_intelligent_feature_groups('notebooks/correlation_with_fixing_time.csv')

    # --- ESPERIMENTI ---
    # Baseline: tutte le feature
    results_df = results_df.join(get_predictions(X_train, X_test, y_train, y_test, "All_Features"))

    # Heuristic: Alta
    results_df = results_df.join(get_predictions(X_train[alta_cols], X_test[alta_cols], y_train, y_test, "Heuristic_Alta"))
    print(f"\n[DEBUG] Feature Alta Correlazione ({len(alta_cols)}): {alta_cols}")

    # Heuristic: Alta + Media
    full_cols = alta_cols + media_cols
    print(f"\n[DEBUG] Feature Alta + Media Correlazione ({len(full_cols)}): {full_cols}")
    results_df = results_df.join(get_predictions(X_train[full_cols], X_test[full_cols], y_train, y_test, "Heuristic_Full"))

    # SelectKBest
    selector = SelectKBest(score_func=f_regression, k=12).fit(X_train, y_train)
    kbest_cols = feature_names[selector.get_support()]
    print(f"\n[DEBUG] Feature SelectKBest ({len(kbest_cols)}): {kbest_cols.tolist()}")
    results_df = results_df.join(get_predictions(X_train[kbest_cols], X_test[kbest_cols], y_train, y_test, "SelectKBest"))

    # Lasso
    lasso = Lasso(alpha=0.01).fit(X_train, y_train)
    lasso_cols = feature_names[lasso.coef_ != 0]
    print(f"\n[DEBUG] Feature Lasso ({len(lasso_cols)}): {lasso_cols.tolist()}")
    results_df = results_df.join(get_predictions(X_train[lasso_cols], X_test[lasso_cols], y_train, y_test, "Lasso"))

    # 4. Salvataggio
    results_df.to_csv('data/processed/confronto_modelli.csv', index=False)
    print("\nFile 'confronto_modelli.csv' generato con successo!")
    
    # Print MAE finale per conferma
    for col in results_df.columns:
        if col.startswith('pred_'):
            mae = mean_absolute_error(results_df['real_time'], results_df[col])
            mse = mean_squared_error(results_df['real_time'], results_df[col])
            print(f"{col}: MAE {mae:.2f} | MSE {mse:.2f}")

if __name__ == "__main__":
    main()