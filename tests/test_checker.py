import os
import sys
import tempfile
import pathlib

# Ensure parent directory (project root) is on sys.path when executing test directly
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.c64_syntax_checker import SyntaxChecker, check_file

BASIC_OK = """10 PRINT \"HELLO WORLD\"\n20 END\n"""
BASIC_MAZE = """1 rem maze generator by wizofwor
2 rem inspired by the book 10 print
10 print \"{clr}{home}             maze generator \"\n20 print \"  push f1 or f3 to change the pattern\"\n30 gosub 200 \n40 p = 5 : q = 205.5\n60 rem random maze generator\n70 for i=1104 to 1635 : poke i,q+rnd(1)\n80 get k$ : if k$<>\"\" then gosub 310\n90 next\n100 for i=1651 to 2024 : poke i,q+rnd(1)\n110 get k$ : if k$<>\"\" then gosub 310\n120 next\n130 goto 60\n190 end\n200 rem indicator bar\n210 for i=0 to 14 : read a : poke 1636+i,a : next\n250 for i=0 to 14 : read a : poke 55908+i,a : next\n290 return\n300 rem key control \n310 if k$=chr$(133) then p=p-1\n320 if k$=chr$(134) then p=p+1\n330 if p<0 then p=0\n340 if p>10 then p=10\n350 q = 205 + p/10\n360 rem update indicator bar\n370 for j = p+1 to 11 : poke 1637+j,100 : next\n380 for j = 1 to p+1 : poke 1637+j,224 : next\n390 return\n490 rem char and color data for indicator bar\n500 data 134,177,224,224,224,224,224,224\n510 data 100,100,100,100,100,134,179\n520 data 10,10,1,1,1,1,1,1\n530 data 1,1,1,1,1,7,7\n"""
BASIC_ERRORS = """10 NEXT J\n20 IF I=5 PRINT \"NO THEN\"\n30 GOTO 9999\n40 FOR I=1 TO 10\n50 NEXT I\n60 A@=5\n70 IF I 2 THEN 100\n80 GOTO 120\n90 PRINT \"UNREACHABLE\"\n100 END\n110 PRINT \"ALSO UNREACHABLE\"\n120 END\n"""

def write_temp(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix='.bas', text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def test_no_errors():
    path = write_temp(BASIC_OK)
    sc = SyntaxChecker()
    with open(path, 'r', encoding='utf-8') as f:
        sc.load(f.read())
    sc.validate()
    errors = [i for i in sc.issues if i.severity == 'ERROR']
    assert not errors, f"Unexpected errors: {errors}"


def test_detect_errors():
    path = write_temp(BASIC_ERRORS)
    sc = SyntaxChecker()
    with open(path, 'r', encoding='utf-8') as f:
        sc.load(f.read())
    sc.validate()
    errors = [i for i in sc.issues if i.severity == 'ERROR']
    warns = [i for i in sc.issues if i.severity == 'WARN']
    assert any('NEXT without matching FOR' in e.message for e in errors), 'Expected NEXT without matching FOR error'
    assert any('IF without THEN' in e.message for e in errors), 'Expected IF without THEN error'
    assert any("Invalid variable name 'A@'" in e.message for e in errors), 'Expected invalid variable name error for A@'
    # With new precedence parser we expect a diagnostic related to malformed IF expression (I 2): leftover token or unrecognized
    expr_diags = [d for d in errors+warns if ('Unexpected token' in d.message or 'Unrecognized token' in d.message)]
    assert expr_diags, 'Expected some expression-related diagnostic for malformed IF condition'
    # GOTO 9999 should be warning, not error
    assert any('target line 9999 does not exist' in w.message for w in warns)
    # Unreachable lines warnings for 90 and 110
    unreachable_lines = [w.line for w in warns if 'Unreachable line' in w.message]
    assert 90 in unreachable_lines and 110 in unreachable_lines

def test_maze_program_clean():
    path = write_temp(BASIC_MAZE)
    sc = SyntaxChecker()
    with open(path,'r',encoding='utf-8') as f:
        sc.load(f.read())
    # Disable reachability to avoid end-of-program unreachable warning for demonstration
    sc.enable_reachability_warnings = False
    sc.validate()
    operator_warns = [w for w in sc.issues if w.severity=='WARN' and 'Unknown token' in w.message]
    assert not operator_warns, f"Unexpected operator unknown token warnings: {[w.message for w in operator_warns]}"
    loop_errors = [e for e in sc.issues if e.severity=='ERROR' and 'FOR loops' in e.message]
    assert not loop_errors, f"Unexpected loop errors: {[e.message for e in loop_errors]}"

if __name__ == '__main__':
    # simple ad-hoc run
    test_no_errors()
    test_detect_errors()
    test_maze_program_clean()
    print('All tests passed.')
