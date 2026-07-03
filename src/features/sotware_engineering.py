import math
import re
from src.utils.text_utils import clean_text
from src.utils.text_utils import remove_stacktraces
from src.utils.text_utils import remove_java_code_blocks

def compute_num_stacktrace_lines(bug):
    comments = bug.get("long_desc", [])
    if not comments:
        return 0

    full_text = " ".join(
        c.get("thetext", "") for c in comments
    )
    if not full_text:
        return 0

    patterns = [
        r'at\s+[\w\.\$]+(?:<\w+>)?[\w\.\$]*\s*\([^\)]*\)',   # Java / C#
        r'File\s+"[^"]+",\s+line\s+\d+',            # Python
        r'#\d+\s+0x[0-9a-fA-F]+',                   # C++ gdb
        r'[\w\$][\w\.\$]*@(?:https?://|chrome)',     # JS Browser
    ]

    combined = re.compile('|'.join(patterns))
    matches = combined.findall(full_text)
    return len(matches)


def compute_has_code_blocks(bug):
    """
    Restituisce 1 se nella descrizione iniziale è presente almeno 
    un blocco di codice, altrimenti 0.
    """
    comments = bug.get("long_desc", [])
    if not comments: 
        return 0
    
    text = comments[0].get("thetext", "")
    if not text: 
        return 0

    # 1. Pulizia preventiva dei log di performance (evita falsi positivi)
    text = re.sub(r'\(?\d+\)?\s*\d+(\.\d+)?%', '', text)
    text = re.sub(r'\d+\s*ms', '', text)

    # 2. Pattern per identificare la presenza di codice
    patterns = [
        r'\b(?:public|private|static|final|void)\s+\w+\s*\(.*?\)\s*\{', # Metodi
        r'\{[\s\S]*?\}',                                               # Blocchi graffe
        r'\b\w+\s+\w+\s*=\s*new\s+\w+\(.*?\);',                        # Instanziazioni
        r'```[\s\S]*?```'                                              # Markdown
    ]
    
    combined_pattern = re.compile('|'.join(patterns))

    # Cerchiamo se esiste almeno un match
    if combined_pattern.search(text):
        return 1
    
    return 0
    
def compute_num_issue_references(bug):
    """
    Feature num_issue_references
    Conta il numero totale di riferimenti a bug, PR o issue presenti nella descrizione iniziale e nei commenti del bug report.
    """

    short_desc = bug.get("short_desc", "")
    comments = bug.get("long_desc", [])
    long_desc = " ".join(c.get("thetext", "") for c in comments)
    full_text = f"{short_desc}\n{long_desc}"

    # Pattern per "bug 12345", "bug#12345", "bugid 12345"
    pattern_bug = r"bug[\s\xa0]*(?:#|id|issue)?[\s\xa0]*\d+"
    # Pattern per PR: "pr 12345", "pr#12345", "prid 12345"
    pattern_pr = r"pr[\s\xa0]*(?:#|id|issue)?[\s\xa0]*\d+"
    # Pattern per vecchi ID legacy: 7 caratteri alfanumerici che iniziano con un numero (es. "1abcde2")
    pattern_legacy = r"\b[1-9][a-z0-9]{6}\b"
    pattern_pr_distante = r"\bpr\b(?:\s+\w+){0,10}\s+\d[a-z]{3}\d[a-z0-9]{2}\b"

    combined_pattern = (
        f"{pattern_pr_distante}|{pattern_bug}|{pattern_pr}|{pattern_legacy}"
    )

    matches = re.findall(combined_pattern, full_text, flags=re.IGNORECASE)
    return len(set(matches))


def compute_num_urls(bug):
    """
    Calcola il numero di URL unici presenti
    nei commenti del bug report.

    Cerca URL che iniziano con:
    - http://
    - https://
    - www.
    """
    # Set usato per salvare URL unici
    unique_urls = set()

    long_desc = bug.get("long_desc", [])
    # Regex per trovare URL
    url_pattern = r'(?:https?://|www\.)[^\s]+'

    for comment in long_desc:
        text = comment.get("thetext", "")
        if text:
            # Cerca tutti gli URL nel testo
            found_urls = re.findall(url_pattern, text)
            # rimuove eventuali punti finali
            cleaned_urls = [
                url.rstrip('.')
                for url in found_urls
            ]
            # Aggiunge gli URL al set
            unique_urls.update(cleaned_urls)
    return len(unique_urls)


