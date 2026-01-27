from datetime import datetime
import logging
import os

import sys
from pathlib import Path

logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent))

from utils.bas2prg import Bas2Prg

def get_message_content(content):
    """
    Extracts text content from a message which may contain text and other elements.
    """
    if len(content) == 0:
        return
    if isinstance(content, list):
        message = content[0]
    else:
        message = content
    if isinstance(message, str):
        return message
    elif isinstance(message, dict):
        return message.get("text", "")
    return str(message)   

def read_example_programs(num_examples: int = 5, folder: str = "resources/c64basic") -> str:
    # Only read the *.bas files from the folder and not the subfolders
    examples = []
    example_files = [f for f in os.listdir(folder) if f.endswith(".bas") and os.path.isfile(os.path.join(folder, f))]
    for i, filename in enumerate(example_files):
        if i >= num_examples:
            break
        with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
            content = f.read()
            examples.append(f"```basic\n{content}\n```")
            logger.info(f"Loaded example program from {filename}")
    return "\n\n".join(examples)

def convert_c64_bas_to_prg(bas_code: str, write_to_file: bool = True, xcbasic3_mode = False) -> (tuple[str, bytes, str]):
    prg_file_path = None

    if xcbasic3_mode:

        current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_bas_path = os.path.join("output", f"tmp_{current_timestamp}.bas")
        with open(temp_bas_path, "w") as temp_bas_file:
            temp_bas_file.write(bas_code)

        prg_file_path = os.path.join("output", f"tmp_{current_timestamp}.prg")

        import subprocess
        result = subprocess.run(['xcbasic3', temp_bas_path, prg_file_path], capture_output=True, text=True)
        conversion_output = ''

        if result.returncode != 0:
            #print("Stderr:", result.stderr)
            # Handle the following 2 types of error messages:
            # tmp_20260127105302.bas:2.5: syntax error near 'A Data-Sca' in file tmp_20260127105302.bas in line 2
            # tmp_20260127105249.bas:13.0: ERROR: Variable "k$" does not exist or is unknown in this scope
            # Note: the stderr may contain multiple lines of errors, so first strip and then process line by line

            err_output = result.stderr.strip()
            err_output_lines = err_output.split('\n')
            # Process all lines and combine them into one error message
            err_output = ''
            for line in err_output_lines:
                if ':' in line:
                    # Skip lines containing "NOTICE:"
                    if 'NOTICE:' in line:
                        continue
                    err_parts = line.split(':', 2)
                    if len(err_parts) >= 3:
                        line_info = err_parts[1].strip()
                        error_message = err_parts[2].strip()
                        # Remove the in file ... part if present
                        if ' in file ' in error_message:
                            error_message = error_message.split(' in file ')[0].strip()

                        # Keep only the line number, no need for the .5 part
                        if '.' in line_info:
                            line_info = line_info.split('.')[0]
                        err_output += f"Line {line_info}: {error_message}\n"
            err_output = err_output.strip()
            

            conversion_output = 'Error in source code:\n' + err_output
            return prg_file_path, b'', conversion_output
        else:
            conversion_output = 'Successfully converted source code to PRG file.'
            # Read the generated PRG file
            with open(prg_file_path, "rb") as prg_file:
                prg_data = prg_file.read()
        
            return prg_file_path, prg_data, conversion_output

    else:

        converter = Bas2Prg()
        prg_data = converter.convert(source_text=bas_code)

        if write_to_file:
            current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            prg_file_path = os.path.join("output", f"tmp_{current_timestamp}.prg")
            with open(prg_file_path, "wb") as prg_file:
                prg_file.write(prg_data)

        return prg_file_path, prg_data, "Successfully converted source code to PRG file."

def format_llm_error_message(model_name: str, error_str: str) -> str:
    # Handle common error types and provide friendly English error messages
    if "RateLimitError" in error_str or "429" in error_str:
        if "quota" in error_str.lower() or "exceed" in error_str.lower():
            return f"⚠️ {model_name} API quota exceeded. Please check your plan and billing details."
        else:
            return f"⚠️ {model_name} API rate limit hit. Please try again later."
    elif "401" in error_str or "authentication" in error_str.lower():
        return f"🔑 {model_name} API key is invalid. Please check your configuration."
    elif "403" in error_str or "permission" in error_str.lower():
        return f"🚫 {model_name} API access denied. Please check permissions."
    elif "timeout" in error_str.lower():
        return f"⏰ {model_name} API call timed out. Please retry."
    else:
        return f"❌ {model_name} model call failed: {error_str}"

