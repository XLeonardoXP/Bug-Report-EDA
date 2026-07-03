import re
import nltk
nltk.download('cmudict')
from nltk.corpus import cmudict



def remove_stacktraces(text):
    """
    Rimuove stacktrace di Python, Java, JavaScript, C#, PHP, Ruby
    inclusi stacktrace Java compressi e multilinea.
    """

    STACKTRACE_LINE_PATTERNS = [
        re.compile(r"^\s*at\s+[\w.$]+\((?:[\w.$]+(?::\d+)?|Native Method|Unknown Source)\)\s*$"),
        re.compile(r"^\s*Caused by:\s+[\w.$]+(?::\s*.*)?\s*$"),
        re.compile(r"^\s*\.\.\.\s+\d+\s+(more|common frames omitted)\s*$"),
        re.compile(r'^\s*File\s+"[^"]+",\s+line\s+\d+,\s+in\s+\S+\s*$'),
        re.compile(r"^\s*at\s+(?:[\w.$<>]+\s+)?\(?[\w./$:-]+(?::\d+){1,2}\)?\s*$"),
        re.compile(r"^\s*at\s+[\w.<>]+\(.*?\)(?:\s+in\s+.+:\s*line\s+\d+)?\s*$"),
        re.compile(r"^\s*#\d+\s+.+\(\d+\):\s+.+\s*$"),
        re.compile(r"^\s*#\d+\s+\{main\}\s*$"),
        re.compile(r"^\s*from\s+.+\.rb:\d+:in\s+`.+'\s*$"),
    ]

    STACKTRACE_HEADER_PATTERNS = [
        re.compile(r"^\s*[\w.$]+(?:Exception|Error|Throwable):\s*.*$"),
        re.compile(r"^\s*(?:java|javax|org|com|sun|net)\.[.\w$]+(?:Exception|Error)\s*$"),
        re.compile(r"^\s*Traceback \(most recent call last\):\s*$"),
        re.compile(r"^\s*(?:TypeError|ReferenceError|SyntaxError|RangeError|URIError|EvalError):\s+.+$"),
        re.compile(r"^\s*System\.[\w.]+(?:Exception|Error):\s*.+$"),
        re.compile(r"^\s*(?:Fatal error|Warning|Notice|Parse error):\s+.+\s+in\s+.+\s+on\s+line\s+\d+\s*$"),
        re.compile(r"^\s*.+\.rb:\d+:in\s+`.+':\s+.+\(.+\)\s*$"),
    ]

    lines = text.splitlines()
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if any(p.match(line) for p in STACKTRACE_LINE_PATTERNS):
            i += 1
            continue

        if any(p.match(line) for p in STACKTRACE_HEADER_PATTERNS):
            lookahead = lines[i + 1] if i + 1 < len(lines) else ""
            if any(p.match(lookahead) for p in STACKTRACE_LINE_PATTERNS + STACKTRACE_HEADER_PATTERNS):
                i += 1
                continue

        result.append(line)
        i += 1

    cleaned = "\n".join(result)

    # Java stacktrace compressi su una sola riga
    cleaned = re.sub(
        r"[\w.$]+(?:Exception|Error|Throwable)[^:\n]*(?::\s*[^\n]*)?\s+(?:at\s+[\w.$]+\([^)]+\)\s*)+",
        "",
        cleaned
    )

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def remove_java_code_blocks(text):
    """Rimuove blocchi di codice Java dalla stringa, inclusi quelli con try-catch-finally."""
    start_patterns = [
        r'public\s+static\s+void',
        r'public\s+class',
        r'private\s+',
        r'protected\s+',
        r'for\s*\(',
        r'while\s*\(',
        r'if\s*\(',
        r'try\s*\{'
    ]

    combined = re.compile('|'.join(start_patterns))

    while True:
        match = combined.search(text)
        if not match:
            break

        start = match.start()
        brace_start = text.find('{', start)
        if brace_start == -1:
            break

        depth = 0
        end = brace_start

        # parsing blocco principale
        while end < len(text):

            if text[end] == '{':
                depth += 1
            elif text[end] == '}':
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1

        # include eventuali catch/finally
        while True:
            remaining = text[end:]
            catch_match = re.match(
                r'\s*(catch\s*\([^\)]*\)\s*\{|finally\s*\{)',
                remaining
            )
            if not catch_match:
                break
            # trova {
            brace_pos = text.find('{', end)

            if brace_pos == -1:
                break

            depth = 0
            temp_end = brace_pos

            while temp_end < len(text):

                if text[temp_end] == '{':
                    depth += 1

                elif text[temp_end] == '}':
                    depth -= 1

                    if depth == 0:
                        temp_end += 1
                        break

                temp_end += 1

            end = temp_end

        #
        # rimuove tutto il costrutto
        #
        text = text[:start] + ' ' + text[end:]

    return text


def clean_text(text):
    if not text:
        return ""
    # stacktrace
    text = remove_stacktraces(text)
    # code blocks
    text = remove_java_code_blocks(text)
    # package Java
    text = re.sub(
        r'\b(?:[a-z_]+\.){2,}[A-Za-z_][\w]*\b',
        ' ',
        text
    )
    # rimuove pattern di classi con :: (es. ReplaceWithTeamStream::getEditionToLoad)
    text = re.sub(
        r'\b[A-Za-z_]\w*::[A-Za-z_]\w*\([^)]*\)',
        ' ',
        text
    )
    # rimuove chiamate a metodi residui o assegnazioni (es. getRemoteResource())
    text = re.sub(
        r'\b[A-Za-z_]\w*\([^)]*\)',
        ' ',
        text
    )
    # timestamp COMPLETO compreso AM/PM
    text = re.sub(
        r'\(?\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)\)?',
        ' ',
        text,
        flags=re.IGNORECASE
    )
    # versioni
    text = re.sub(
        r'\bv?\d+(?:\.\d+)+\b',
        ' ',
        text
    )
    # normalizzazione
    text = re.sub(r'\s+', ' ', text) 

    return text.strip()



d = cmudict.dict()

def normalize_word(word):
    # rimuove punteggiatura iniziale/finale
    return re.sub(r"^[^\w]+|[^\w]+$", "", word)

def count_syllables_word(word):
    # normalizza prima
    word = normalize_word(word)

    # gestisci sigle (API, VCM, KM)
    if word.isupper() and len(word) <= 5:
        return len(word)  # ogni lettera = 1 sillaba

    word = word.lower()

    if word in d:
        # ogni vocale fonetica contiene un numero (es. AH0, EH1)
        return [sum(1 for phoneme in pron if phoneme[-1].isdigit()) for pron in d[word]][0]
    else:
        # fallback: euristica
        return heuristic_syllable_count(word)

def heuristic_syllable_count(word):
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_vowel = False

    for char in word:
        if char in vowels:
            if not prev_vowel:
                count += 1
            prev_vowel = True
        else:
            prev_vowel = False

    # parole che finiscono con "e" muta
    if word.endswith("e") and count > 1:
        count -= 1

    return max(1, count)

def count_syllables(word):
    return count_syllables_word(word)
