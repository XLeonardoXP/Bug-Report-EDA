from src.utils.text_utils import clean_text
import re
import numpy as np

"""
def compute_num_comments(bug):
    ".""
    Calcola il numero totale di commenti.
    Estrae il valore massimo dal campo comment_count per gestire
    qualsiasi tipo di ordinamento (oldest/newest).
    ""."
    comments = bug.get("long_desc", [])
    if not comments:
        return 0

    counts = []
    for c in comments:
        try:
            # Estraiamo il valore di comment_count e lo convertiamo in intero
            val = int(c.get("comment_count", 0))
            counts.append(val)
        except (ValueError, TypeError):
            continue
    
    # Il numero totale di commenti è il valore massimo trovato
    if not counts:
        return len(comments) # Fallback alla lunghezza della lista
        
    return max(counts)
"""
def compute_num_comments(bug):
    """
    Calcola il numero totale di commenti di discussione,
    escludendo il primo elemento che rappresenta la descrizione estesa del bug.
    """
    comments = bug.get("long_desc", [])
    
    # Se non ci sono elementi o c'è solo la descrizione iniziale, i commenti di risposta sono 0
    if len(comments) <= 1:
        return 0
        
    # Sottrae 1 per escludere la descrizione iniziale del bug
    return len(comments) - 1

def compute_num_participants(bug):
    """
    Conta il numero di utenti unici che hanno partecipato alla discussione
    tramite i commenti (long_desc).
    """
    comments = bug.get("long_desc", [])
    
    if not comments:
        return 0
    # Usiamo un set per memorizzare gli utenti unici
    # Il set elimina automaticamente i duplicati
    participants = set()
    
    for comment in comments:
        user = comment.get("who")
        if user:
            participants.add(user)
            
    return len(participants)

def compute_avg_comment_length(bug):
    """
    Calcola la lunghezza media dei commenti (in parole) nella discussione.
    """
    comments = bug.get("long_desc", [])
    # Se non ci sono commenti oltre alla descrizione (indice 0), la media è 0
    if len(comments) <= 1:
        return 0.0
    total_words = 0
    # Consideriamo solo i commenti dal secondo in poi (la discussione vera e propria)
    discussion_comments = comments[1:]
    num_discussion_comments = len(discussion_comments)
    
    for comment in discussion_comments:
        raw_text = comment.get("thetext", "")
        if not raw_text:
            continue
        # 1. pulizia dei commenti da parole tecniche
        cleaned_text = clean_text(raw_text)
        # 2. conteggio parole usando regex per contare solo parole reali (escludendo numeri e simboli)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', cleaned_text)
        total_words += len(words)
        
    avg_length = total_words / num_discussion_comments
    
    return avg_length

def compute_discussion_intensity(num_comments, num_participants):
    """
    Calcola l'intensità della discussione combinando il tasso di coinvolgimento 
    medio con il volume assoluto dei commenti. Esclude fixing_time per evitare leakage.
    """
    # Condizione di guardia: se non ci sono commenti o partecipanti, l'intensità è zero
    if num_participants == 0 or num_comments == 0:
        return 0.0
        
    # Rapporto base: quanti commenti scrive in media ogni persona
    avg_comments_per_user = num_comments / num_participants
    
    # Moltiplichiamo per il numero totale di commenti (num_comments) per "pesare" il volume.
    # In questo modo, 100 commenti / 10 persone (valore pesato = 100) 
    # diventa giustamente più importante di 10 commenti / 1 persona (valore pesato = 10).
    weighted_intensity = avg_comments_per_user * num_comments
    
    # Applichiamo il logaritmo naturale (np.log1p) per stabilizzare la varianza,
    # schiacciare gli outlier ed evitare che la feature domini ingiustamente sulle altre.
    return float(np.log1p(weighted_intensity))
        
def compute_discussion_description_ratio(bug, description_length):
    comments = bug.get("long_desc", [])
    total_comment_words = 0
    
    if len(comments) > 1:
        discussion_comments = comments[1:]
        for comment in discussion_comments:
            raw_text = comment.get("thetext", "")
            if raw_text:
                # Applichiamo la stessa pulizia vista finora
                cleaned_text = clean_text(raw_text)
                words = re.findall(r'\b[a-zA-Z]{2,}\b', cleaned_text)
                total_comment_words += len(words)
                
    # 3. Applica la formula finale
    ratio = total_comment_words / (description_length + 1)
    
    return ratio

