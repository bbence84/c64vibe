import struct
import argparse
import sys
import re

# Exact token list from tokens.c
# Indices 0-127 correspond to bytes 0x80-0xFF
TOKENS = [
    "END",      "FOR",      "NEXT",     "DATA",     "INPUT#",   "INPUT",    "DIM",      "READ",
    "LET",      "GOTO",     "RUN",      "IF",       "RESTORE",  "GOSUB",    "RETURN",   "REM",
    "STOP",     "ON",       "WAIT",     "LOAD",     "SAVE",     "VERIFY",   "DEF",      "POKE",
    "PRINT#",   "PRINT",    "CONT",     "LIST",     "CLR",      "CMD",      "SYS",      "OPEN",
    "CLOSE",    "GET",      "NEW",      "TAB(",     "TO",       "FN",       "SPC(",     "THEN",
    "NOT",      "STEP",     "+",        "-",        "*",        "/",        "^",        "AND",
    "OR",       ">",        "=",        "<",        "SGN",      "INT",      "ABS",      "USR",
    "FRE",      "POS",      "SQR",      "RND",      "LOG",      "EXP",      "COS",      "SIN",
    "TAN",      "ATN",      "PEEK",     "LEN",      "STR$",     "VAL",      "ASC",      "CHR$",
    "LEFT$",    "RIGHT$",   "MID$",     "GO",       "{cc}",     "{cd}",     "{ce}",     "{cf}",
    "{d0}",     "{d1}",     "{d2}",     "{d3}",     "{d4}",     "{d5}",     "{d6}",     "{d7}",
    "{d8}",     "{d9}",     "{da}",     "{db}",     "{dc}",     "{dd}",     "{de}",     "{df}",
    "{e0}",     "{e1}",     "{e2}",     "{e3}",     "{e4}",     "{e5}",     "{e6}",     "{e7}",
    "{e8}",     "{e9}",     "{ea}",     "{eb}",     "{ec}",     "{ed}",     "{ee}",     "{ef}",
    "{f0}",     "{f1}",     "{f2}",     "{f3}",     "{f4}",     "{f5}",     "{f6}",     "{f7}",
    "{f8}",     "{f9}",     "{fa}",     "{fb}",     "{fc}",     "{fd}",     "{fe}",     "{pi}"
]

class Bas2Prg:
    def __init__(self, start_addr=0x0801, invert_case=False, 
                 auto_number=False, trim_spaces=False, collapse_spaces=False):
        self.start_addr = start_addr
        self.invert_case = invert_case
        self.auto_number = auto_number
        self.trim_spaces = trim_spaces
        self.collapse_spaces = collapse_spaces
        self.last_line_num = -1

    def _get_token(self, text_slice):
        """
        Mimics C gettoken: checks if text starts with a token by iterating 
        the array from start to end. First match wins.
        Returns (token_val, length) or (None, 0).
        """
        for index, token_str in enumerate(TOKENS):
            # C code uses strncmp, which is equivalent to startswith in this context
            if text_slice.startswith(token_str):
                # The C code maps index 0 to 0x80 (128)
                return (index + 128), len(token_str)
        return None, 0

    def _tokenize_line(self, content):
        """
        Converts a line string into C64 byte tokens.
        """
        output = bytearray()
        i = 0
        length = len(content)
        quoted = False
        rem_mode = False
        
        # Token constants
        TOKEN_REM = 0x8F # Index 15 + 128

        while i < length:
            char = content[i]
            
            # C logic: collapsespaces checks !(rem || quoted)
            # It skips the character if it is whitespace.
            if self.collapse_spaces and not (rem_mode or quoted):
                if char.isspace():
                    i += 1
                    continue

            if char == '"':
                quoted = not quoted
            
            # C logic: attempt token match if not REM and not Quoted
            found_token = False
            if not rem_mode and not quoted:
                token_val, token_len = self._get_token(content[i:])
                if token_val is not None:
                    if token_val == TOKEN_REM:
                        rem_mode = True
                    output.append(token_val)
                    i += token_len
                    found_token = True
            
            if found_token:
                continue

            # Copy character if not tokenized
            # The C code explicitly skips '\r' but copies others.
            if char != '\r':
                # Map unicode char to single byte. 
                # If outside 0-255 range, replace with '?' (standard safety)
                val = ord(char)
                if val > 255: val = 63 
                output.append(val)
            
            i += 1

        # C Logic: C64 BASIC has a problem with zero-length lines
        if len(output) == 0:
            output.append(ord(' '))
            
        output.append(0) # Null terminator
        return output

    def convert(self, source_text):
        """
        Convert a string of BASIC source code to PRG bytes.
        """
        prg = bytearray()
        
        # 1. Write Start Address (Little Endian)
        current_addr = self.start_addr
        prg.extend(struct.pack('<H', current_addr))
        
        # The C code uses fgets, so we iterate lines.
        lines = source_text.splitlines()
        
        for raw_line in lines:
            if not raw_line:
                continue

            # Processing happens on a copy
            line = raw_line

            # Invert Case logic (C code processes this before number parsing)
            if self.invert_case:
                converted = []
                for c in line:
                    if c.isupper():
                        converted.append(c.lower())
                    elif c.islower():
                        converted.append(c.upper())
                    else:
                        converted.append(c)
                line = "".join(converted)

            # Parse Line Number
            # We look for leading digits.
            match = re.match(r'^\s*(\d+)?(.*)', line)
            if not match:
                # Should not happen with splitlines logic unless empty, handled above
                continue
                
            line_num_str = match.group(1)
            content_part = match.group(2)

            # Auto-number logic
            if not line_num_str:
                # C code: if autonumber is on, use last + 1.
                if self.auto_number:
                    linenum = self.last_line_num + 1
                    # C code prints to stderr: fprintf(stderr, "auto-numbering %li\n", linenum);
                else:
                    # C code: strtol returns 0 if no digits found.
                    linenum = 0
            else:
                linenum = int(line_num_str)

            # Range checks / warnings (logic mimics C code truncation)
            if linenum < 0: linenum = 0
            if linenum > 65535: linenum = 65535
            
            self.last_line_num = linenum

            # Trim spaces logic
            # C code trims from the END of the line, then from the start of the pointer `cp`.
            if self.trim_spaces:
                content_part = content_part.strip()

            # Tokenize content
            # The C code passes the pointer AFTER the line number to tokenize.
            tokenized_bytes = self._tokenize_line(content_part)
            
            # Calculate logic for linked list
            # Size = 2 (next addr) + 2 (line num) + content length (incl null)
            tok_len = len(tokenized_bytes)
            
            # The C code adds: startaddr += toklinelen + 4;
            next_addr = current_addr + tok_len + 4
            
            # Write Next Line Address
            prg.extend(struct.pack('<H', next_addr))
            
            # Write Line Number
            prg.extend(struct.pack('<H', linenum))
            
            # Write Content
            prg.extend(tokenized_bytes)
            
            # Update current address for next loop
            current_addr = next_addr

        # Write End of Program (Double Null: Link 00 00)
        prg.extend(struct.pack('<H', 0))
        
        return prg