def compute_num_file_paths(bug: dict) -> int:
    """
    Conta i percorsi ai file unici trovati in short_desc e long_desc,
    dopo aver rimosso gli stacktrace.
    """

    KNOWN_EXTENSIONS_RE = (
        r"java|py|pyc|rb|php|js|ts|jsx|tsx"
        r"|c|cpp|cc|cxx|h|hpp|cs|go|rs|swift|kt"
        r"|xml|json|yaml|yml|toml|ini|cfg|conf"
        r"|html|htm|css|scss|less"
        r"|sh|bash|zsh|bat|cmd|ps1"
        r"|txt|log|md|rst|csv"
        r"|jar|war|ear|class"
        r"|so|dll|dylib|exe"
        r"|gradle|pom|mk|cmake"
    )

    # Estensioni corte e ambigue da escludere se usate come "file nudo"
    # (es. "Fixed." matcha .d, "server." matcha .rs, "model." matcha .el ecc.)
    # Le escludiamo dal pattern "file nudo" lasciandole solo per path con slash
    SAFE_EXTENSIONS_RE = (
        r"java|pyc|php|jsx|tsx"
        r"|cpp|cxx|hpp|swift"
        r"|xml|json|yaml|yml|toml|conf"
        r"|html|htm|scss|less"
        r"|bash|zsh|cmd|ps1"
        r"|txt|log|rst|csv"
        r"|jar|war|ear|class"
        r"|dll|dylib|exe"
        r"|gradle|cmake"
    )

    PATTERNS = [
        # Unix/Linux/macOS assoluto: /path/to/file
        re.compile(r"(?<![:\w])/(?:[\w.\-]+/)*[\w.\-]+(?:\.(?:" + KNOWN_EXTENSIONS_RE + r"))?(?![:\w])"),

        # Windows assoluto backslash: C:\Users\john\file.txt
        re.compile(r"[A-Za-z]:\\(?:[\w.\- ]+\\)*[\w.\- ]+(?:\.(?:" + KNOWN_EXTENSIONS_RE + r"))?(?![\w])"),

        # Windows assoluto forward slash: C:/Users/john/file.txt
        re.compile(r"[A-Za-z]:/(?:[\w.\-]+/)*[\w.\-]+(?:\.(?:" + KNOWN_EXTENSIONS_RE + r"))?(?![\w])"),

        # Windows UNC: \\server\share\file.txt
        re.compile(r"\\\\[\w.\-]+(?:\\[\w.\- ]+)+(?:\.(?:" + KNOWN_EXTENSIONS_RE + r"))?(?![\w])"),

        # Percorsi relativi espliciti: ./foo/bar.xml  ../src/Foo.java
        re.compile(r"\.\.?/(?:[\w.\-]+/)*[\w.\-]+\.(?:" + KNOWN_EXTENSIONS_RE + r")(?![\w])"),

        # File nudi: Foo.java, config.xml
        # Usa SAFE_EXTENSIONS_RE (no estensioni corte ambigue come .c .h .go .md .rs .so .py .rb .js .ts .sh .ini .cfg .pom .mk)
        re.compile(r"(?<![.\w])[\w.\-]+\.(?:" + SAFE_EXTENSIONS_RE + r")(?!\w)"),
    ]

    # Estrazione testo difensiva
    bug_data = bug.get("bug", bug)

    short_desc = bug_data.get("short_desc", "")
    if isinstance(short_desc, dict):
        short_desc = ""

    comments = bug_data.get("long_desc", [])
    if isinstance(comments, dict):
        comments = [comments] if comments else []
    elif not isinstance(comments, list):
        comments = []

    long_desc = " ".join(
        c.get("thetext", "") for c in comments
        if isinstance(c, dict)
    )

    full_text = f"{short_desc}\n{long_desc}".strip()
    if not full_text:
        return 0

    cleaned_text = remove_stacktraces(full_text)
    cleaned_text = re.sub(r"https?://\S+|ftp://\S+", "", cleaned_text)

    found_paths: set[str] = set()
    for pattern in PATTERNS:
        for match in pattern.finditer(cleaned_text):
            path = match.group(0).strip()
            # Filtra package Java/comuni
            if re.match(r"^(?:java|javax|org|com|sun|net|io|eclipse)\.", path):
                continue
            # Filtra path troppo corti
            if len(path) < 5:
                continue
            found_paths.add(path)
    return len(found_paths)



