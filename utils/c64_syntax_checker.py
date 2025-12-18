"""
C64 BASIC Syntax Checker

Validates a Commodore 64 BASIC program for common structural & syntactic issues:
- Line number presence (must be first token and numeric)
- Duplicate line numbers
- Line number range (0-63999 typical for C64 BASIC)
- Unknown keywords (basic set; ignores after REM)
- Quotation mark pairing
- Parentheses balance
- IF ... THEN structure
- FOR / NEXT pairing (variable match when specified)
- GOTO / GOSUB target existence
- ON <expr> GOTO/GOSUB line list validity
- Basic token case-insensitive
- Expression sanity (missing operators, invalid variable names)
- Control-flow graph reachability (flags unreachable lines)

Limitations:
- Does not fully parse expressions or detect all illegal variable usages.
- Does not evaluate numeric expressions; treats them as opaque.
- Does not handle embedded control chars or tokenized PRG binary format.

Usage:
    python c64_syntax_checker.py path/to/program.bas

Program format expected: ASCII text lines representing BASIC with line numbers.
"""
from __future__ import annotations
import re
import sys
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

BASIC_KEYWORDS = {
    'END','FOR','NEXT','DATA','INPUT','DIM','READ','LET','GOTO','RUN','IF','THEN','ELSE','RESTORE','GOSUB','RETURN','REM','STOP','ON','WAIT','LOAD','SAVE','VERIFY','DEF','POKE','PRINT','CONT','LIST','CLR','CMD','SYS','OPEN','CLOSE','GET','NEW','TAB','TO','FN','SPC','THEN','NOT','STEP','AND','OR','$','ABS','ASC','ATN','CHR$','COS','EXP','INT','LEFT$','LEN','LOG','MID$','PEEK','POS','RIGHT$','RND','SGN','SIN','SQR','STR$','TAN','VAL'}
# Accept synonyms (e.g., '?' for PRINT) handled in tokenization.

# Built-in function metadata: return type, min args, max args (-1 means variadic / same as min)
FUNC_INFO = {
    'CHR$': ('string',1,1),
    'MID$': ('string',2,3), # MID$(str,pos[,len])
    'LEFT$': ('string',2,2),
    'RIGHT$': ('string',2,2),
    'STR$': ('string',1,1),
    'VAL': ('numeric',1,1),
    'ASC': ('numeric',1,1),
    'LEN': ('numeric',1,1),
    'RND': ('numeric',0,1),
    'INT': ('numeric',1,1),
    'ABS': ('numeric',1,1),
    'LOG': ('numeric',1,1),
    'SIN': ('numeric',1,1),
    'COS': ('numeric',1,1),
    'TAN': ('numeric',1,1),
    'SQR': ('numeric',1,1),
    'PI': ('numeric',0,0), # treated as constant function w/ no args
}

LINE_RE = re.compile(r"^(\d{1,5})\s*(.*)$")
TOKEN_SPLIT_RE = re.compile(r"(?<!\$)[^A-Za-z0-9?$]\s*|")  # We'll do manual scanning instead.

@dataclass
class BasicLine:
    number: int
    raw: str
    content: str  # part after line number
    tokens: List[str] = field(default_factory=list)

@dataclass
class Issue:
    line: Optional[int]
    severity: str  # 'ERROR' or 'WARN'
    message: str

