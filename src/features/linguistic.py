import math
import re
from src.utils.text_utils import clean_text, normalize_word
from src.utils.text_utils import count_syllables_word
from collections import Counter


def compute_text_entropy(bug):
    """
    Calcola l'entropia di Shannon sulla descrizione iniziale
    H = -Σ p(w) * log2(p(w))
    Misura la complessità informativa e la ricchezza del vocabolario della descrizione iniziale del bug (long_desc[0]).
    - Valori Bassi (< 3.0): Indicano un testo povero, estremamente ripetitivo 
    o generato automaticamente (es. log di errore ciclici).
    - Valori Medi (4.0 - 5.5): Rappresentano un bug report standard ben 
    strutturato, con un buon mix di linguaggio naturale e termini tecnici.
    - Valori Alti (> 6.0): Indicano una descrizione molto complessa, con 
    un vocabolario vasto e quasi nessuna ripetizione (alta densità informativa).
    """
    long_desc = bug.get("long_desc", [])
    if not long_desc:
        return 0.0
    
    # 1. Recuperiamo il testo grezzo
    raw_text = long_desc[0].get("thetext", "")
    
    # Pulizia del testo da termini tecnici e simboli
    cleaned_text = clean_text(raw_text)
    
    # 3. Dividere in parole 
    words = cleaned_text.lower().split()
    
    if not words:
        return 0.0
    
    # Calcolo delle frequenze relative p(w)
    total_words = len(words)
    word_counts = Counter(words)
    
    # Formula di Shannon
    entropy = 0.0
    for count in word_counts.values():
        p_w = count / total_words
        entropy -= p_w * math.log2(p_w)
        
    return entropy

def compute_lexical_diversity(cleaned_description_text):
    """
    Misura la varietà del vocabolario usato nella descrizione iniziale del bug
    Formula: LexicalDiversity = NumUniqueWords / NumTotalWords
    """
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", cleaned_description_text)

    if not words:
        return 0.0
    
    num_total = len(words)
    num_unique = len(set(w.lower() for w in words))
    
    return num_unique / num_total

def compute_flesch_reading_ease(description_words, num_sentences, bug):
    """
    Feature  Flesch Reading Ease.
    Misura la leggibilità della descrizione iniziale del bug (long_desc[0]). 
    Indica quanto sia "faticoso" per uno sviluppatore leggere e comprendere 
    il report iniziale.

    LOGICA DI CALCOLO:
    La metrica si basa sulla struttura sintattica (lunghezza delle frasi) e 
    sulla complessità lessicale (lunghezza delle parole in sillabe).
    Formula: 206.835 - 1.015 * (Words/Sentences) - 84.6 * (Syllables/Words)

    PARAMETRI DI ANALISI:
    1. Average Sentence Length (ASL): Più le frasi sono lunghe, più il punteggio scende.
    2. Average Syllables per Word (ASW): Più le parole sono lunghe/complesse, più il punteggio scende.

    INTERPRETAZIONE DEI VALORI:
    - 90.0 - 100.0: Molto facile (comprensibile da un bambino).
    - 60.0 - 70.0: Standard (linguaggio colloquiale/chiaro).
    - 30.0 - 50.0: Difficile (testo accademico o tecnico specialistico).
    - < 30.0: Molto difficile (testi legali o tecnici estremamente densi).
    """
    long_desc = bug.get("long_desc", [])
    if not long_desc or description_words == 0 or num_sentences == 0:
        return 0.0
    
    raw_text = long_desc[0].get("thetext", "")
    # Il testo viene pulito da stacktrace, codice, timestamp e versioni
    cleaned_description = clean_text(raw_text)
    # Il testo viene diviso in parole
    words_list = cleaned_description.split()
    # Calcolo totale sillabe
    total_syllables = sum(count_syllables_word(normalize_word(w)) for w in words_list)
    # Calcolo dei parametri ASL e ASW
    asl = description_words / num_sentences
    asw = total_syllables / description_words if description_words > 0 else 0
    # Formula di Flesch
    reading_ease = 206.835 - (1.015 * asl) - (84.6 * asw)
    
    return reading_ease

def compute_flesch_kincaid_grade(description_words, num_sentences, bug):
    """
    Misura il livello scolastico richiesto per comprendere il testo della descrizione del bug.
    Più alto è il valore, più il testo è complesso e richiede un lettore più istruito.

    LOGICA DI CALCOLO:
    La metrica ha una formula che si basa su due componenti principali: Lunghezza media delle frasi 
    e la complessità delle parole.
    Formula: 0.39 × (DescriptionWords / NumSentences) + 11.8 × (DescriptionSyllables / DescriptionWords) - 15.59

    PARAMETRI DI ANALISI:
    1. Average Sentence Length (ASL): Più le frasi sono lunghe, più il punteggio scende.
    2. Average Syllables per Word (ASW): Più le parole sono lunghe/complesse, più il punteggio scende.

    INTERPRETAZIONE DEI VALORI:
    - < 6   Scuola elementare   Testo semplicissimo
    - 6 - 8 Scuola media        Articoli giornalistici
    - 9 - 12 Liceo              Testi accademici base
    - 13 - 16 Università        Documentazione tecnica
    - > 16   Post-laurea        Testi scientifici avanzati
    """

    long_desc = bug.get("long_desc", [])
    if not long_desc or description_words == 0 or num_sentences == 0:
        return 0.0
    
    raw_text = long_desc[0].get("thetext", "")
    # Il testo viene pulito da stacktrace, codice, timestamp e versioni
    cleaned_description = clean_text(raw_text)
    # Il testo viene diviso in parole
    words_list = cleaned_description.split()
    # Calcolo totale sillabe
    total_syllables = sum(count_syllables_word(normalize_word(w)) for w in words_list)

    # Formula
    component1 = 0.39 * (description_words / num_sentences)
    component2 = 11.8 * (total_syllables / description_words)
    
    grade = component1 + component2 - 15.59

    return grade

def extract_linguistic_features(bug, calculated_features):
    description_words = calculated_features.get("description_words", 0)
    num_sentences = calculated_features.get("num_sentences", 0)
    cleaned_description_text = clean_text(bug.get("long_desc", [{}])[0].get("thetext", ""))   

    return{
        "text_entropy": compute_text_entropy(bug),
        "lexical_diversity": compute_lexical_diversity(cleaned_description_text),
        "flesch_reading_ease": compute_flesch_reading_ease(description_words, num_sentences, bug),
        "flesch_kincaid_grade": compute_flesch_kincaid_grade(description_words, num_sentences, bug),
    }