def compute_num_function_mentions(bug):
    """
    Conta il numero di riferimenti
    a funzioni/metodi nel titolo, descrizione iniziale e commenti.
    """

    # Pattern regex per catturare nomi di funzioni/metodi seguiti da parentesi vuote ()
    # Supporta anche chiamate concatenate come resource.getName() o e.getStatus()
    function_pattern = re.compile(
        r'\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*\(\s*\)',
        re.MULTILINE
    )
    
    #  estrae il sotto-oggetto "bug"
    bug_data = bug.get("bug", bug)
    
    parts = []

    # Aggiunge la descrizione breve del bug
    short_desc = bug_data.get("short_desc", "")
    if short_desc:
        parts.append(short_desc)
    
    # Estrae il testo da tutti i commenti
    long_desc = bug_data.get("long_desc", [])
    if isinstance(long_desc, list):
        # Caso normale: long_desc è una lista di commenti
        for comment in long_desc:
            parts.append(comment.get("thetext", ""))
    elif isinstance(long_desc, dict):
        # Caso in cui c'è un solo commento (non lista)
        parts.append(long_desc.get("thetext", ""))
    
    # Unisce tutti i testi estratti
    raw_text = "\n\n".join(parts)

    # Rimuove eventuali stacktrace dal testo
    clean_text = remove_stacktraces(raw_text)
    
    # Restituisce il numero di funzioni/metodi trovati
    return len(function_pattern.findall(clean_text))

def compute_has_version_mentions(bug):
    """
    Conta il numero di volte  che nel testo del bug viene menzionata una versione
    es. v205, v1.0
    """

    version_pattern = re.compile(
        r'(?<![A-Za-z])(?<!IVCMEvent\s)(?<!IVCMListener\s)(?<!IVCMProvider\s)\b(v\d+[a-z]?(\.\d+)*|\d+(\.\d+)+[a-z]?|M\d+)\b',
        re.MULTILINE
    )

    bug_data = bug.get("bug", bug)

    parts = []

    # Aggiunge la descrizione breve del bug
    short_desc = bug_data.get("short_desc", "")
    if short_desc:
        parts.append(short_desc)

    # Estrae il testo da tutti i commenti
    long_desc = bug_data.get("long_desc", [])
    if isinstance(long_desc, list):
        # Caso normale: long_desc è una lista di commenti
        for comment in long_desc:
            parts.append(comment.get("thetext", ""))
    elif isinstance(long_desc, dict):
        # Caso in cui c'è un solo commento (non lista)
        parts.append(long_desc.get("thetext", ""))

    # Unisce tutti i testi estratti
    raw_text = "\n\n".join(parts)

    clean_text = remove_stacktraces(raw_text)

    # Rimuove righe con riferimenti interni tipo >IVCMEvent 0.4 000
    clean_text = re.sub(r'>IVCM\w+.*$', '', clean_text, flags=re.MULTILINE)

    return 1 if version_pattern.search(clean_text) else 0

def compute_num_attachments(bug):
    """
    Conta il numero di allegati nel bug report.
    Un commento ha un allegato se contiene il campo 'attachid'.
    """
    bug_data = bug.get("bug", bug)

    comments = bug_data.get("long_desc", [])
    if isinstance(comments, dict):
        comments = [comments] if comments else []
    elif not isinstance(comments, list):
        comments = []

    return sum(
        1 for c in comments
        if isinstance(c, dict) and c.get("attachid")
    )


