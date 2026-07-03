import math
from src.utils.date_utils import *
from src.features.collaboration import compute_num_comments
from src.features.collaboration import compute_num_participants


def compute_fixing_time(bug):
    """
    Restituisce il numero di giorni tra apertura e risoluzione.
    Usa il campo days_resolution già presente nel JSON.
    Restituisce None se il bug non è ancora risolto.
    """
    value = bug.get("days_resolution")
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
    
def compute_time_to_first_comment(bug):
    """
    Calcola la differenza in giorni tra la creazione del bug e il primo commento di risposta,
    gestendo dinamicamente l'ordine dei commenti (oldest vs newest).
    """
    creation_ts = bug.get("creation_ts")
    comments = bug.get("long_desc", [])
    sort_order = bug.get("comment_sort_order", "oldest_to_newest") # Default standard

    # Ci serve almeno la descrizione (0) e una risposta (1)
    if not creation_ts or len(comments) < 2:
        return None

    dt_creation = parse_bug_date(creation_ts)
    
    # Identifichiamo la prima risposta in base all'ordine
    if sort_order == "oldest_to_newest":
        # Il primo commento utile è all'indice 1
        dt_first_comment = parse_bug_date(comments[1].get("bug_when"))
    else:
        # Se è newest_to_oldest, il primo commento cronologico è l'ultimo della lista
        # (L'indice 0 sarebbe l'ultimo commento scritto in ordine di tempo)
        dt_first_comment = parse_bug_date(comments[-1].get("bug_when"))

    if dt_creation and dt_first_comment:
        diff = dt_first_comment - dt_creation
        days = diff.total_seconds() / 86400
        
        # Applichiamo il logaritmo naturale log(1 + x)
        # Assicuriamoci che days non sia negativo (raro, ma per sicurezza)
        log_days = math.log1p(max(0, days))
        
        return log_days
    
    return None

def compute_avg_comment_gap(bug):
    """
    Calcola il tempo medio logaritmico tra commenti consecutivi.
    """
    gaps = get_comment_gaps(bug, parse_bug_date)
    
    if not gaps:
        return 0.0

    avg_gap = sum(gaps) / len(gaps)
    return math.log1p(avg_gap)

def compute_max_silence(bug):
    """
    Calcola il massimo periodo di inattività logaritmico tra commenti.
    """
    gaps = get_comment_gaps(bug, parse_bug_date)
    
    if not gaps:
        return 0.0

    max_gap = max(gaps)
    return math.log1p(max_gap)


def compute_activity_density(bug):
    """
    Calcola l'activity density riutilizzando le funzioni num_comments e num_participants.
    Formula: (NumComments + NumActivity) / num_participants
    """
    # Riutilizzo delle funzioni esistenti
    num_comments = compute_num_comments(bug)
    num_participants = compute_num_participants(bug)

    
    try:
        num_activity = int(bug.get("nr_activities", 0))
    except (ValueError, TypeError):
        num_activity = 0
        
    # Calcolo della densità
    density = (num_comments + num_activity) / num_participants if num_participants > 0 else 1
    return density
        

def extract_temporal_features(bug):
    return {
        "fixing_time": compute_fixing_time(bug),
        "time_to_first_comment": compute_time_to_first_comment(bug),
        "avg_comment_gap": compute_avg_comment_gap(bug),
        "max_silence": compute_max_silence(bug),
        "activity_density":compute_activity_density(bug),
    }