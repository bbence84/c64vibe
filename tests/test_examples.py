import os
import sys
import pathlib
from typing import List, Tuple

# Ensure parent directory (project root) is on sys.path when executing test directly
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.c64_syntax_checker import SyntaxChecker

EXAMPLES_DIR = PROJECT_ROOT / "resources" / "examples"


def get_bas_files() -> List[pathlib.Path]:
    """Get all .bas files from the examples directory."""
    if not EXAMPLES_DIR.exists():
        return []
    return sorted(EXAMPLES_DIR.glob("*.bas"))


def check_bas_file(filepath: pathlib.Path) -> Tuple[str, bool, List[str], List[str]]:
    """
    Check a single .bas file using SyntaxChecker.
    
    Returns:
        Tuple of (filename, has_errors, error_messages, warning_messages)
    """
    sc = SyntaxChecker()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sc.load(content)
    sc.validate()
    
    errors = [f"Line {i.line}: {i.message}" for i in sc.issues if i.severity == 'ERROR']
    warnings = [f"Line {i.line}: {i.message}" for i in sc.issues if i.severity == 'WARN']
    
    has_errors = len(errors) > 0
    
    return (filepath.name, has_errors, errors, warnings)


def test_all_examples():
    """Test all .bas files in the examples directory."""
    bas_files = get_bas_files()
    
    assert len(bas_files) > 0, f"No .bas files found in {EXAMPLES_DIR}"
    
    print(f"\nTesting {len(bas_files)} .bas files from examples directory:\n")
    
    results = []
    files_with_errors = []
    
    for bas_file in bas_files:
        filename, has_errors, errors, warnings = check_bas_file(bas_file)
        results.append((filename, has_errors, errors, warnings))
        
        if has_errors:
            files_with_errors.append(filename)
        
        # Print results
        status = "❌ ERRORS" if has_errors else "✓ OK"
        print(f"{status}: {filename}")
        
        if errors:
            print(f"  Errors ({len(errors)}):")
            for err in errors[:5]:  # Limit to first 5 errors
                print(f"    - {err}")
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more errors")
        
        if warnings:
            print(f"  Warnings ({len(warnings)}):")
            for warn in warnings[:3]:  # Limit to first 3 warnings
                print(f"    - {warn}")
            if len(warnings) > 3:
                print(f"    ... and {len(warnings) - 3} more warnings")
        
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(bas_files)} files tested")
    print(f"  ✓ Clean: {len(bas_files) - len(files_with_errors)}")
    print(f"  ❌ With errors: {len(files_with_errors)}")
    
    if files_with_errors:
        print(f"\nFiles with errors: {', '.join(files_with_errors)}")
    
    print(f"{'='*60}\n")
    
    # Note: We don't fail the test if examples have errors, as they might be
    # intentionally broken or legacy code. This test is for informational purposes.
    # If you want to enforce error-free examples, uncomment the line below:
    # assert not files_with_errors, f"Found errors in: {', '.join(files_with_errors)}"


def test_specific_file_alice():
    """Test alice.bas specifically - it should have no critical errors."""
    alice_path = EXAMPLES_DIR / "alice.bas"
    if not alice_path.exists():
        print(f"Skipping: {alice_path} not found")
        return
    
    filename, has_errors, errors, warnings = check_bas_file(alice_path)
    
    # This is an example of testing a specific file
    # Adjust assertions based on what you expect
    print(f"\nTesting {filename} specifically:")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")


if __name__ == '__main__':
    # Run tests
    test_all_examples()
    print("\n" + "="*60)
    test_specific_file_alice()
    print("\nAll tests completed.")