if __name__ == "__main__":
    source_code = """1 REM Cyber-Serpent 64
2 REM A Data-Scavenger internal program
3 GOSUB init_system
4 
5 main_menu:
6 GOSUB clear_screen
7 TEXTAT 12, 5, "CYBER-SERPENT 64", 7
8 TEXTAT 10, 10, "DATA-SCAVENGER MODE", 1
9 TEXTAT 11, 14, "CONTROLS: WASD", 3
10 TEXTAT 12, 16, "IJKM WORKS TOO", 3
11 TEXTAT 9, 20, "PRESS FIRE OR SPACE", 1
12 wait_start:
13 GET k$ : IF k$ <> " " AND JOY(2) AND 16 = 0 THEN GOTO wait_start
14 
15 gameplay_init:
16 DIM snake_x(255) AS BYTE
17 DIM snake_y(255) AS BYTE
18 DIM snake_len AS BYTE : snake_len = 3
19 DIM head_x AS BYTE : head_x = 20
20 DIM head_y AS BYTE : head_y = 12
21 DIM dir_x AS INT : dir_x = 1
22 DIM dir_y AS INT : dir_y = 0
23 DIM score AS DECIMAL : score = 0000d
24 DIM food_x AS BYTE
25 DIM food_y AS BYTE
26 DIM game_speed AS BYTE : game_speed = 10
27 DIM frame_count AS BYTE : frame_count = 0
28 RANDOMIZE TI()
29 GOSUB clear_screen
30 GOSUB draw_border
31 GOSUB spawn_food
32 
33 FOR i AS BYTE = 0 TO snake_len
34   snake_x(i) = head_x - snake_len + i
35   snake_y(i) = head_y
36 NEXT
37 
38 game_loop:
39 frame_count = frame_count + 1
40 GOSUB read_keyboard
41 IF frame_count < game_speed THEN GOTO game_loop
42 frame_count = 0
43 
44 REM Move snake
45 old_tail_x = snake_x(0)
46 old_tail_y = snake_y(0)
47 POKE 1024 + old_tail_x + (old_tail_y * 40), 32
48 
49 FOR i AS BYTE = 0 TO snake_len - 1
50   snake_x(i) = snake_x(i + 1)
51   snake_y(i) = snake_y(i + 1)
52 NEXT
53 
54 head_x = head_x + CAST(dir_x)
55 head_y = head_y + CAST(dir_y)
56 snake_x(snake_len) = head_x
57 snake_y(snake_len) = head_y
58 
59 REM Collision detection
60 IF head_x = 0 OR head_x = 39 OR head_y = 0 OR head_y = 24 THEN GOTO death
61 char_at_head = PEEK(1024 + head_x + (head_y * 40))
62 IF char_at_head = 81 THEN GOTO death
63 
64 REM Eat food
65 IF head_x = food_x AND head_y = food_y THEN GOSUB eat_data
66 
67 REM Draw snake
68 FOR i AS BYTE = 0 TO snake_len
69   char = 81 : IF i = snake_len THEN char = 87
70   POKE 1024 + snake_x(i) + (snake_y(i) * 40), char
71   POKE 55296 + snake_x(i) + (snake_y(i) * 40), 5
72 NEXT
73 
74 TEXTAT 2, 0, "DATA PACKETS:", 1
75 TEXTAT 16, 0, score, 7
76 GOTO game_loop
77 
78 eat_data:
79 GOSUB sound_beep
80 score = score + 0001d
81 snake_len = snake_len + 1
82 snake_x(snake_len) = head_x
83 snake_y(snake_len) = head_y
84 IF game_speed > 2 THEN game_speed = game_speed - 1
85 GOSUB spawn_food
86 RETURN
87 
88 spawn_food:
89 food_x = (RNDB() MOD 38) + 1
90 food_y = (RNDB() MOD 23) + 1
91 IF PEEK(1024 + food_x + (food_y * 40)) <> 32 THEN GOTO spawn_food
92 POKE 1024 + food_x + (food_y * 40), 90
93 POKE 55296 + food_x + (food_y * 40), 2
94 RETURN
95 
96 death:
97 GOSUB sound_noise
98 FOR i AS BYTE = 0 TO 10 : FOR j AS BYTE = 0 TO 250 : NEXT : NEXT
99 TEXTAT 15, 12, "MAINFRAME CRASH", 2
100 TEXTAT 13, 14, "PRESS ANY KEY", 1
101 flush:
102 GET k$ : IF k$ <> "" THEN GOTO flush
103 wait_key:
104 GET k$ : IF k$ = "" THEN GOTO wait_key
105 GOTO main_menu
106 
107 read_keyboard:
108 GET k$
109 IF k$ = "w" OR k$ = "i" THEN IF dir_y <> 1 THEN dir_x = 0 : dir_y = -1
110 IF k$ = "s" OR k$ = "k" OR k$ = "m" THEN IF dir_y <> -1 THEN dir_x = 0 : dir_y = 1
111 IF k$ = "a" OR k$ = "j" THEN IF dir_x <> 1 THEN dir_x = -1 : dir_y = 0
112 IF k$ = "d" OR k$ = "l" THEN IF dir_x <> -1 THEN dir_x = 1 : dir_y = 0
113 RETURN
114 
115 init_system:
116 POKE 53280, 0 : POKE 53281, 0
117 VOLUME 15
118 VOICE 1 ADSR 0, 9, 15, 5
119 RETURN
120 
121 clear_screen:
122 SYS 65490 FAST
123 RETURN
124 
125 draw_border:
126 FOR x AS BYTE = 0 TO 39
127   POKE 1024 + x, 160 : POKE 1024 + x + 960, 160
128   POKE 55296 + x, 6 : POKE 55296 + x + 960, 6
129 NEXT
130 FOR y AS BYTE = 0 TO 24
131   POKE 1024 + (y * 40), 160 : POKE 1024 + 39 + (y * 40), 160
132   POKE 55296 + (y * 40), 6 : POKE 55296 + 39 + (y * 40), 6
133 NEXT
134 RETURN
135 
136 sound_beep:
137 VOICE 1 WAVE TRI TONE 4000 ON
138 FOR t AS BYTE = 0 TO 50 : NEXT
139 VOICE 1 OFF
140 RETURN
141 
142 sound_noise:
143 VOICE 1 WAVE NOISE TONE 1000 ON
144 FOR t AS BYTE = 0 TO 200 : NEXT
145 VOICE 1 OFF
146 RETURN
147 
148 REM ==============================
149 REM CREATED USING VIBEC64 IN XC=BASIC
150 REM GITHUB.COM/BBENCE84/VIBEC64
"""

    source_code = """REM Cyber-Serpent 64
REM A Data-Scavenger internal program

DIM k$ AS STRING * 16

GOSUB init_system

main_menu:
GOSUB clear_screen
TEXTAT 12, 5, "CYBER-SERPENT 64", 7
TEXTAT 10, 10, "DATA-SCAVENGER MODE", 1
TEXTAT 11, 14, "CONTROLS: WASD", 3
TEXTAT 12, 16, "IJKM WORKS TOO", 3
TEXTAT 9, 20, "PRESS FIRE OR SPACE", 1
wait_start:
GET k$ : IF k$ <> " " AND JOY(2) AND 16 = 0 THEN GOTO wait_start

gameplay_init:
DIM snake_x(255) AS BYTE
DIM snake_y(255) AS BYTE
DIM snake_len AS BYTE : snake_len = 3
DIM head_x AS BYTE : head_x = 20
DIM head_y AS BYTE : head_y = 12
DIM dir_x AS INT : dir_x = 1
DIM dir_y AS INT : dir_y = 0
DIM score AS DECIMAL : score = 0000d
DIM food_x AS BYTE
DIM food_y AS BYTE
DIM game_speed AS BYTE : game_speed = 10
DIM frame_count AS BYTE : frame_count = 0
RANDOMIZE TI()
GOSUB clear_screen
GOSUB draw_border
GOSUB spawn_food

FOR i AS BYTE = 0 TO snake_len
  snake_x(i) = head_x - snake_len + i
  snake_y(i) = head_y
NEXT

game_loop:
frame_count = frame_count + 1
GOSUB read_keyboard
IF frame_count < game_speed THEN GOTO game_loop
frame_count = 0

REM Move snake
old_tail_x = snake_x(0)
old_tail_y = snake_y(0)
POKE 1024 + old_tail_x + (old_tail_y * 40), 32

FOR i AS BYTE = 0 TO snake_len - 1
  snake_x(i) = snake_x(i + 1)
  snake_y(i) = snake_y(i + 1)
NEXT

head_x = head_x + CAST(dir_x)
head_y = head_y + CAST(dir_y)
snake_x(snake_len) = head_x
snake_y(snake_len) = head_y

REM Collision detection
IF head_x = 0 OR head_x = 39 OR head_y = 0 OR head_y = 24 THEN GOTO death
char_at_head = PEEK(1024 + head_x + (head_y * 40))
IF char_at_head = 81 THEN GOTO death

REM Eat food
IF head_x = food_x AND head_y = food_y THEN GOSUB eat_data

REM Draw snake
FOR i AS BYTE = 0 TO snake_len
  char = 81 : IF i = snake_len THEN char = 87
  POKE 1024 + snake_x(i) + (snake_y(i) * 40), char
  POKE 55296 + snake_x(i) + (snake_y(i) * 40), 5
NEXT

TEXTAT 2, 0, "DATA PACKETS:", 1
TEXTAT 16, 0, score, 7
GOTO game_loop

eat_data:
GOSUB sound_beep
score = score + 0001d
snake_len = snake_len + 1
snake_x(snake_len) = head_x
snake_y(snake_len) = head_y
IF game_speed > 2 THEN game_speed = game_speed - 1
GOSUB spawn_food
RETURN

spawn_food:
food_x = (RNDB() MOD 38) + 1
food_y = (RNDB() MOD 23) + 1
IF PEEK(1024 + food_x + (food_y * 40)) <> 32 THEN GOTO spawn_food
POKE 1024 + food_x + (food_y * 40), 90
POKE 55296 + food_x + (food_y * 40), 2
RETURN

death:
GOSUB sound_noise
FOR i AS BYTE = 0 TO 10 : FOR j AS BYTE = 0 TO 250 : NEXT : NEXT
TEXTAT 15, 12, "MAINFRAME CRASH", 2
TEXTAT 13, 14, "PRESS ANY KEY", 1
flush:
GET k$ : IF k$ <> "" THEN GOTO flush
wait_key:
GET k$ : IF k$ = "" THEN GOTO wait_key
GOTO main_menu

read_keyboard:
GET k$
IF k$ = "w" OR k$ = "i" THEN IF dir_y <> 1 THEN dir_x = 0 : dir_y = -1
IF k$ = "s" OR k$ = "k" OR k$ = "m" THEN IF dir_y <> -1 THEN dir_x = 0 : dir_y = 1
IF k$ = "a" OR k$ = "j" THEN IF dir_x <> 1 THEN dir_x = -1 : dir_y = 0
IF k$ = "d" OR k$ = "l" THEN IF dir_x <> -1 THEN dir_x = 1 : dir_y = 0
RETURN

init_system:
POKE 53280, 0 : POKE 53281, 0
VOLUME 15
VOICE 1 ADSR 0, 9, 15, 5
RETURN

clear_screen:
SYS 65490 FAST
RETURN

draw_border:
FOR x AS BYTE = 0 TO 39
  POKE 1024 + x, 160 : POKE 1024 + x + 960, 160
  POKE 55296 + x, 6 : POKE 55296 + x + 960, 6
NEXT
FOR y AS BYTE = 0 TO 24
  POKE 1024 + (y * 40), 160 : POKE 1024 + 39 + (y * 40), 160
  POKE 55296 + (y * 40), 6 : POKE 55296 + 39 + (y * 40), 6
NEXT
RETURN

sound_beep:
VOICE 1 WAVE TRI TONE 4000 ON
FOR t AS BYTE = 0 TO 50 : NEXT
VOICE 1 OFF
RETURN

sound_noise:
VOICE 1 WAVE NOISE TONE 1000 ON
FOR t AS BYTE = 0 TO 200 : NEXT
VOICE 1 OFF
RETURN

REM ==============================
REM CREATED USING VIBEC64 IN XC=BASIC
REM GITHUB.COM/BBENCE84/VIBEC64 """

    source_code = """DIM FAST room_id AS BYTE
DIM game_running AS BYTE
DIM basket_held AS BYTE
DIM sandwiches_held AS BYTE
DIM ball_held AS BYTE
DIM treat_held AS BYTE
DIM blanket_held AS BYTE
DIM pip_happy AS BYTE
DIM dog_happy AS BYTE
DIM robin_ready AS BYTE
DIM command$ AS STRING * 32
DIM verb$ AS STRING * 10
DIM noun$ AS STRING * 20

CONST RM_KITCHEN = 1
CONST RM_HALLWAY = 2
CONST RM_LIVING  = 3
CONST RM_BEDROOM = 4
CONST RM_GARDEN  = 5

SUB cls() STATIC
    PRINT "{CLR}"
END SUB

SUB show_intro() STATIC
    CALL cls()
    PRINT "--- THE PERFECT PICNIC ---"
    PRINT "A SUNNY SATURDAY MORNING AT HOME."
    PRINT "FIND THE ITEMS AND GATHER EVERYONE"
    PRINT "IN THE GARDEN FOR A PICNIC."
    PRINT "COMMANDS: GO N, S, E, W, GET, LOOK, GIVE, INV"
    PRINT "--------------------------"
END SUB

SUB describe_room() STATIC
    CALL cls()
    SELECT CASE room_id
        CASE RM_KITCHEN
            PRINT "YOU ARE IN THE KITCHEN."
            PRINT "ROBIN IS HERE PACKING BOXES."
            PRINT "EXITS: NORTH (HALLWAY)"
            IF basket_held = 0 THEN PRINT "YOU SEE A BASKET HERE."
            IF treat_held = 0 THEN PRINT "THERE IS A DOG TREAT ON THE COUNTER."
            IF sandwiches_held = 0 THEN PRINT "FRESH SANDWICHES ARE SITTING HERE."
        CASE RM_HALLWAY
            PRINT "YOU ARE IN THE LONG HALLWAY."
            IF dog_happy = 0 THEN
                PRINT "BARNABY THE DOG IS BARKING LOUDLY,"
                PRINT "BLOCKING THE WAY TO THE BEDROOM!"
            ELSE
                PRINT "BARNABY IS CALMLY CHEWING A TREAT."
            END IF
            PRINT "EXITS: NORTH (GARDEN), SOUTH (KITCHEN),"
            PRINT "WEST (LIVING ROOM), EAST (BEDROOM)."
        CASE RM_LIVING
            PRINT "THE LIVING ROOM IS COZY."
            PRINT "PIP IS SITTING ON THE RUG, LOOKING BORED."
            IF ball_held = 0 THEN PRINT "A COLORFUL BALL LIES UNDER THE CHAIR."
            PRINT "EXITS: EAST (HALLWAY)"
        CASE RM_BEDROOM
            PRINT "THE SUN STREAMS INTO THE BEDROOM."
            IF blanket_held = 0 THEN PRINT "A PICNIC BLANKET IS ON THE BED."
            PRINT "EXITS: WEST (HALLWAY)"
        CASE RM_GARDEN
            PRINT "THE GARDEN IS LUSH AND GREEN."
            PRINT "THE PERFECT SPOT FOR A PICNIC!"
            PRINT "EXITS: SOUTH (HALLWAY)"
    END SELECT
END SUB

FUNCTION check_win AS BYTE () STATIC
    IF room_id <> RM_GARDEN THEN RETURN 0
    IF basket_held = 0 OR sandwiches_held = 0 OR blanket_held = 0 THEN RETURN 0
    IF pip_happy = 0 OR robin_ready = 0 THEN RETURN 0
    RETURN 1
END FUNCTION

SUB parse_input() STATIC
    DIM p AS BYTE
    verb$ = "" : noun$ = ""
    p = INSTR(command$, " ")
    IF p = 0 THEN
        verb$ = command$
    ELSE
        verb$ = LEFT(command$, p - 1)
        noun$ = RIGHT(command$, LEN(command$) - p)
    END IF
END SUB

room_id = RM_KITCHEN
game_running = 1
basket_held = 0
sandwiches_held = 0
ball_held = 0
treat_held = 0
blanket_held = 0
pip_happy = 0
dog_happy = 0
robin_ready = 0

CALL show_intro()

DO 
    IF check_win() THEN
        PRINT ""
        PRINT "CONGRATULATIONS!"
        PRINT "EVERYONE IS IN THE GARDEN. THE FOOD"
        PRINT "IS SPREAD OUT ON THE BLANKET."
        PRINT "YOU HAVE ORGANIZED THE PERFECT PICNIC!"
        game_running = 0
        EXIT DO
    END IF

    CALL describe_room()
    PRINT ""
    INPUT "> "; command$
    CALL parse_input()

    IF verb$ = "GO" THEN
        IF noun$ = "N" THEN
            IF room_id = RM_KITCHEN THEN room_id = RM_HALLWAY : GOTO next_loop
            IF room_id = RM_HALLWAY THEN
                IF sandwiches_held = 1 AND blanket_held = 1 THEN
                    robin_ready = 1
                    room_id = RM_GARDEN
                ELSE
                    PRINT "ROBIN SAYS: WE AREN'T READY YET!"
                    WAIT 198, 1
                END IF
                GOTO next_loop
            END IF
            PRINT "CAN'T GO THAT WAY." : WAIT 198, 1
        ELSEIF noun$ = "S" THEN
            IF room_id = RM_HALLWAY THEN room_id = RM_KITCHEN : GOTO next_loop
            IF room_id = RM_GARDEN THEN room_id = RM_HALLWAY : GOTO next_loop
            PRINT "CAN'T GO THAT WAY." : WAIT 198, 1
        ELSEIF noun$ = "E" THEN
            IF room_id = RM_HALLWAY THEN
                IF dog_happy = 1 THEN
                    room_id = RM_BEDROOM
                ELSE
                    PRINT "BARNABY WON'T LET YOU PASS!"
                    WAIT 198, 1
                END IF
                GOTO next_loop
            END IF
            PRINT "CAN'T GO THAT WAY." : WAIT 198, 1
        ELSEIF noun$ = "W" THEN
            IF room_id = RM_HALLWAY THEN room_id = RM_LIVING : GOTO next_loop
            IF room_id = RM_BEDROOM THEN room_id = RM_HALLWAY : GOTO next_loop
            PRINT "CAN'T GO THAT WAY." : WAIT 198, 1
        END IF

    ELSEIF verb$ = "GET" THEN
        IF noun$ = "BASKET" AND room_id = RM_KITCHEN AND basket_held = 0 THEN
            basket_held = 1 : PRINT "TAKEN." : WAIT 198, 1
        ELSEIF noun$ = "SANDWICHES" AND room_id = RM_KITCHEN AND sandwiches_held = 0 THEN
            IF basket_held = 1 THEN
                sandwiches_held = 1 : PRINT "YOU PACK THE SANDWICHES IN THE BASKET." : WAIT 198, 1
            ELSE
                PRINT "YOU NEED THE BASKET FIRST." : WAIT 198, 1
            END IF
        ELSEIF noun$ = "TREAT" AND room_id = RM_KITCHEN AND treat_held = 0 THEN
            treat_held = 1 : PRINT "TAKEN." : WAIT 198, 1
        ELSEIF noun$ = "BALL" AND room_id = RM_LIVING AND ball_held = 0 THEN
            ball_held = 1 : PRINT "TAKEN." : WAIT 198, 1
        ELSEIF noun$ = "BLANKET" AND room_id = RM_BEDROOM AND blanket_held = 0 THEN
            blanket_held = 1 : PRINT "TAKEN." : WAIT 198, 1
        ELSE
            PRINT "I DON'T SEE THAT HERE." : WAIT 198, 1
        END IF

    ELSEIF verb$ = "GIVE" THEN
        IF noun$ = "TREAT" AND treat_held = 1 AND room_id = RM_HALLWAY THEN
            treat_held = 2 : dog_happy = 1 : PRINT "BARNABY CALMS DOWN AND EATS THE TREAT." : WAIT 198, 1
        ELSEIF noun$ = "BALL" AND ball_held = 1 AND room_id = RM_LIVING THEN
            ball_held = 2 : pip_happy = 1 : PRINT "PIP IS THRILLED! PIP FOLLOWS YOU TO THE GARDEN." : WAIT 198, 1
        ELSE
            PRINT "NOTHING HAPPENS." : WAIT 198, 1
        END IF

    ELSEIF verb$ = "LOOK" THEN
        GOTO next_loop

    ELSEIF verb$ = "INV" THEN
        PRINT "YOU HAVE:"
        IF basket_held = 1 THEN PRINT "- BASKET"
        IF sandwiches_held = 1 THEN PRINT "- SANDWICHES"
        IF ball_held = 1 THEN PRINT "- BALL"
        IF treat_held = 1 THEN PRINT "- TREAT"
        IF blanket_held = 1 THEN PRINT "- BLANKET"
        IF basket_held=0 AND sandwiches_held=0 AND ball_held=0 AND treat_held=0 AND blanket_held=0 THEN PRINT "NOTHING."
        WAIT 198, 1

    ELSE
        PRINT "UNKNOWN COMMAND." : WAIT 198, 1
    END IF

    next_loop:
LOOP WHILE game_running = 1

END

"""

    prg_file_path, prg_data, conversion_output = convert_c64_bas_to_prg(source_code, xcbasic3_mode=True)
    print(conversion_output)
# #     #hardware_access = C64HardwareAccess(device_port="COM3", baud_rate=19200, debug=False)
# #     send_prg_to_c64("""C:\output\guessing_game.prg""")