def compute_clarification_request_count(bug):
    """"
    Conta il numero di commenti nei quali viene richiesto un chiarimento sul bug, trovando parole come clarify, more details
    """
    long_desc = bug.get("long_desc")
    # I commenti partono da index 1, index 0 è la descrizione
    comments = long_desc[1:]

    if not comments:
        return 0

    # Pattern di richiesta chiarimento

    clarification_patterns = re.compile(
        r'\b('
        r'clarif\w*|needs? clarification|'
        r'more details?|additional details|further details|'
        r'need(?:s)? more information|provide more information|insufficient information|'
        r'elaborat\w*|explain (?:further|more)|'
        r'what do you mean|can you explain|could you explain|what exactly|'
        r'how to reproduc\w*|repro steps|'
        # Blindiamo 'version' per evitare che matchi "PRODUCT VERSION"
        r'(?:what|which|how to check)\s+(?:browser|os|environment|system)?\s*version'
        r')\b',
        re.IGNORECASE,)
    
    count = 0

    for comment in comments:
        text = comment.get("thetext", "")
        if not text:
            continue
            
        # Dividiamo il commento in righe
        lines = text.splitlines()
        
        found_in_comment = False
        for line in lines:
            clean_line = line.strip()
            
            # Se la riga è una citazione (inizia con '>'), la saltiamo
            if clean_line.startswith(">"):
                continue
                
            # Cerchiamo il pattern solo nella riga "nuova" (non citata)
            if clarification_patterns.search(clean_line):
                found_in_comment = True
                break # Trovata una richiesta, passiamo al commento successivo
        
        if found_in_comment:
            count += 1

    return count

def compute_clarification_burden(clarification_request_count, num_comments):
    """
    Misura il peso proporzionale delle richieste di chiarimento rispetto al totale dei commenti.
    """

    clarification_burden = clarification_request_count / (num_comments + 1)

    return clarification_burden

def compute_coordination_complexity(num_participants, num_comments, avg_comment_length):
    """
    Calcola la complessità di coordinazione basandosi sui canali di comunicazione potenziali.
    Risolve il problema del data leakage eliminando il riferimento al tempo di fixing totale.
    """
    # Se c'è meno di un partecipante, non esiste complessità di coordinazione relazionale
    if num_participants <= 1:
        return 0.0
        
    # Formula combinatoria dei canali di comunicazione unici: n * (n - 1) / 2
    communication_channels = (num_participants * (num_participants - 1)) / 2
    
    # Calcolo dell'interazione geometrica tra canali, volume dei messaggi e ricchezza testuale
    raw_complexity = communication_channels * num_comments * avg_comment_length
    
    # Trasformazione logaritmica per stabilizzare la varianza ed evitare outlier estremi
    return float(np.log1p(raw_complexity))

def compute_has_cannot_reproduce(bug):
    """
    Feature binaria che indica se nella discussione del bug è presente almeno un commento che menziona "cannot reproduce" o varianti simili.
    """
    long_desc = bug.get("long_desc", [])
    if len(long_desc) <= 1:
        return 0
        
    comments = long_desc[1:]

    reproduce_patterns = re.compile(
        r'\b('
        r'cannot reproduce|can\'t reproduce|couldnot reproduce|couldn\'t reproduce|'
        r'not able to reproduce|unable to reproduce|'
        r'works for me|worksforme|'
        r'failed to reproduce|cannot replicate'
        r')\b', 
        re.IGNORECASE
    )

    for comment in comments:
        text = comment.get("thetext", "")
        
        # Pulizia citazioni per evitare di contare quando uno sviluppatore 
        # risponde a un utente che aveva detto "it works for me"
        text_clean = re.sub(r'^>.*$', '', text, flags=re.MULTILINE)
        
        if reproduce_patterns.search(text_clean):
            # Restituiamo 1 (True) appena troviamo la prima occorrenza
            return 1
            
    return 0

def extract_collaboration_features(bug, calculated_features):
    description_length = calculated_features.get("description_words", 0)
    avg_comment_length = compute_avg_comment_length(bug)
    clarification_request_count = compute_clarification_request_count(bug)
    num_comments = compute_num_comments(bug)
    num_participants = compute_num_participants(bug)

    return{
        "num_comments": compute_num_comments(bug),
        "num_participants": compute_num_participants(bug),
        "avg_comment_lenght": avg_comment_length,
        "discussion_intensity": compute_discussion_intensity(num_comments, num_participants),
        "discussion_description_ratio": compute_discussion_description_ratio(bug, description_length),
        "clarification_request_count": clarification_request_count,
        "clarification_burden": compute_clarification_burden(clarification_request_count, num_comments),
        "coordination_complexity": compute_coordination_complexity(num_participants, num_comments, avg_comment_length),
        "has_cannot_reproduce": compute_has_cannot_reproduce(bug)
    }