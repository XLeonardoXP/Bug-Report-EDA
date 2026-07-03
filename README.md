# Bug Report EDA

Progetto per l’analisi della qualità linguistica dei bug report generati tramite Bugzilla, attraverso l’estrazione di feature linguistiche e temporali e l’addestramento di modelli di machine learning.

---

# 📌 Obiettivi del Progetto

Il progetto ha i seguenti obiettivi:

* estrarre feature linguistiche e temporali dai bug report;
* analizzare la qualità dei report tramite tecniche di Exploratory Data Analysis (EDA);
* addestrare e valutare modelli di machine learning;
* confrontare statisticamente le performance dei modelli ottenuti.

---

# 📂 Struttura del Progetto

```text id="h8r2fa"
.
├── data
│   ├── raw/                # Dataset JSON originali
│   └── processed/          # Dataset CSV elaborati
│
├── notebooks/              # Notebook per EDA e analisi
│
├── out/                    # Output dei modelli e grafici
│
├── src
│   ├── features/           # Calcolo feature linguistiche e temporali
│   ├── models/             # Training e valutazione modelli
│   ├── statistic_test/     # Test statistici
│   └── utils/              # Funzioni di utilità
│
├── app.py                  # Script principale
├── requirements.txt        # Dipendenze del progetto
└── README.md
```

---

# 🚀 Installazione

## Prerequisiti

* Python 3.8+
* pip

## Installazione dipendenze

Dalla root del progetto eseguire:

```bash id="v8j5ow"
pip install -r requirements.txt
```

---

# 💻 Guida all’Esecuzione

## 1. Inserimento del dataset

Posizionare il file JSON sorgente nella cartella:

```text id="8hkh9s"
data/raw/
```

---

## 2. Elaborazione dei dati

Eseguire lo script principale dalla root del progetto:

```bash id="3d7g0m"
python app.py
```

Questo passaggio:

* legge i file JSON;
* estrae le feature;
* genera i dataset CSV elaborati.

---

## 3. Exploratory Data Analysis (EDA)

Aprire ed eseguire il notebook:

```text id="6md5l8"
notebooks/advanced_eda.ipynb
```

Il notebook consente di:

* visualizzare statistiche descrittive;
* analizzare correlazioni tra feature;
* generare grafici esplorativi.

---

## 4. Addestramento dei Modelli

Accedere alla cartella:

```text id="6h5z4r"
src/models/
```

Eseguire in sequenza:

```bash id="g7hz5q"
python train.py
python binarize_results.py
python evaluate.py
```

### Script disponibili

| Script                | Descrizione                             |
| --------------------- | --------------------------------------- |
| `train.py`            | Addestra i modelli di machine learning  |
| `binarize_results.py` | Converte i risultati in formato binario |
| `evaluate.py`         | Valuta le performance dei modelli       |

---

# 📊 Output Generati

La cartella `out/` contiene:

* matrici di confusione;
* grafici delle performance;
* metriche di valutazione;
* risultati dei modelli.

---

# 📈 Test Statistici

Per confrontare statisticamente i modelli:

1. Inserire i risultati nella cartella dedicata.
2. Accedere a:

```text id="eqlt80"
src/statistic_test/
```

3. Eseguire:

```bash id="uxn1na"
python confronto_risultati.py
python nemenyi_test.py
```

### Script disponibili

| Script                   | Descrizione                          |
| ------------------------ | ------------------------------------ |
| `confronto_risultati.py` | Confronta i risultati dei modelli    |
| `nemenyi_test.py`        | Esegue il test statistico di Nemenyi |

---

# 🛠 Tecnologie Utilizzate

* Python
* Pandas
* NumPy
* Scikit-learn
* Matplotlib
* Seaborn
* Jupyter Notebook

---

# 📄 Licenza

Questo progetto è distribuito con finalità accademiche e di ricerca.
