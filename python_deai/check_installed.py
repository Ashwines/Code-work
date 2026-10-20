"""Reports install state to a UTF-8 file for reliable reading."""
import importlib.util

def installed(name):
    return importlib.util.find_spec(name) is not None

lines = []
for pkg in ["openpyxl", "pandas", "dotenv", "pydantic", "websockets",
            "google.auth", "httpx", "anyio", "tenacity", "google.genai"]:
    lines.append(f"{pkg:16s} -> {'INSTALLED' if installed(pkg) else 'MISSING'}")

with open("install_state.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))