class SyntaxChecker:
    def __init__(self):
        self.lines: List[BasicLine] = []
        self.issues: List[Issue] = []
        self.line_map: Dict[int, BasicLine] = {}
        self.cfg_edges: Dict[int, List[int]] = {}
        self.unreachable: List[int] = []
        self.enable_reachability_warnings: bool = True
        self.var_types: Dict[str,str] = {}  # variable name -> 'string' | 'numeric' | 'integer' | 'unknown'
        self.reachability_mode: str = 'strict'  # 'strict' | 'relaxed'
        self.lines_with_input: set[int] = set()  # lines containing dynamic input (GET / INPUT)
        self.backward_goto_lines: set[int] = set()  # lines that end with unconditional backward GOTO (potential infinite loop)
        # Track subroutine targets for improved GOSUB/RETURN validation
        self.gosub_targets = set()  # set of subroutine entry line numbers targeted by GOSUB

    def load(self, text: str):
        for idx, raw in enumerate(text.splitlines()):
            stripped = raw.strip()
            if not stripped:
                continue
            m = LINE_RE.match(stripped)
            if not m:
                self._add_issue(None, 'ERROR', f"Missing/invalid line number on line {idx+1}: '{raw}'")
                continue
            num = int(m.group(1))
            if not (0 <= num <= 63999):
                self._add_issue(num, 'ERROR', f"Line number {num} out of range (0-63999)")
            if num in self.line_map:
                self._add_issue(num, 'ERROR', f"Duplicate line number {num}")
            content = m.group(2)
            bl = BasicLine(number=num, raw=raw, content=content)
            bl.tokens = self._tokenize(content)
            self.lines.append(bl)
            self.line_map[num] = bl

    def _tokenize(self, content: str) -> List[str]:
        tokens: List[str] = []
        i = 0
        in_string = False
        current = ''
        operator_chars = ':;,()=<>+-*/^'
        while i < len(content):
            c = content[i]
            if c == '"':
                current += c
                i += 1
                # collect until closing quote
                while i < len(content):
                    current += content[i]
                    if content[i] == '"':
                        i += 1
                        break
                    i += 1
                tokens.append(current)
                current = ''
                continue
            if c.isspace():
                if current:
                    tokens.append(current)
                    current = ''
                i += 1
                continue
            # separators & operators we treat as individual tokens
            if c in operator_chars:
                if current:
                    tokens.append(current)
                    current = ''
                tokens.append(c)
                i += 1
                continue
            current += c
            i += 1
        if current:
            tokens.append(current)
        return tokens

    def validate(self):
        self._check_quotes()
        self._check_parentheses()
        self._check_keywords()
        self._check_if_then()
        self._check_for_next()
        self._check_goto_gosub()
        self._check_on_goto_gosub()
        self._check_expressions()
        self._check_gosub_return()
        self._build_cfg_and_flag_unreachable()

    def _add_issue(self, line: Optional[int], severity: str, msg: str):
        self.issues.append(Issue(line, severity, msg))

    def _check_quotes(self):
        # tokenization already treats strings as single tokens; just ensure even number of '"'
        for bl in self.lines:
            if bl.content.count('"') % 2 != 0:
                self._add_issue(bl.number, 'ERROR', 'Unmatched quotes')

    def _check_parentheses(self):
        for bl in self.lines:
            stack = 0
            for ch in bl.content:
                if ch == '(':
                    stack += 1
                elif ch == ')':
                    stack -= 1
                    if stack < 0:
                        self._add_issue(bl.number, 'ERROR', 'Closing parenthesis without matching opening')
                        break
            if stack > 0:
                self._add_issue(bl.number, 'ERROR', 'Unclosed parenthesis')

    def _check_keywords(self):
        for bl in self.lines:
            # stop parsing after REM
            for tok in bl.tokens:
                u = tok.upper()
                if u.startswith('"'):
                    continue
                if u == '?':
                    continue  # synonym for PRINT
                if u == 'REM':
                    break
                # Skip numeric literals, variable names, separators
                if re.match(r'^\d+(\.\d+)?$', tok):
                    continue
                if tok in [':',';','(',',',')']:
                    continue
                # Skip operators
                if u in ("=","+","-","/","*","^","<",">","<=",">=","<>"):
                    continue
                # function names with trailing $ or parenthesis handled by starting token
                base = u.rstrip('()')
                if base and base not in BASIC_KEYWORDS and not re.match(r'^[A-Z][A-Z0-9]*([\$%][A-Z0-9]*)?$', base):
                    self._add_issue(bl.number, 'WARN', f"Unknown token '{tok}'")

    def _check_if_then(self):
        for bl in self.lines:
            tokens_u = [t.upper() for t in bl.tokens]
            if 'IF' in tokens_u:
                # find THEN after IF before any colon
                try:
                    if_idx = tokens_u.index('IF')
                    # ensure THEN exists
                    if 'THEN' not in tokens_u[if_idx+1:]:
                        self._add_issue(bl.number, 'ERROR', 'IF without THEN')
                except ValueError:
                    continue

    def _check_for_next(self):
        # Track FOR variable stack
        for_stack: List[Tuple[int, Optional[str]]] = []
        for bl in self.lines:
            # Ignore anything after REM in loop analysis to prevent false FOR in comments
            effective_tokens = []
            for t in bl.tokens:
                if t.upper() == 'REM':
                    break
                effective_tokens.append(t)
            tu = [t.upper() for t in effective_tokens]
            i = 0
            while i < len(tu):
                if tu[i] == 'FOR':
                    # expect variable name next like A= or A SPACE
                    var = None
                    j = i+1
                    if j < len(effective_tokens):
                        var_candidate = effective_tokens[j]
                        if re.match(r'^[A-Za-z][A-Za-z0-9]*([\$%])?$', var_candidate):
                            var = var_candidate.upper()
                    for_stack.append((bl.number, var))
                elif tu[i] == 'NEXT':
                    # Support NEXT I,J,K : parse comma-separated identifiers after NEXT
                    next_vars: List[str] = []
                    k = i+1
                    while k < len(effective_tokens):
                        token = effective_tokens[k]
                        if token == ',':
                            k += 1
                            continue
                        if re.match(r'^[A-Za-z][A-Za-z0-9]*([\$%])?$', token):
                            next_vars.append(token.upper())
                            k += 1
                            # If next token is not comma, break list
                            if k >= len(effective_tokens) or effective_tokens[k] != ',':
                                break
                        else:
                            break
                    if not next_vars:
                        next_vars = [None]  # single implicit NEXT without variable
                    for nv in next_vars:
                        if not for_stack:
                            self._add_issue(bl.number, 'ERROR', 'NEXT without matching FOR')
                        else:
                            start_line, for_var = for_stack.pop()
                            if nv and for_var and nv != for_var:
                                self._add_issue(bl.number, 'WARN', f"NEXT variable {nv} does not match FOR variable {for_var} (FOR at line {start_line})")
                i += 1
        if for_stack:
            remaining = ', '.join(f"{v or '?'}@{ln}" for ln, v in for_stack)
            self._add_issue(None, 'ERROR', f"Unclosed FOR loops: {remaining}")

    def _check_goto_gosub(self):
        for bl in self.lines:
            tu = [t.upper() for t in bl.tokens]
            for i, tok in enumerate(tu):
                if tok in ('GOTO','GOSUB'):
                    # next token should be a line number
                    if i+1 >= len(bl.tokens):
                        self._add_issue(bl.number, 'ERROR', f"{tok} without target line")
                        continue
                    target = bl.tokens[i+1]
                    if not target.isdigit():
                        self._add_issue(bl.number, 'ERROR', f"{tok} target '{target}' is not a line number")
                        continue
                    tnum = int(target)
                    if tnum not in self.line_map:
                        self._add_issue(bl.number, 'WARN', f"{tok} target line {tnum} does not exist")

    def _check_on_goto_gosub(self):
        for bl in self.lines:
            tu = [t.upper() for t in bl.tokens]
            for i, tok in enumerate(tu):
                if tok == 'ON':
                    # find GOTO/GOSUB later in line before REM/colon
                    slice_tokens = tu[i+1:]
                    mode = None
                    if 'GOTO' in slice_tokens:
                        mode = 'GOTO'
                    elif 'GOSUB' in slice_tokens:
                        mode = 'GOSUB'
                    if not mode:
                        self._add_issue(bl.number, 'ERROR', 'ON without GOTO/GOSUB')
                        continue
                    # line list after mode
                    after_idx = slice_tokens.index(mode)
                    line_list = bl.tokens[i+1+after_idx+1:]
                    # collect numeric tokens until colon or end
                    collected = []
                    for t in line_list:
                        if t == ':' or t.upper() == 'REM':
                            break
                        if t.endswith(','):
                            t = t.rstrip(',')
                        if t:
                            collected.append(t)
                    if not collected:
                        self._add_issue(bl.number, 'ERROR', f"ON {mode} without line targets")
                        continue
                    for c in collected:
                        if not c.isdigit():
                            self._add_issue(bl.number, 'ERROR', f"ON {mode} target '{c}' not a number")
                        else:
                            tnum = int(c)
                            if tnum not in self.line_map:
                                self._add_issue(bl.number, 'WARN', f"ON {mode} target line {tnum} does not exist")
                    # Static selector analysis: if expression immediately after ON is constant
                    selector_tokens = bl.tokens[i+1:i+1+after_idx]  # tokens between ON and mode keyword
                    if selector_tokens and len(selector_tokens) == 1 and selector_tokens[0].isdigit():
                        sel_val = int(selector_tokens[0])
                        # ON expr GOTO chooses line based on expr: 1 -> first list item
                        if sel_val == 0:
                            # falls through; warn if no fallthrough statement before end
                            pass
                        elif sel_val > len(collected):
                            self._add_issue(bl.number, 'WARN', f"ON {mode} selector {sel_val} exceeds target list length {len(collected)}")

    # ------------------ Expression Checking ------------------
    _OP_SET = {"+","-","*","/","^","AND","OR","=","<",">","<=",">=","<>"}

    def _is_string(self, tok: str) -> bool:
        return tok.startswith('"') and tok.endswith('"') and len(tok) >= 2

    def _is_number(self, tok: str) -> bool:
        return bool(re.match(r'^\d+(\.\d+)?$', tok))

    def _is_identifier(self, tok: str) -> bool:
        # Accept constructs like I%2 treating them as I% (type suffix before ignored trailing chars)
        return bool(re.match(r'^[A-Za-z][A-Za-z0-9]*([\$%][A-Za-z0-9]*)?$', tok))

    def _is_operator(self, tok: str) -> bool:
        return tok.upper() in self._OP_SET

    def _normalize_ops(self, tokens: List[str]) -> List[str]:
        # Merge two-character comparison operators if tokenized separately (e.g., '>' '=')
        merged = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            u = t.upper()
            nxt = tokens[i+1] if i+1 < len(tokens) else None
            pair = (u + (nxt.upper() if nxt else '')) if nxt else None
            if nxt and pair in ('<=','>=','<>'):
                merged.append(pair)
                i += 2
            else:
                merged.append(t)
                i += 1
        return merged

    def _split_statements(self, bl: BasicLine) -> List[List[str]]:
        stmts: List[List[str]] = []
        current: List[str] = []
        for tok in bl.tokens:
            if tok.upper() == 'REM':
                # stop further processing on line
                if current:
                    stmts.append(current)
                return stmts
            if tok == ':':
                stmts.append(current)
                current = []
            else:
                current.append(tok)
        if current:
            stmts.append(current)
        return stmts

    def _find_expression_slices(self, stmt: List[str]) -> List[List[str]]:
        """Return list of token slices that are likely expressions for basic validation.
        Cases:
        - LET var = expr
        - var = expr (implicit LET)
        - IF <expr> THEN ...
        - FOR var = start TO end [STEP step]
        """
        slices: List[List[str]] = []
        upper = [t.upper() for t in stmt]
        # IF ... THEN
        if 'IF' in upper and 'THEN' in upper:
            i_if = upper.index('IF')
            i_then = upper.index('THEN')
            if i_then > i_if + 1:
                slices.append(stmt[i_if+1:i_then])
            # after THEN if first token numeric implies line number target; else remaining may be statements with expressions but we skip
        # FOR var = start TO end STEP step
        if len(stmt) >= 4 and upper[0] == 'FOR':
            # find '=' then 'TO'
            if '=' in stmt:
                try:
                    i_eq = stmt.index('=')
                    if 'TO' in upper:
                        i_to = upper.index('TO')
                        if i_to > i_eq + 1:
                            slices.append(stmt[i_eq+1:i_to])  # start expr
                        # end expr until STEP or line end
                        if 'STEP' in upper:
                            i_step = upper.index('STEP')
                            if i_step > i_to + 1:
                                slices.append(stmt[i_to+1:i_step])
                            if i_step + 1 < len(stmt):
                                slices.append(stmt[i_step+1:])
                        else:
                            if i_to + 1 < len(stmt):
                                slices.append(stmt[i_to+1:])
                except ValueError:
                    pass
        # LET / implicit assignment
        if upper and (upper[0] == 'LET' or (len(stmt) > 2 and stmt[1] == '=')):
            if upper[0] == 'LET':
                # expect pattern LET var = expr
                if len(stmt) >= 4 and stmt[2] == '=':
                    slices.append(stmt[3:])
            else:
                # implicit var = expr (even if var name invalid we still capture expression part)
                if '=' in stmt:
                    i_eq = stmt.index('=')
                    if i_eq + 1 < len(stmt):
                        slices.append(stmt[i_eq+1:])
        return slices

    def _validate_expression(self, expr_tokens: List[str], line_no: int):
        if not expr_tokens:
            return
        parser = ExpressionParser(self, expr_tokens, line_no)
        result_type = parser.parse_expression()
        # Record type info if assignment target processed earlier via _check_expressions
        # Type mismatch detection for '+' happens inside parser; here we could add more global checks if needed.

    def _check_expressions(self):
        for bl in self.lines:
            stmts = self._split_statements(bl)
            for stmt in stmts:
                if not stmt:
                    continue
                upper0 = stmt[0].upper()
                # Track dynamic input sources for relaxed reachability
                if any(t.upper() in ('GET','INPUT') for t in stmt):
                    self.lines_with_input.add(bl.number)
                # Validate assignment LHS variable name (LET var = ... or implicit)
                if upper0 == 'LET' and len(stmt) >= 3 and stmt[2] == '=':
                    var_tok = stmt[1]
                    if re.match(r'^[A-Za-z]', var_tok) and not self._is_identifier(var_tok):
                        self._add_issue(bl.number, 'ERROR', f"Invalid variable name '{var_tok}'")
                elif len(stmt) >= 3 and stmt[1] == '=':
                    var_tok = stmt[0]
                    if re.match(r'^[A-Za-z]', var_tok) and not self._is_identifier(var_tok):
                        self._add_issue(bl.number, 'ERROR', f"Invalid variable name '{var_tok}'")
                slices = self._find_expression_slices(stmt)
                for expr in slices:
                    self._validate_expression(expr, bl.number)

    # ------------------ Control Flow Graph & Reachability ------------------
    def _build_cfg_and_flag_unreachable(self):
        if not self.lines:
            return
        ordered = sorted(self.line_map.keys())
        next_map = {}
        for idx, ln in enumerate(ordered):
            next_map[ln] = ordered[idx+1] if idx+1 < len(ordered) else None
        # Build edges
        for bl in self.lines:
            self.cfg_edges[bl.number] = []
            terminating = False
            stmts = self._split_statements(bl)
            for stmt in stmts:
                upper = [t.upper() for t in stmt]
                if not stmt:
                    continue
                # IF with line-number THEN target
                if 'IF' in upper and 'THEN' in upper:
                    i_then = upper.index('THEN')
                    if i_then + 1 < len(stmt) and stmt[i_then+1].isdigit():
                        self.cfg_edges[bl.number].append(int(stmt[i_then+1]))
                if upper and upper[0] in ('GOTO','GO','GOSUB'):
                    # handle GOTO <n> or GOSUB <n>
                    if len(stmt) >= 2 and stmt[1].isdigit():
                        self.cfg_edges[bl.number].append(int(stmt[1]))
                    if upper[0] == 'GOTO':
                        terminating = True
                        break
                # Handle standalone GOTO/GOSUB inside line (not first token)
                for i,tok in enumerate(upper):
                    if tok in ('GOTO','GOSUB') and i+1 < len(stmt) and stmt[i+1].isdigit():
                        self.cfg_edges[bl.number].append(int(stmt[i+1]))
                        if tok == 'GOTO':
                            terminating = True
                            break
                if terminating:
                    break
                if any(k in upper for k in ('END','STOP')):
                    terminating = True
                    break
            if not terminating:
                nxt = next_map.get(bl.number)
                if nxt is not None:
                    self.cfg_edges[bl.number].append(nxt)
        # Reachability
        entry = min(self.line_map.keys())
        visited = set()
        stack = [entry]
        while stack:
            ln = stack.pop()
            if ln in visited:
                continue
            visited.add(ln)
            for tgt in self.cfg_edges.get(ln, []):
                if tgt in self.line_map and tgt not in visited:
                    stack.append(tgt)
        for ln in ordered:
            if ln not in visited:
                self.unreachable.append(ln)
                if self.enable_reachability_warnings:
                    self._add_issue(ln, 'WARN', 'Unreachable line (no control-flow path)')

    def report(self, print_errors: bool = True, return_warnings: bool = True) -> Tuple[int,int]:
        """Return a human-readable text report of all issues.

        Previously this method returned (errors, warnings) counts. It now
        returns the full textual report while still printing it when
        print_errors=True.

        Returns:
            str: Multiline string listing each issue followed by a summary.
        """
        errors = sum(1 for i in self.issues if i.severity == 'ERROR')
        warnings = sum(1 for i in self.issues if i.severity == 'WARN')
        lines: List[str] = []
        for issue in self.issues:
            if not return_warnings and issue.severity == 'WARN':
                continue
            loc = f"Line {issue.line}" if issue.line is not None else "(global)"
            lines.append(f"{issue.severity}: {loc}: {issue.message}")
        lines.append("")
        if not return_warnings:
            lines.append(f"Summary: {errors} error(s)")
        else:
            lines.append(f"Summary: {errors} error(s), {warnings} warning(s)")
        report_text = "\n".join(lines)
        if print_errors:
            print(report_text)
        return report_text

    def structured(self) -> Dict[str, object]:
        """Return a structured representation of issues and summary suitable for JSON."""
        return {
            'issues': [
                {
                    'line': issue.line,
                    'severity': issue.severity,
                    'message': issue.message
                } for issue in self.issues
            ],
            'summary': {
                'errors': sum(1 for i in self.issues if i.severity == 'ERROR'),
                'warnings': sum(1 for i in self.issues if i.severity == 'WARN')
            },
            'unreachable': self.unreachable,
            'reachability_mode': self.reachability_mode,
        }

    # --------------- GOSUB / RETURN Matching ---------------
    def _check_gosub_return(self):
        # Collect all GOSUB target line numbers
        for bl in self.lines:
            tokens_before_rem = []
            for t in bl.tokens:
                if t.upper() == 'REM':
                    break
                tokens_before_rem.append(t)
            upper = [t.upper() for t in tokens_before_rem]
            for i,tok in enumerate(upper):
                if tok == 'GOSUB':
                    if i+1 >= len(upper) or not upper[i+1].isdigit():
                        self._add_issue(bl.number,'ERROR','GOSUB without target line')
                    else:
                        tgt = int(upper[i+1])
                        self.gosub_targets.add(tgt)
        # For each target line, ensure there's a RETURN after it
        for tgt in sorted(self.gosub_targets):
            has_return = False
            for bl in self.lines:
                if bl.number < tgt:
                    continue
                # stop scanning if we reach next subroutine start (another target) and haven't found RETURN yet? We still continue; single RETURN suffices.
                tokens_before_rem = []
                for t in bl.tokens:
                    if t.upper() == 'REM':
                        break
                    tokens_before_rem.append(t)
                if any(t.upper() == 'RETURN' for t in tokens_before_rem):
                    has_return = True
                    break
            if not has_return:
                self._add_issue(None,'ERROR',f"Missing RETURN for GOSUB target line {tgt}")
        # Detect stray RETURN with no preceding GOSUB target line at all
        if not self.gosub_targets:
            for bl in self.lines:
                tokens_before_rem = []
                for t in bl.tokens:
                    if t.upper() == 'REM':
                        break
                    tokens_before_rem.append(t)
                if any(t.upper() == 'RETURN' for t in tokens_before_rem):
                    self._add_issue(bl.number,'WARN','RETURN appears but no GOSUB targets found')

