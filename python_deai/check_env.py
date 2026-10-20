"""Environment check - writes results to a file for reliable capture."""
results = []
try:
    import openpyxl
    results.append(f"openpyxl {openpyxl.__version__}")
except Exception as e:
    results.append(f"openpyxl FAIL: {e}")

try:
    import google.genai
    results.append("google-genai OK")
except Exception as e:
    results.append(f"google-genai FAIL: {e}")

try:
    import pandas
    results.append(f"pandas {pandas.__version__}")
except Exception as e:
    results.append(f"pandas FAIL: {e}")

with open("env_check.txt", "w") as f:
    f.write("\n".join(results))
print("\n".join(results))