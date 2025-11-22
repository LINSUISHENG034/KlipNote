## ⚠️ CRITICAL: Bash Tool Uses Unix Commands

**IMPORTANT:** Even on Windows, the Bash tool in Claude Code executes **Unix/bash commands**, NOT Windows CMD or PowerShell commands.

**This means:**
- ✅ Use Unix commands: `rm`, `ls`, `cp`, `mv`, `test`, `mkdir -p`
- ❌ DO NOT use Windows CMD: `del`, `dir`, `copy`, `move`, `if exist`
- 🎯 Prefer specialized tools (Read, Write, Edit) over bash for file operations

**Examples of common mistakes:**
```bash
# ❌ WRONG - Windows CMD syntax (will fail)
if exist "file.txt" del "file.txt"
dir /b
copy source.txt dest.txt

# ✅ CORRECT - Unix bash syntax
test -f "file.txt" && rm "file.txt"
# or
[ -f "file.txt" ] && rm "file.txt"
ls
cp source.txt dest.txt

# 🎯 BEST - Use specialized tools
# Use Read tool to read files
# Use Write tool to create files
# Use Edit tool to modify files
```

---

## 🛠️ Project Environment Management: Using `uv` (For Senior Developers)

* **Tool:** This project utilizes **`uv`** for ultra-fast package and virtual environment management.
* **Execution Standard:** All Python script execution *must* be performed using **`uv run`** to ensure the correct environment and dependencies are loaded.

### ⚠️ Critical Environment Isolation

Due to **dependency conflicts**, different models are configured in **isolated virtual environments**. You **must** specify the correct environment path when running related scripts:

| Model | Virtual Environment Path | Example Execution Command |
| :--- | :--- | :--- |
| **Belle2** | `backend/.venv` | `uv run --with backend/.venv python your_script.py` |
| **WhisperX** | `backend/.venv-whisperx` | `uv run --with backend/.venv-whisperx python another_script.py` |

> **Key Action:** Always use `uv run --with [PATH]` for running scripts. Avoid direct `python` calls.

---