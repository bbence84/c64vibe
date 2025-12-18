import pathlib, sys

# Ensure project root on path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.c64_syntax_checker import check_source

BASIC_OK = """10 PRINT "HELLO"\n20 END\n"""
BASIC_BAD = """10 IF A=5 PRINT "MISSING THEN"\n20 END\n"""

def test_check_source_ok():
    rc = check_source(BASIC_OK)
    assert rc == 0, "Expected no errors for BASIC_OK"

def test_check_source_error():
    rc = check_source(BASIC_BAD)
    assert rc == 1, "Expected errors for BASIC_BAD (IF without THEN)"

if __name__ == '__main__':
    test_check_source_ok()
    test_check_source_error()
    print("check_source tests passed")
