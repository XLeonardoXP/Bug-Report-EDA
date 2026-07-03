import os
import json
import pandas as pd
from datetime import datetime

from src.features.temporal import extract_temporal_features
from src.features.collaboration import extract_collaboration_features
from src.features.text import extract_text_features
from src.features.linguistic import extract_linguistic_features
from src.features.sotware_engineering import extract_software_engineering_features

reporter_history = {}

def run_pipeline(input_folder, output_path, interim_folder):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(interim_folder, exist_ok=True)

    json_files = [f for f in os.listdir(input_folder) if f.endswith(".json")]

    if not json_files:
        print(f"Nessun file JSON trovato in {input_folder}")
        return

    all_bug_data = []
    is_mozilla = False

    # STEP 1: carica tutto e controlla il nome del file
    for filename in json_files:
        filepath = os.path.join(input_folder, filename)

        if filename == "Mozilla_original.json":
            is_mozilla = True

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    bug = data.get("bug", {})
                    if bug:
                        all_bug_data.append(bug)
                except json.JSONDecodeError:
                    continue

    # STEP 2: ordina TUTTO UNA SOLA VOLTA
    all_bug_data.sort(
        key=lambda bug: datetime.strptime(
            bug["creation_ts"],
            "%Y-%m-%d %H:%M:%S %z"
        )
    )

    # APPLICA IL LIMITE SOLO SE È MOZILLA
    if is_mozilla:
        all_bug_data = all_bug_data[:26334]

    rows = []

    # STEP 3: feature extraction in ordine temporale
    for bug in all_bug_data:
        features = {"bug_id": bug.get("bug_id")}

        features.update(extract_temporal_features(bug))
        features.update(extract_text_features(bug))
        features.update(extract_collaboration_features(bug, features))
        features.update(extract_linguistic_features(bug, features))
        features.update(extract_software_engineering_features(bug, reporter_history))

        rows.append(features)

    # STEP 4: salva
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

    print(f"\nSuccesso!")
    print(f"Salvati {len(df)} bug con {len(df.columns)} feature in {output_path}")