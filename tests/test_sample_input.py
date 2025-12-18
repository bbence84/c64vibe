import os, sys
from pathlib import Path

# Ensure module import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import utils.c64_syntax_checker as c64

SAMPLE_PATH = PROJECT_ROOT / 'sample_input.bas'

EXPECT_ERROR_SUBSTRING = 'NEXT without matching FOR'
EXPECT_LINE = 230  # documented intentional mismatch

def run_check():
    text = SAMPLE_PATH.read_text(encoding='utf-8')
    sc = c64.SyntaxChecker()
    sc.load(text)
    sc.validate()
    # Find the specific intentional error
    matched = [iss for iss in sc.issues if iss.line == EXPECT_LINE and EXPECT_ERROR_SUBSTRING in iss.message]
    assert matched, f"Expected intentional error '{EXPECT_ERROR_SUBSTRING}' at line {EXPECT_LINE}, but not found. Issues: {[ (i.line,i.message) for i in sc.issues ]}"
    # Ensure we didn't accidentally 'fix' it by FOR inference around REM or comments.
    print('OK: intentional NEXT mismatch present.')

if __name__ == '__main__':
    run_check()
