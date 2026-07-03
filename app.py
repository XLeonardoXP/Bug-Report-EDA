from pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline(
        input_folder="data/raw",
        output_path="data/processed/features.csv",
        interim_folder="data/interim"
    )