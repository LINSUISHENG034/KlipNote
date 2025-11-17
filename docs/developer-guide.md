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

## ⚠️ CRITICAL: Use `uv` for environment management

**IMPORTANT:** Belle2 and WhisperX **rely on** (or **use**) different **environments**. **Belle2 uses** the environment at `backend/.venv`, and **WhisperX uses** the environment at `backend/.venv-whisperx`.