def compute_num_reopenings(bug):
    """
    Feature num_reopenings
    Conta le riaperture del bug basandosi sui commenti che iniziano
    con varianti di reopen/reopened/reopening nei bug report Eclipse/Bugzilla.
    """
    bug_data = bug.get("bug", bug)

    comments = bug_data.get("long_desc", [])
    if isinstance(comments, dict):
        comments = [comments] if comments else []
    elif not isinstance(comments, list):
        comments = []

    # Matcha tutte le varianti viste nel dataset:
    # reopen, re-open, reopened, re-opened, reopening, re-opening,
    # reopenned, reopenning, re-openning, reopeneing, re-openeing ecc.
    # Seguite da: fine stringa, punto, spazio+qualsiasi cosa
    REOPEN_PATTERN = re.compile(
        r"^re-?open(n?ed|n?ing|n?eing|ed|\+\+)?(\.|\s.*)?$",
        re.IGNORECASE
    )

    # Falsi positivi: "reopen" riferito a oggetti tecnici, non al bug
    TECHNICAL_CONTEXT = re.compile(
        r"^re-?open\s+(editor|file|view|dialog|wizard|tab|window|"
        r"perspective|project|folder|resource|the\s+editor|the\s+file|"
        r"the\s+view|the\s+dialog|the\s+window)",
        re.IGNORECASE
    )

    count = 0
    # Salta il primo commento (descrizione iniziale del bug)
    for comment in comments[1:]:
        if not isinstance(comment, dict):
            continue
        text = comment.get("thetext", "").strip()
        if not text:
            continue
        first_line = text.splitlines()[0].strip()

        if REOPEN_PATTERN.match(first_line) and not TECHNICAL_CONTEXT.match(first_line):
            count += 1

    return count

def compute_step_to_reproduce(bug):
    """
    Feature: has_steps_to_reproduce
    Restituisce 1 se nel testo del bug report è presente una sezione 
    con i passi di riproducibilità o un elenco numerato (es. 1. First step).
    Restituisce 0 altrimenti.
    """

    # Pattern regex migliorato
    steps_pattern = re.compile(
        r'''
        (?:
            # Intestazioni esplicite comuni
            (?:steps?\s+to\s+(?:reproduce|recreate)(?:\s+the\s+problem)?|
               to\s+reproduce|
               how\s+(?:to|i)\s+reproduce|
               reproduce\s+steps|
               what\s+steps\s+will\s+reproduce|
               ^\s*steps\s*)
            \s*[:\?\-]?
        |
            # Elenco numerato con punto o parentesi a inizio riga
            ^\s*[1-9][0-9]?[.)]\s+[A-Za-z]
        )
        ''',
        re.IGNORECASE | re.MULTILINE | re.VERBOSE
    )
    
    bug_data = bug.get("bug", bug)
    parts = []

    # Aggiunge la descrizione breve del bug
    short_desc = bug_data.get("short_desc", "")
    if short_desc:
        parts.append(short_desc)

    # Estrae il testo da tutti i commenti
    long_desc = bug_data.get("long_desc", [])
    if isinstance(long_desc, list):
        for comment in long_desc:
            parts.append(comment.get("thetext", ""))
    elif isinstance(long_desc, dict):
        parts.append(long_desc.get("thetext", ""))

    raw_text = "\n\n".join(parts)

    # --- FASE DI PRE-PROCESSAMENTO DEL TESTO ---
    
    # Rimuove gli stacktrace per evitare falsi positivi con i numeri di riga
    clean_text = remove_stacktraces(raw_text)

    # Normalizza spazi multipli riducendoli a UN SINGOLO SPAZIO (più sicuro del \n)
    clean_text = re.sub(r' {2,}', ' ', clean_text)

    # MANDA A CAPO i numeri di step scritti "inline" sulla stessa riga
    # Es: "Steps: 1. Do this 2. Do that" -> diventa multiriga
    clean_text = re.sub(r'(?<!\n)\s+(\d+[.)]\s)', r'\n\1', clean_text)

    return 1 if steps_pattern.search(clean_text) else 0


def compute_has_patch(bug):
    """
    Feature: has_patch
    Restituisce 1 se nei commenti del bug report è presente almeno un allegato con patch
    """
    bug_data = bug.get("bug", bug)
    comments = bug_data.get("long_desc", [])

    # Gestione sicura del formato: se è un singolo dict, trasformalo in lista
    if isinstance(comments, dict):
        comments = [comments]
    # Parole chiave
    patch_keywords = ["patch", "proposed fix", "diff", "pull request", "pr"]
    # Falsi positivi
    false_positives = ["screenshot", "png", "jpg", "jpeg", "gif", "log", "stacktrace", "txt", "dump", "exception"]

    for comment in comments:
        if "attachid" in comment:
            text = comment.get("thetext", "")
            match = re.search(r"Created attachment \d+(?:\s+\[details\])?\s+(.*)", text, re.IGNORECASE)

            if match:
                attachment_description = match.group(1).lower()
                has_patch_keyword = any(kw in attachment_description for kw in patch_keywords)
                has_false_positive = any(fp in attachment_description for fp in false_positives)

                if has_patch_keyword and not has_false_positive:
                    return 1 

    return 0 