# ------------------ Expression Parser with Precedence ------------------
class ExpressionParser:
    def __init__(self, checker: SyntaxChecker, tokens: List[str], line_no: int):
        self.c = checker
        self.toks = checker._normalize_ops(tokens)
        self.pos = 0
        self.line_no = line_no

    def peek(self) -> Optional[str]:
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def advance(self) -> Optional[str]:
        t = self.peek()
        if t is not None:
            self.pos += 1
        return t

    def parse_expression(self) -> str:
        etype = self.parse_or()
        if self.peek() is not None:
            # leftover tokens; mark as suspicious
            self.c._add_issue(self.line_no,'WARN', f"Unexpected token '{self.peek()}' after expression")
        return etype

    # Precedence: OR > AND > REL > ADD > MUL > UNARY > PRIMARY
    def parse_or(self) -> str:
        left = self.parse_and()
        while True:
            tok = self.peek()
            if tok and tok.upper() == 'OR':
                self.advance()
                right = self.parse_and()
                left = self.combine_types(left,right,'OR')
            else:
                break
        return left

    def parse_and(self) -> str:
        left = self.parse_rel()
        while True:
            tok = self.peek()
            if tok and tok.upper() == 'AND':
                self.advance()
                right = self.parse_rel()
                left = self.combine_types(left,right,'AND')
            else:
                break
        return left

    def parse_rel(self) -> str:
        left = self.parse_add()
        tok = self.peek()
        if tok and tok.upper() in ('=','<','>','<=','>=','<>'):
            self.advance()
            right = self.parse_add()
            # relational result numeric (treated as boolean numeric)
            return 'numeric'
        return left

    def parse_add(self) -> str:
        left = self.parse_mul()
        while True:
            tok = self.peek()
            if tok in ('+','-'):
                op = tok
                self.advance()
                right = self.parse_mul()
                # Type rules for '+' (string concatenation) and '-' (numeric only)
                if op == '+':
                    if left == 'string' and right == 'string':
                        left = 'string'
                    elif left == 'numeric' and right == 'numeric':
                        left = 'numeric'
                    else:
                        # Mixed types
                        self.c._add_issue(self.line_no,'ERROR', f"Type mismatch for '+' between {left} and {right}")
                        left = 'unknown'
                else:  # '-'
                    if left != 'numeric' or right != 'numeric':
                        self.c._add_issue(self.line_no,'ERROR', "'-' applied to non-numeric operand")
                        left = 'unknown'
                    else:
                        left = 'numeric'
            else:
                break
        return left

    def parse_mul(self) -> str:
        left = self.parse_unary()
        while True:
            tok = self.peek()
            if tok in ('*','/','^'):
                self.advance()
                right = self.parse_unary()
                if left != 'numeric' or right != 'numeric':
                    self.c._add_issue(self.line_no,'ERROR', f"Operator '{tok}' applied to non-numeric operand")
                    left = 'unknown'
                else:
                    left = 'numeric'
            else:
                break
        return left

    def parse_unary(self) -> str:
        tok = self.peek()
        if tok and tok.upper() in ('-','NOT'):
            self.advance()
            inner = self.parse_unary()
            if tok == '-' and inner != 'numeric':
                self.c._add_issue(self.line_no,'ERROR', "Unary '-' on non-numeric operand")
                return 'unknown'
            return inner
        return self.parse_primary()

    def parse_primary(self) -> str:
        tok = self.peek()
        if tok is None:
            self.c._add_issue(self.line_no,'ERROR','Empty expression')
            return 'unknown'
        u = tok.upper()
        # Parenthesized expression
        if tok == '(':
            self.advance()
            inner = self.parse_or()
            if self.peek() != ')':
                self.c._add_issue(self.line_no,'ERROR','Missing closing parenthesis in expression')
            else:
                self.advance()
            return inner
        # String literal
        if self.c._is_string(tok):
            self.advance(); return 'string'
        # Number literal
        if self.c._is_number(tok):
            self.advance(); return 'numeric'
        # Built-in constant PI
        if u == 'PI':
            self.advance(); return 'numeric'
        # Identifier / function / array
        if self.c._is_identifier(tok):
            name = tok.upper(); self.advance()
            # Array or function call if next token '('
            if self.peek() == '(':
                self.advance()  # consume '('
                args: List[str] = []
                if self.peek() == ')':
                    self.advance()
                else:
                    while True:
                        arg_type = self.parse_or()
                        args.append(arg_type)
                        if self.peek() == ',':
                            self.advance(); continue
                        elif self.peek() == ')':
                            self.advance(); break
                        else:
                            self.c._add_issue(self.line_no,'ERROR', 'Function/array call missing closing )')
                            break
                if name in FUNC_INFO:
                    ret_type, min_args, max_args = FUNC_INFO[name]
                    argc = len(args)
                    if argc < min_args or (max_args >= 0 and argc > max_args):
                        self.c._add_issue(self.line_no,'ERROR', f"{name} expects {min_args}-{max_args} args, got {argc}")
                    return ret_type
                else:
                    # Treat as array usage; no type change
                    return self.infer_var_type(name)
            # Plain variable
            return self.infer_var_type(name)
        # Fallback
        self.c._add_issue(self.line_no,'WARN', f"Unrecognized token '{tok}' in expression")
        self.advance()
        return 'unknown'

    def infer_var_type(self, name: str) -> str:
        # Derive type from suffix
        if name.endswith('$'): return 'string'
        if name.endswith('%'): return 'numeric'  # treat integer as numeric
        # Use recorded type if available
        return self.c.var_types.get(name,'numeric')

    def combine_types(self, left: str, right: str, op: str) -> str:
        # Logical ops expect numeric (boolean) operands; treat non-numeric as error
        if left != 'numeric' or right != 'numeric':
            self.c._add_issue(self.line_no,'ERROR', f"Operator {op} applied to non-numeric operand(s) {left}/{right}")
            return 'unknown'
        return 'numeric'


