# C64 BASIC Syntax Checker

A lightweight Python utility to perform structural syntax checks on Commodore 64 BASIC source files (text `.bas` format with line numbers).

## Features
- Validates line numbers (presence, range, duplicates).
- Checks FOR/NEXT pairing and variable consistency.
- Ensures IF has a corresponding THEN.
- Verifies GOTO/GOSUB / ON GOTO/GOSUB targets exist (warn if missing).
- Detects unmatched quotes and parentheses.
- Flags NEXT without FOR, unclosed FOR loops.
- Warns about unknown tokens (heuristic, case-insensitive).

## Not Implemented
- Full expression parsing or type checking.
- Binary PRG tokenized file handling.
- Performance optimizations for very large programs.

## Installation
Python 3.9+ recommended. No external dependencies.

```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt  # (currently empty / can skip)
```

## Usage
```bash
python c64_syntax_checker.py sample_input.bas
```
Exit code is `0` if no errors, `1` if errors found.

## Sample Output
```
ERROR: Line 230: NEXT without matching FOR
ERROR: Line 240: IF without THEN
WARN: Line 220: GOTO target line 9999 does not exist

Summary: 2 error(s), 1 warning(s)
```

## Programmatic Use
```python
from c64_syntax_checker import SyntaxChecker, check_source

# Option 1: Manual class usage
text = open('sample_input.bas').read()
sc = SyntaxChecker()
sc.load(text)
sc.validate()
for issue in sc.issues:
    print(issue.severity, issue.line, issue.message)

# Option 2: Convenience helper for in-memory source
src = "10 PRINT \"HELLO\"\n20 END\n"
exit_code = check_source(src)  # 0 if no errors, 1 if errors

# Structured JSON-style result
data = check_source(src, return_structured=True)
print(data['summary'])
```

## Testing
Run simple tests:
```bash
python tests/test_checker.py
```

## Future Enhancements
- Add tokenized PRG loader.
- Add optional auto-suggest for missing THEN or variable typos.
- Implement flow graph for unreachable code detection.

## License
MIT (Add LICENSE file if needed).