def compute_severity_score(bug):
    """
    Converte il campo testuale bug_severity in un valore numerico ordinale che rappresenta la gravità del bug.
    """
    # Prendiamo direttamente la severity dall'oggetto passato
    severity = bug.get("bug_severity", "").lower().strip()
    
    severity_map = {
        "blocker": 7,
        "critical": 6, 
        "major": 5,
        "normal": 4, 
        "minor": 3,
        "trivial": 2, 
        "enhancement": 1
    }
    
    return severity_map.get(severity, 0)


def compute_priority_score(bug):
    """
    Feature: priority_score
    Mapping: P1=5, P2=4, P3=3, P4=2, P5=1, Altro=0
    """
    # Prova a cercare in bug['bug']['priority'] (struttura annidata)
    # Se fallisce, cerca direttamente in bug['priority'] (struttura piatta)
    priority_str = bug.get("bug", {}).get("priority") or bug.get("priority")

    # Mapping della priorità
    priority_map = {
        "P1": 5,
        "P2": 4,
        "P3": 3,
        "P4": 2,
        "P5": 1,
    }
    
    # .get() restituisce il valore se esiste, altrimenti il secondo argomento (0)
    return priority_map.get(priority_str, 0)

def compute_reporter_experience(bug, reporter_history):
    """
    Numero di bug aperti in precedenza
    dallo stesso reporter.
    """

    reporter = bug.get("reporter")

    if reporter is None:
        return 0

    # esperienza PRIMA del bug corrente
    experience = reporter_history.get(reporter, 0)

    # aggiorna storico
    reporter_history[reporter] = experience + 1

    return experience

def compute_has_error_message(bug):
    """
    Feature: has_error_message
    Restituisce 1 se nel bug report è presente un messaggio di errore
    Eccezioni Java/Python/JS/C# nella forma NomeEccezione: messaggio
    Log strutturati tipo ERROR: ..., FATAL: ...
    Segfault, core dumped, access violation
    """

    ERROR_MESSAGE_PATTERN = re.compile(
        r"(?:"
        r"\b[A-Z][A-Za-z0-9]*(?:Exception|Error|Throwable|Fault|Failure)\s*:\s*\S+"
        r"|"
        r"\b(?:ERROR|FATAL|CRITICAL|SEVERE|WARN(?:ING)?)\s*[:\|]\s*\S+"
        r"|"
        r"\b(?:fatal\s+)?(?:parse\s+)?error\s*:\s*\S+"
        r"|"
        r"\b(?:fatal\s+error|warning|notice|parse\s+error)\s*:\s*.+\s+in\s+.+\s+on\s+line\s+\d+"
        r"|"
        r"\b(?:access\s+violation|segmentation\s+fault|core\s+dumped|bus\s+error)\b"
        r"|"
        r"\bpanic\s*:\s*\S+"
        r"|"
        r"\bthread\s+'.+'\s+panicked\s+at\b"
        r")",
        re.IGNORECASE
    )

    try:
        bug_data = bug.get("bug", bug)
        long_desc = bug_data.get("long_desc", [])

        for index, comment in enumerate(long_desc):
            text = comment.get("thetext", "")
            matches = ERROR_MESSAGE_PATTERN.findall(text)

            if matches:
                return 1

        return 0

    except Exception as e:
        print(f"[ERROR] Bug {bug_data.get('bug_id', '?')}: {e}")
        return 0
    


def compute_has_actual_behaviour(bug):
    """
    È una feature binaria (0/1) che rileva se nella
    descrizione iniziale il reporter ha descritto cosa 
    succede realmente quando si manifesta il bug
    (es. actual, observed)
    """

    bug_content = bug.get("bug", bug) 
    long_desc_list = bug_content.get("long_desc", [])
    first_comment = long_desc_list[0]
    raw_text = first_comment.get("thetext", "").lower()
    text = clean_text(raw_text)

    actual_patterns = re.compile(
        r'\b(actual\w*|observ\w*|instead|what happens|'
        r'what occurred|result is|currently|'
        r'but it|however it|it does not|it doesn\'t|'
        r'fails to|failure|wrong|incorrect|unexpected)\b',
        re.IGNORECASE
    )

    if actual_patterns.search(text):
        return 1
    
    return 0

