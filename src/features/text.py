from pydoc import text
import re
from src.utils.text_utils import *


def compute_description_chars(bug):
    """
    Calcola il numero di caratteri nella descrizione originale (long_desc[0]).
    """
    comments = bug.get("long_desc", [])
    
    if not comments:
        return 0
        
    description = comments[0].get("thetext", "")
    
    if not description:
        return 0
    
    # Pulizia base: rimuoviamo spazi bianchi superflui in testa e coda
    cleaned_description = description.strip()
    
    return len(cleaned_description)

def compute_description_words(cleaned_description):
    """
    Calcola il numero di parole nella descrizione originale (long_desc[0]).
    """
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b",cleaned_description)
    
    return len(words)

def compute_summary_words(cleaned_summary_text):
    """
    Conta le parole nel titolo (short_desc).
    """
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", cleaned_summary_text)
    return len(words)

def compute_num_sentences(cleaned_description_text):
    """
    Calcola il numero di frasi nella descrizione originale (long_desc[0]).
    """
    # Le frasi sono divise su punti reali seguiti da Spazio e Maiuscola (o fine riga)
    sentence_boundary = re.compile(r'[.!?]+(?:\s+(?=[A-Z])|$)')
    sentences = sentence_boundary.split(cleaned_description_text)

    return len(sentences)


def compute_avg_sentence_length(description_words, num_sentences):
    """
    Calcola la lunghezza media delle frasi.
    """
    if num_sentences == 0:
        return 0
    
    avg_length = description_words / num_sentences

    return avg_length

def compute_title_description_overlap(cleaned_description_text, cleaned_summary_text):
    """
    Andiamo a calcolare la coerenza tra titolo e descrizione iniziale. Riceve i testi già puliti, li trasforma in set di parole
    e calcola l'overlap ( TitleWords ∩ DescriptionWords / lunghezza titolo).
    """
    # 1. Definiamo le stopwords (se non sono globali)
    stopwords = {
        "the", "is", "a", "an", "on", "in", "at", "to", "for", "of", "and", 
        "or", "with", "by", "this", "that", "from", "as", "it", "be", "are", 
        "was", "were", "has", "have", "had"
    }

    # 2. Trasformiamo le stringhe pulite in SET di parole
    desc_words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", cleaned_description_text.lower())
    summ_words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", cleaned_summary_text.lower())
                            
    # Creiamo i set filtrando le stopwords
    description_set = {w for w in desc_words if w not in stopwords}
    summary_set = {w for w in summ_words if w not in stopwords}

    # 3. Calcolo dell'overlap
    if not summary_set:
        return 0.0

    shared_words = description_set.intersection(summary_set)
    
    return len(shared_words) / len(summary_set)

def compute_description_summary_ratio(description_words, summary_words):
    """ 
    Calcola il rapporto tra parole nella descrizione e parole nel titolo.
    """
    if summary_words == 0:
        return 0

    return description_words / summary_words

def extract_text_features(bug):
    cleaned_description_text = clean_text(bug.get("long_desc", [{}])[0].get("thetext", ""))   
    cleaned_summary_text = clean_text(bug.get("short_desc", ""))    
    description_words = compute_description_words(cleaned_description_text)
    summary_words = compute_summary_words(cleaned_summary_text)
    num_sentences = compute_num_sentences(cleaned_description_text)
    
    return {
        "description_chars": compute_description_chars(bug),
        "description_words": description_words,
        "summary_words": summary_words,
        "num_sentences": num_sentences,
        "avg_sentence_length": compute_avg_sentence_length(description_words, num_sentences),
        "title_description_overlap": compute_title_description_overlap(cleaned_description_text, cleaned_summary_text),
        "description_summary_ratio": compute_description_summary_ratio(description_words, summary_words),
    }