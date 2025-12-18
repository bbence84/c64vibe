import sys, json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import utils.c64_syntax_checker as c64

SAMPLE_PATH = PROJECT_ROOT / 'sample_input.bas'

def test_json_structure():
    data = c64.check_file(str(SAMPLE_PATH), return_structured=True)
    assert 'issues' in data and isinstance(data['issues'], list)
    assert 'summary' in data and 'errors' in data['summary'] and 'warnings' in data['summary']
    # Ensure each issue dict has required keys
    for issue in data['issues']:
        assert set(issue.keys()) == {'line','severity','message'}
    print('JSON structure OK')

if __name__ == '__main__':
    test_json_structure()