def compute_has_expected_behaviour(bug):
    """
    Feature: has_expected_behaviour
    Restituisce 1 se nella descrizione sono presenti indicatori 
    di comportamento atteso (es. "should", "expected", "instead of").
    """
    bug_content = bug.get("bug", bug) 
    long_desc_list = bug_content.get("long_desc", [])
    first_comment = long_desc_list[0]
    raw_text = first_comment.get("thetext", "").lower()
    text = clean_text(raw_text)
   
    expected_patterns = [
        r"expected", 
        r"should be", 
        r"should have",
        r"instead of", 
        r"rather than",
        r"supposed to",
        r"fix is to",
        r"correct behavior",
    ]
    combined_pattern = re.compile("|".join(expected_patterns))
    
    if combined_pattern.search(text):
        return 1
    
    return 0


def compute_has_assignee(bug):
    """
    Controlla se il bug è stato assegnato ad un reporter.
    Ritorna 1 se il bug ha un assegnatario reale, 0 altrimenti.
    Controlla il campo 'assigned_to'.
    """
    # Recupera il valore del campo assigned_to
    assigned_to = bug.get("assigned_to", "")

    # Verifica che non sia vuoto
    # e che non contenga solo spazi
    if assigned_to and assigned_to.strip():
        return 1

    return 0
    
def compute_same_reporter_assignee(bug):
    """
    Feature: same_reporter_assignee
    Restituisce 1 se il reporter e l'assegnatario (assigned_to) sono la stessa persona,
    altrimenti 0.
    """
    data = bug.get("bug", bug)
    
    reporter = data.get("reporter")
    assignee = data.get("assigned_to")

    # Debug rapido: se vuoi vedere cosa vede il computer, scommenta la riga sotto
    # print(f"DEBUG: '{reporter}' vs '{assignee}'")

    if not reporter or not assignee:
        return 0

    # Usiamo strip() per eliminare eventuali spazi invisibili dovuti al parsing
    if str(reporter).strip() == str(assignee).strip():
        return 1
    
    return 0

def compute_technical_complexity(num_stacktrace_lines, has_code_blocks, num_file_paths, num_function_mentions, has_error_message, severity_score, has_version_mentions):
    """
    Feature: technical_complexity
    Calcola la complessità tecnica del bug in base alle caratteristiche estratte.
    """
    alpha = 1.5  # Forte impatto logaritmico per lo stacktrace
    beta  = 1.0  # Peso per elementi strutturali contabili (file, funzioni)
    gamma = 0.5  # Peso per la gravità del bug (severity)
    
    # Nuovi pesi per i flag binari
    w_code = 1.2   # Un blocco di codice è un forte indicatore tecnico
    w_error = 1.0  # Un messaggio d'errore stringato ha un buon valore
    w_version = 0.3 # La versione è utile, ma non deve pesare quanto il codice
    
    technical_complexity = (
        alpha * math.log1p(num_stacktrace_lines)   
        + beta * (num_file_paths + num_function_mentions)
        + gamma * severity_score
        + (w_code * has_code_blocks)
        + (w_error * has_error_message)
        + (w_version * has_version_mentions)
    )
    return technical_complexity