def check_file(path: str, return_structured: bool = False):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    sc = SyntaxChecker()
    # Allow env var override for reachability warnings
    import os
    if os.getenv('C64_NO_REACH') == '1':
        sc.enable_reachability_warnings = False
    reach_mode_env = os.getenv('C64_REACH_MODE')
    if reach_mode_env in ('strict','relaxed'):
        sc.reachability_mode = reach_mode_env
    sc.load(text)
    sc.validate()
    if return_structured:
        return sc.structured()
    # Generate textual report (printed by default) and derive exit code for CLI usage
    sc.report(print_errors=True)
    errors = sum(1 for i in sc.issues if i.severity == 'ERROR')
    return 1 if errors else 0


def check_source(source: str, return_structured: bool = False, print_errors: bool = True, return_warnings: bool = True) -> str | Dict[str, object]:
    """Validate C64 BASIC source provided directly as a string.

    This now returns a textual report when `return_structured` is False instead
    of an integer exit code, allowing callers to capture and display the
    results programmatically.

    Environment variable overrides still apply:
      C64_NO_REACH=1      -> disable reachability warnings
      C64_REACH_MODE=...  -> 'strict' | 'relaxed'

    Args:
        source: Full BASIC program text with line-numbered lines.
        return_structured: If True, returns structured dict (issues + summary).
        print_errors: If True, also prints the textual report to stdout.

    Returns:
        str: Multiline textual report (when return_structured=False)
        dict: Structured issues + summary (when return_structured=True)
    """
    sc = SyntaxChecker()
    import os
    if os.getenv('C64_NO_REACH') == '1':
        sc.enable_reachability_warnings = False
    reach_mode_env = os.getenv('C64_REACH_MODE')
    if reach_mode_env in ('strict','relaxed'):
        sc.reachability_mode = reach_mode_env
    sc.load(source)
    sc.validate()
    if return_structured:
        return sc.structured()
    report_text = sc.report(print_errors=print_errors, return_warnings=return_warnings)
    return report_text


def main(argv: List[str]):
    if len(argv) < 2:
        print("Usage: python c64_syntax_checker.py <file.bas> [--no-reach] [--reach=strict|relaxed] [--json]")
        sys.exit(2)
    path = argv[1]
    args = argv[2:]
    no_reach = '--no-reach' in args
    reach_arg = next((a for a in args if a.startswith('--reach=')), None)
    want_json = '--json' in args
    if want_json:
        data = check_file(path, return_structured=True)
        print(json.dumps(data, indent=2))
        errors = data['summary']['errors']
        sys.exit(1 if errors else 0)
    else:
        rc = check_file(path)
        sys.exit(rc)

if __name__ == '__main__':
    main(sys.argv)
