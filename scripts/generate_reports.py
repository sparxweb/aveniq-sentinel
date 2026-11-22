"""Generate data quality reports on the benchmark sample dataset."""

import sys
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
from neuralshield.data.validation import generate_all_data_quality_reports
from neuralshield.data.discovery import inspect_dataset_inventory
from config.settings import SAMPLE_DATA_DIR, DATA_QUALITY_REPORTS_DIR

def main():
    sample_csv = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"
    if not sample_csv.is_file():
        print(f"Sample CSV not found at {sample_csv}")
        return

    print(f"Loading sample data from {sample_csv}...")
    df = pd.read_csv(sample_csv)
    inventory = inspect_dataset_inventory()

    print(f"Generating data quality reports in {DATA_QUALITY_REPORTS_DIR}...")
    generated = generate_all_data_quality_reports(
        df=df,
        inventory_dict=inventory,
        output_dir=DATA_QUALITY_REPORTS_DIR,
        target_col="label",
    )

    print("Successfully generated all reports:")
    for key, path in generated.items():
        print(f"  - {key}: {path} ({path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