# -----------------------------------------------------------------------------
# Command Line Interface
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convert C64 BASIC text file to PRG.")
    parser.add_argument('filename', nargs='?', help="Input filename (stdin if empty)")
    parser.add_argument('-o', '--output', help="Output filename")
    parser.add_argument('-a', '--autonumber', action='store_true', help="Auto-number lines if missing")
    parser.add_argument('-c', '--collapsespaces', action='store_true', help="Collapse spaces in non-quoted/rem sections")
    parser.add_argument('-i', '--invertcase', action='store_true', help="Invert case (Swap ASCII/PETSCII)")
    parser.add_argument('-s', '--startaddr', type=str, default="0x0801", help="Start address (default 0x0801)")
    parser.add_argument('-t', '--trimspaces', action='store_true', help="Trim spaces from beginning/end of lines")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug output")

    args = parser.parse_args()

    # Handle Start Address parsing
    s_addr = args.startaddr
    try:
        if s_addr.lower().startswith("0x"):
            start_addr = int(s_addr, 16)
        elif s_addr.startswith("$"):
            start_addr = int(s_addr[1:], 16)
        else:
            start_addr = int(s_addr)
    except ValueError:
        print(f"Invalid start address: {s_addr}", file=sys.stderr)
        sys.exit(1)

    if args.debug:
        print(f"Load address: ${start_addr:04X}", file=sys.stderr)

    # Input handling
    if args.filename:
        try:
            # Use 'latin-1' or 'utf-8'. Latin-1 preserves byte values better for generic binary text.
            with open(args.filename, 'r', encoding='utf-8', errors='replace') as f:
                source_text = f.read()
        except Exception as e:
            print(f"Error reading input: {e}", file=sys.stderr)
            sys.exit(3)
    else:
        source_text = sys.stdin.read()

    converter = Bas2Prg(
        start_addr=start_addr,
        invert_case=args.invertcase,
        auto_number=args.autonumber,
        trim_spaces=args.trimspaces,
        collapse_spaces=args.collapsespaces
    )

    prg_data = converter.convert(source_text)

    # Output handling
    if args.output:
        try:
            with open(args.output, 'wb') as f:
                f.write(prg_data)
        except Exception as e:
            print(f"Unable to create output '{args.output}': {e}", file=sys.stderr)
            sys.exit(2)
    else:
        # Write to stdout
        if sys.stdout.isatty():
            print("Binary data not written to terminal. Use -o or redirect output.", file=sys.stderr)
        else:
            sys.stdout.buffer.write(prg_data)

if __name__ == '__main__':
    main()