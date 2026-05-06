import json
import time


def process_bug_report(filepath):
    total_bugs = 0
    start_time = time.time()  # Segna l'ora di inizio
    severity_counts = {}
    
    with open(filepath, 'rb') as f:
        
        for row, row_byte in enumerate(f, 1):

            # Salta eventuali righe vuote nel json
            if not row_byte.strip():
                continue

            try:
                # Decodifica la riga in UTF-8 perchè è stata letta in modalità binaria
                row_text = row_byte.decode("utf-8")

                # Carichiamo le righe del JSON
                row_data = json.loads(row_text)

                if 'bug' in row_data:
                    total_bugs += 1
                    
                    # Estraiamo la severity. 
                    # Usiamo .get() per sicurezza se il campo mancasse
                    bug_info = row_data.get('bug', {})
                    sev = bug_info.get('bug_severity', 'Unknown')

                    # Aggiorniamo il contatore nel dizionario
                    if sev in severity_counts:
                        severity_counts[sev] += 1
                    else:
                        severity_counts[sev] = 1
                        
            except UnicodeDecodeError:
                print(f"Errore di codifica alla riga {row}")
            except json.JSONDecodeError:
                print(f"Errore JSON alla riga {row}")

    end_time = time.time()    # Segna l'ora di fine

    print(f"Bug totali analizzati: {total_bugs}")
    print(f"Tempo impiegato: {end_time - start_time:.4f} secondi")   

    print("-" * 30)         
    print("CONTEGGIO PER SEVERITY:")
    # Iteriamo sul dizionario per stampare i risultati in modo ordinato
    for sev, count in severity_counts.items():
        print(f"- {sev}: {count}")
    print("-" * 30)

    
process_bug_report("data/Eclipse_original.json")
