# Data Profiler (python_deai)

A **data-profiling pipeline** built from the Inceptezlabs tutorial: ingest raw files
from a `landing/` folder, parse them into DataFrames, profile schema + data-quality
metrics, and hand the results to a Gemini model for source classification and
schema inference. Unparseable files are quarantined to `error/`.

## Project layout

```
python_deai/
├── script/
│   └── data_profiler.py   # main pipeline (standalone script, calls main() at bottom)
├── landing/               # drop CSV/JSON/XLSX/TXT files here (raw inputs)
├── data/
│   ├── archive/           # processed sources moved here (original bytes)
│   ├── error/             # unparseable .py / unparseable files
│   ├── output/            # *_classification.json, *_schema.json, *_processed.csv, *_profile.csv
│   └── processing/        # files currently being processed
├── run_pipeline.bat       # convenient orchestrator (run this to start)
├── requirements.txt
├── .env.example           # copy to .env and add GOOGLE_API_KEY
└── README.md
```

## Quick start

```bat
# 1. Configure your Gemini API key
copy .env.example .env
# edit .env:  GOOGLE_API_KEY=<your-key>

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Run the pipeline
run_pipeline.bat
```

`run_pipeline.bat` finds `landing/`, profiles every supported file, classifies each
source with Gemini, writes artifacts under `data/output/`, and archives the original
files under `data/archive/`. Any file it cannot parse (e.g. `.py`) is moved to
`data/error/`.

## Test suite

```bat
python test_pipeline.py .
```

Runs the full suite **without real AI calls** (mocked) and verifies:
- multi-format `load_dataframe()` (csv/json/xlsx/txt)
- `profile_dataframe()` artifact writing
- `build_prompts()` content
- mocked `ask_gemini()` response
- end-to-end `process_file()` (landing -> processing -> output classification/schema/CSV, source archived)
- `main()` quarantine of unsupported `.py` files

## Notes

- The pipeline is a **standalone script** (not a package): `data_profiler.py` calls
  `main()` at module bottom, so it cannot be imported directly. Tests load its source
  via `exec()` and strip the trailing `main()` call to keep imports side-effect free.
- This environment was verified with pandas 3.0.5, openpyxl 3.1.5, python-dotenv,
  pydantic 2.14.1, google-genai, google-auth, httpx, anyio, tenacity.