def compute_technical_density(bug):
    """
    Calcola la densità tecnica del testo del bug report.
    Formula: token_tecnici / token_totali
    
    Ottimizzata per evitare falsi positivi su testi brevi contenenti
    acronimi ricorrenti o parole di formattazione in UPPERCASE.
    """
    bug_data = bug.get("bug", bug)
    parts = []

    # 1. Estrazione del testo dal titolo (short_desc) e dai commenti (long_desc)
    short_desc = bug_data.get("short_desc", "")
    if short_desc:
        parts.append(short_desc)

    long_desc = bug_data.get("long_desc", [])
    if isinstance(long_desc, list):
        for comment in long_desc:
            parts.append(comment.get("thetext", ""))
    elif isinstance(long_desc, dict):
        parts.append(long_desc.get("thetext", ""))

    raw_text = "\n\n".join(parts)

    # 2. Tokenizzazione basata sugli spazi (preserva package e path completi)
    raw_tokens = re.findall(r'\S+', raw_text)

    if not raw_tokens:
        return 0.0

    num_total = len(raw_tokens)

    # 3. Compilazione dei pattern tecnici (Raffinati e restrittivi)
    technical_patterns = re.compile(
        r'^('
        r'[a-z]+[A-Z][a-zA-Z0-9]*'                        # camelCase
        r'|'
        r'[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+'                 # PascalCase (es. VCMDiffTreeViewer)
        r'|'
        r'[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)+'             # snake_case
        r'|'
        r'I[A-Z][A-Za-z0-9]+'                             # Interfacce con prefisso I (es. IVCMEvent)
        r'|'
        r'[A-Z][A-Za-z0-9]*(?:Exception|Error|Throwable)'   # Eccezioni e Errori (es. ClassCastException)
        r'|'
        r'[A-Z]{4,}(?:_[A-Z0-9]+)*'                       # Costanti vere (minimo 4 lettere o UPPER_SNAKE)
        r'|'
        r'@[A-Z][a-zA-Z]+'                               # Annotazioni
        r'|'
        r'[A-Za-z_]\w*::[A-Za-z_]\w*'                     # Operatore di scope ::
        r'|'
        r'(?:[a-zA-Z0-9_]+\.)+[a-zA-Z0-9_]+(?:\$[0-9]+)?' # Package/Classi Java (es. org.eclipse.ui.internal)
        r'|'
        r'[a-zA-Z0-9_\-]+\.(?:java|cpp|h|py|c|js|ts|class)\:[0-9]+' # File:Linea degli stacktrace
        r')$'
    )

    # 4. Blacklist per escludere acronimi e parole di testo comune in maiuscolo
    UPPERCASE_BLACKLIST = {
        "VCM", "API", "UI", "TS", "IP", "PR", "ID", 
        "NOTES", "PRODUCT", "VERSION", "YES", "NO", 
        "AM", "PM", "FIXED", "BUG"
    }

    num_technical = 0

    # 5. Ciclo di conteggio con pulizia della punteggiatura di contorno
    for token in raw_tokens:
        # Rimuove la punteggiatura solo dall'inizio e dalla fine del token
        # Esempio: "(IVCMEvent)." diventa "IVCMEvent"
        clean_token = token.strip('.,;:!?()[]{}""\'`<>*')
        
        # Ignora i token vuoti dopo la pulizia
        if not clean_token:
            continue
            
        # Salta i token presenti nella blacklist degli acronimi/prosa
        if clean_token.upper() in UPPERCASE_BLACKLIST:
            continue
            
        # Verifica se il token pulito risponde a uno dei pattern tecnici
        if technical_patterns.match(clean_token):
            num_technical += 1

    return num_technical / num_total

def extract_software_engineering_features(bug, reporter_history):
    num_stacktrace_lines = compute_num_stacktrace_lines(bug)
    has_code_blocks = compute_has_code_blocks(bug)
    has_error_message = compute_has_error_message(bug)
    num_function_mentions = compute_num_function_mentions(bug)
    severity_score = compute_severity_score(bug)
    num_file_paths = compute_num_file_paths(bug)
    has_version_mentions = compute_has_version_mentions(bug)

    return {
        "num_stacktrace_lines": num_stacktrace_lines,
        "has_code_blocks": has_code_blocks,
        "num_issue_references": compute_num_issue_references(bug),
        "num_urls": compute_num_urls(bug),
        "num_file_paths": num_file_paths,
        "num_function_mentions": num_function_mentions,
        "has_version_mentions": has_version_mentions,
        "num_attachments": compute_num_attachments(bug),
        "num_reopenings": compute_num_reopenings(bug),
        "has_step_to_reproduce":compute_step_to_reproduce(bug),
        "has_patch": compute_has_patch(bug),
        "has_error_message": has_error_message,
        "has_actual_behaviour": compute_has_actual_behaviour(bug),
        "has_expeted_behaviour": compute_has_expected_behaviour(bug),
        "has_assignee": compute_has_assignee(bug),
        "same_reporter_assignee": compute_same_reporter_assignee(bug),
        "severity_score": severity_score,
        "priority_score": compute_priority_score(bug),
        "reporter_experience": compute_reporter_experience(bug, reporter_history),
        "techical_complexity": compute_technical_complexity(num_stacktrace_lines, has_code_blocks, num_file_paths, num_function_mentions, has_error_message, severity_score, has_version_mentions),
        "technical_density": compute_technical_density(bug),
    }