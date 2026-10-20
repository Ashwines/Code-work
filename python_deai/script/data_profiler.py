import os
import sys
import json
import shutil
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from google import genai


# Base project folder: can be passed as argument (e.g. sys.argv[1]), otherwise defaults to D:\python_deai
PROJECT_FOLDER = Path(sys.argv[1])
LANDING = PROJECT_FOLDER / "landing"
DATA = PROJECT_FOLDER / "data"

PROCESSING = DATA / "processing"
ARCHIVE = DATA / "archive"
ERROR = DATA / "error"
OUTPUT = DATA / "output"

for folder in [LANDING, PROCESSING, ARCHIVE, ERROR, OUTPUT]:
    folder.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_FOLDER / ".env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

def load_dataframe(file_path):
    extension = file_path.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(file_path)
    if extension == ".json":
        return pd.read_json(file_path)
    if extension == ".xlsx":
        return pd.read_excel(file_path)
    if extension == ".txt":
        return pd.read_csv(file_path, sep="|")

    print(f"Unsupported file type: {extension}")
    return None

def profile_dataframe(df, file_name):
    print("\nFirst 5 records:")
    print(df.head())
    print("\nShape:")
    print(df.shape)
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nDataFrame information:")
    df.info()

    print("\nStatistical information:")
    print(df.describe(include="all"))
    print("\nNull values:")
    print(df.isnull().sum())
    print("\nUnique values:")
    print(df.nunique())
    duplicates = df.duplicated().sum()
    print("\nDuplicate records:", duplicates)

    row_count = len(df)
    if row_count:
        null_percentage = (df.isnull().sum() / row_count * 100).round(2)
    else:
        null_percentage = df.isnull().sum()

    column_profile = pd.DataFrame({
        "column_name": df.columns,
        "data_type": df.dtypes.astype(str).values,
        "null_count": df.isnull().sum().values,
        "actual_count": row_count,
        "unique_count": df.nunique().values,
        "null_percentage": null_percentage.values
    })

    profile_file = OUTPUT / f"{Path(file_name).stem}_profile.csv"
    column_profile.to_csv(profile_file, index=False)
    print("\nProfile saved:", profile_file)

    data_types = df.dtypes.astype(str).to_dict()
    return data_types, column_profile, duplicates
def build_prompts(file_name, df, data_types, column_profile):
    sample_json = df.head(10).astype(str).to_json(
        orient="records",
        indent=2,
        force_ascii=False
    )

    columns = df.columns.tolist()
    types_json = json.dumps(data_types, indent=2, ensure_ascii=False)
    profile_text = column_profile.to_string(index=False)

    classification_prompt = f"""
You are a Data Engineering and Data Governance expert.

Analyze this dataset.

File: {file_name}
Columns: {json.dumps(columns)}
Pandas data types:
{types_json}

Column profile:
{profile_text}

Sample records:
{sample_json}

Identify:
1. Business domain
2. Dataset type
3. PII columns
4. Sensitive columns
5. Identifier columns
6. Business measure columns
7. Date columns
8. Categorical columns

Explain the classification of every column.
Return valid JSON only, without Markdown fences.
Use only columns that exist in the dataset.
If a classification cannot be determined, state "unknown".
Do not infer sensitive personal attributes from names or weak evidence.
Flag possible PII for human review.
"""

    schema_prompt = f"""
You are a Senior Data Engineer.

Analyze this source dataset.

File: {file_name}
Columns: {json.dumps(columns)}
Pandas data types:
{types_json}

Column profile:
{profile_text}

Sample records:
{sample_json}

Determine:
1. Dataset business purpose
2. Recommended target table
3. Candidate primary key
4. Recommended partition column, if appropriate
5. Business meaning of every column
6. Recommended target data type
7. Nullable or not, based on evidence
8. Possible foreign keys
9. Data quality concerns

Return valid JSON only, without Markdown fences.
Use only columns that actually exist.
Do not claim a primary key or foreign key is confirmed unless evidence establishes it.
Label uncertain recommendations clearly.
"""
    return classification_prompt, schema_prompt
def ask_gemini(prompt):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt)
    return response.text


def process_file(source_file):
    file_name = source_file.name
    processing_file = PROCESSING / file_name

    print("Processing:", file_name)
    print("File size:", source_file.stat().st_size, "bytes")

    shutil.move(str(source_file), str(processing_file))

    df = load_dataframe(processing_file)
    if df is None:
        shutil.move(str(processing_file), str(ERROR / file_name))
        return

    if len(df.columns) == 0:
        print("Dataset has no columns:", file_name)
        shutil.move(str(processing_file), str(ERROR / file_name))
        return

    data_types, column_profile, duplicates = profile_dataframe(df, file_name)

    classification_prompt, schema_prompt = build_prompts(
        file_name, df, data_types, column_profile)

    print("\nRequesting AI classification with", MODEL, "...")
    classification = ask_gemini(classification_prompt)

    print("\nRequesting target schema recommendations with", MODEL, "...")
    schema = ask_gemini(schema_prompt)

    classification_file = OUTPUT / f"{Path(file_name).stem}_classification.json"
    schema_file = OUTPUT / f"{Path(file_name).stem}_schema.json"

    classification_file.write_text(classification, encoding="utf-8")
    schema_file.write_text(schema, encoding="utf-8")

    # Save a copy of the source data as CSV; this does not clean or deduplicate it.
    processed_file = OUTPUT / f"{Path(file_name).stem}_processed.csv"
    df.to_csv(processed_file, index=False)

    shutil.move(str(processing_file), str(ARCHIVE / file_name))

    print("\nSUCCESS:", file_name)
    print("Profile:", OUTPUT / f"{Path(file_name).stem}_profile.csv")
    print("Classification:", classification_file)
    print("Schema:", schema_file)
    print("Processed CSV:", processed_file)
    print("Duplicate records detected:", duplicates)
    print("Source archived:", ARCHIVE / file_name)


def main():
    supported_extensions = [".csv", ".json", ".xlsx", ".txt"]
    files = []
    
    for f in LANDING.iterdir():
        if f.is_file():
            if f.suffix.lower() in supported_extensions:
                files.append(f)
            else:                
                print("\nUnsupported file:", f.name)
                shutil.move(str(f), str(ERROR / f.name))
                print("Moved to:", ERROR / f.name)

    files.sort()

    print("Data Engineering Data Profiler")
    print("Gemini model:", MODEL)

    print("\nFiles available in landing:")
    for file_path in files:
        print(file_path.name)

    if not files:
        print("\nNo files found in landing.")
        print("Place CSV, JSON, XLSX, or TXT files there.")
        return

    for source_file in files:
        process_file(source_file)

    print("Pipeline execution completed.")
    print("Check data\\output, data\\archive, and data\\error.")

main()