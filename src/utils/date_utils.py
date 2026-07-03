from datetime import datetime

def parse_bug_date(date_str):
    """
    Converte la stringa data del JSON in un oggetto datetime.
    Gestisce il formato: "2001-10-10 21:34:00 -0400"
    """
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        # Il formato %z legge l'offset numerico come -0400
        # Puliamo la stringa da eventuali suffissi testuali come 'EDT' se presenti
        clean_date = date_str.split(" (")[0].strip()
        # Se la stringa contiene nomi di zone (es. EDT), le rimuoviamo per il parsing
        # Un metodo robusto è prendere solo i primi 3 blocchi + l'offset
        parts = clean_date.split()
        if len(parts) >= 3:
            date_to_parse = f"{parts[0]} {parts[1]} {parts[2]}"
            return datetime.strptime(date_to_parse, "%Y-%m-%d %H:%M:%S %z")
        return None
    except Exception:
        return None
    
def get_comment_gaps(bug, parse_func):
    """
    Estrae i commenti, pulisce le date e restituisce la lista dei gap in giorni.
    """
    comments = bug.get("long_desc", [])[1:]
    
    # Estrazione e parsing delle date usando la funzione passata come argomento
    dates = [parse_func(c.get("bug_when")) for c in comments]
    dates = [d for d in dates if d is not None]
    
    # Ordinamento per gestire qualsiasi ordine nel JSON (oldest/newest)
    dates.sort()

    # Servono almeno due date valide per calcolare almeno un intervallo
    if len(dates) < 2:
        return []

    # Calcolo dei gap in giorni (assicurandoci che non siano negativi)
    return [max(0, (dates[i+1] - dates[i]).total_seconds() / 86400) for i in range(len(dates)-1)]