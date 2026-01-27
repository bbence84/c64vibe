# XC=BASIC3 Compact Reference

## General Syntax & Vocabulary
*   **Case:** Insensitive (`PRINT` = `print`).
*   **Whitespace:** Required between keywords/identifiers.
*   **Line Endings:** strict CR+LF (Windows) or LF (*nix).
*   **Separators:** Colon `:` separates statements on the same line.
*   **Line Splitting:** Underscore `_` at end of line splits logical line to physical lines.
*   **Comments:** Single quote `'` (comment to end of line). `REM` (needs `:` if following a statement).
*   **Identifiers:** Alphanumeric + `_`. Must start with alpha or `_`. Case insensitive. `$` suffix allowed but does not define type. No length limit.
*   **Reserved Keywords:** (Cannot be used as identifiers)
    `AND AS ASM BACKGROUND BORDER BYTE CALL CASE CHARAT CLOSE CONST CONTINUE DATA DECIMAL DECLARE DIM DO DOKE ELSE END ERR OR EXIT FAST FILTER FLOAT FOR FUNCTION GET GOSUB GOTO HSCROLL IF INCBIN INCLUDE INLINE INPUT INT INTERRUPT LET LOAD LOCATE LONG LOOP MEMCPY MEMSET MEMSHIFT MOD NEXT NOT OFF ON OPEN OPTION OR ORIGIN OVERLOAD POKE PRINT PRIVATE RANDOMIZE RASTER READ REM RETURN SAVE SCREEN SELECT SHARED SOUND SPRITE STATIC STEP STRING SUB SWAP SYS SYSTEM TEXTAT THEN TIMER TO TYPE UNTIL VMODE VOICE VOLUME VSCROLL WHILE WORD WRITE XOR`

## Data Types
*   **Primitives:**
    *   `BYTE`: 0 to 255 (1 byte).
    *   `INT`: -32,768 to 32,767 (2 bytes).
    *   `WORD`: 0 to 65,535 (Unsigned, 2 bytes). Address storage.
    *   `LONG`: -8,388,608 to 8,388,607 (3 bytes).
    *   `FLOAT`: 32-bit (24-bit mantissa, 8-bit exp). Low precision (6-7 digits). Slow.
    *   `DECIMAL`: 0 to 9999 (BCD, 2 bytes). Display only (no conversion overhead). Only supports `+` and `-`.
    *   `STRING`: Fixed length (1-97 bytes). PETSCII.
*   **Literals:**
    *   `FLOAT`: Must contain `.`. (`1.0`).
    *   `DECIMAL`: Suffix `d` (`99d`).
    *   `HEX`: Prefix `$` (`$FF`). Always unsigned (WORD).
    *   `BINARY`: Prefix `%` (`%1101`). Always unsigned (WORD).
    *   Inference: 0-255 -> BYTE; within INT range -> INT; within WORD range -> WORD; others -> LONG/FLOAT.
*   **Booleans:** False = 0; True > 0 (Relational operators return 255 for True).

## Variables & Constants
*   **Definition:** Statically typed. Must be defined (explicit or implicit). No initialization (garbage values).
*   **Explicit:** `DIM name AS type`.
*   **Implicit:** Inferred on assignment (e.g., `x = 5` infers BYTE). *Avoid to prevent truncation.*
*   **Strings:** `DIM name$ AS STRING * length` (Max length 96). `$` optional in name.
*   **Arrays:** `DIM name(d1, d2, d3) AS type`. Max 3 dims. 0-based indices. No bounds checking.
*   **Scope:**
    *   `SHARED`: Visible in all modules (files). `DIM SHARED ...`.
    *   `GLOBAL`: Visible in current module (including inside subs/funcs). Default for outer scope.
    *   `LOCAL`: Visible only inside SUB/FUNCTION. Default for inner scope.
*   **Fast Vars:** `DIM FAST name AS type` (Allocates to Zero Page).
*   **Constants:** `CONST name = value` (Compile-time replacement, no memory usage).
*   **Addresses:** `@variable` returns memory address (WORD).

## Operators
*   **Arithmetic:** `+`, `-`, `*`, `/`, `MOD`. Integer division truncates.
*   **Relational:** `=`, `<>`, `>`, `>=`, `<`, `<=`. Returns 255 (True) or 0 (False). String support: `=` and `<>` only.
*   **Logical:** `AND`, `OR`, `XOR`, `SHL`, `SHR`. (Bitwise on integers).
*   **Unary:** `@` (Address of), `-` (Negation), `NOT` (Bitwise invert).
*   **Precedence:**
    1.  `NOT`, `-` (unary)
    2.  `*`, `/`, `MOD`
    3.  `+`, `-`
    4.  Relational
    5.  Logical
*   **Promotion:** Mixed types promote to highest (BYTE < WORD < INT < LONG < FLOAT). DECIMAL only mixes with DECIMAL.

## Control Flow
*   **Conditional:**
    ```basic
    IF cond THEN
      stmts
    ELSE
      stmts
    END IF
    ```
    Single line: `IF cond THEN stmt:stmt [ELSE stmt:stmt]`
*   **Multi-Branch:** `ON index GOTO label0, label1...` (0-based index).
*   **Loops:**
    *   **FOR:**
        ```basic
        FOR var [AS type] = start TO end [STEP val]
          stmts
          [CONTINUE FOR]
          [EXIT FOR]
        NEXT [var]
        ```
    *   **DO:**
        ```basic
        DO [WHILE|UNTIL cond]
          stmts
          [CONTINUE DO]
          [EXIT DO]
        LOOP [WHILE|UNTIL cond]
        ```
*   **Jumps:** `GOTO label` / `GOSUB label` ... `RETURN`. Labels end with `:`.

## Subroutines
*   **Definition:**
    ```basic
    SUB name ([arg1 AS type, ...]) [STATIC|SHARED|OVERLOAD]
      stmts
      [EXIT SUB]
    END SUB
    ```
*   **Call:** `CALL name(args)`.
*   **Memory:** Dynamic (stack) by default. Recursion allowed.
*   **STATIC:** `SUB name(...) STATIC`. Arguments/Locals in fixed memory. Faster, no recursion.
*   **Scope:** `SHARED` makes SUB visible to other modules. `DECLARE SUB` used for forward declaration.
*   **Overloading:** Same name, different args. Use `OVERLOAD` keyword on variants.

## Functions
*   **Definition:**
    ```basic
    FUNCTION name AS type ([args]) [STATIC|SHARED]
      ...
      name = value  ' QBasic style return
      ' OR
      RETURN value  ' Immediate return
    END FUNCTION
    ```
*   **Usage:** Must return value. Called in expressions: `x = func()`.

## User-Defined Types (UDT)
*   **Definition:**
    ```basic
    TYPE TypeName
      field AS type
      field2 AS otherUDT
    END TYPE
    ```
*   **Constraints:** Max 64 bytes per instance. Arrays in fields not allowed.
*   **Access:** `var.field`.
*   **Methods:** SUB/FUNCTION defined inside TYPE. Use `THIS` to access instance fields. Methods do not add to instance size.

## Modules & Errors
*   **Modules:** `INCLUDE "filename.bas"`. No linker; compiler resolves imports recursively.
*   **Error Handling:**
    *   `ON ERROR GOTO label`.
    *   `ERR()` returns error code (0-255).
    *   `ERROR code` triggers error.
*   **Error Codes:**
    1: TOO MANY FILES, 2: FILE OPEN, 3: FILE NOT OPEN, 4: FILE NOT FOUND, 5: DEVICE NOT PRESENT, 6: NOT INPUT FILE, 7: NOT OUTPUT FILE, 8: MISSING FILENAME, 9: ILLEGAL DEVICE NUMBER, 10: DEVICE NOT READY, 11: OTHER READ ERROR, 14: ILLEGAL QUANTITY, 15: OVERFLOW, 20: DIVISION BY ZERO, 21: ILLEGAL DIRECT.

## Strings (Implementation Details)
*   **Memory:** 1 byte length + N bytes chars. Unused bytes undefined.
*   **Modifying:** `POKE @str + 1 + index, byte` (0-based char index).
*   **Concatenation:** `+`. Truncates if exceeds defined length.

## Example XCBASIC3 programs

```basic
rem ******************* Adventure Template******************************
rem *
rem * XC=BASIC V2 template for a text adventure, similar to: 
rem * https://github.com/gpowerf/CommodoreAdventureTemplate
rem * but with several enhacements
rem *
rem * This is not a full game, it is a template to create a game 
rem *
rem ********************************************************************

rem ************************* Global vars ******************************

let lc! = 0
const O! = 2
const fixtures! = 2
const inlen = 20

rem *** Map ***
dim l![4, 4]
l![0,0] = 255:l![0,1] = 2:l![0,2] = 255:l![0,3] = 1
l![1,0] = 255:l![1,1] = 255:l![1,2] = 0:l![1,3] = 255
l![2,0] = 0:l![2,1] = 255:l![2,2] = 255:l![2,3] = 255
l![3,0] = 255:l![3,1] = 255:l![3,2] = 255:l![3,3] = 255

rem *** Description of locations ***
dim d$[4]
d$[0] = "A city park. It is a bright day and you can see people enjoying the park."
d$[1] = "A corner shop. It seems to be stocked with all sorts of items."
d$[2] = "Your house is to the east."
d$[3] = "You are inside your tiny house, it is so small it is just one room."

rem *** Location of objects ***
dim obl![3]
obl![0] = 0  
obl![1] = 0 
obl![2] = 2 

rem *** Objects, description, locations ***
dim ob$[3, 2]
ob$[0,0]="candle":ob$[0,1]="An old red candle."
ob$[1,0]="bottle":ob$[1,1]="An empty milk bottle."
ob$[2,0]="key":ob$[2,1]="A shinny golden key."

dim ol![3]
ol![0] = 0:ol![1] = 0:ol![2] = 2

rem *** word 1 and 2 for handling commands ***
dim w1$
dim w2$

rem *** Interactive fixtures ***
dim sf$[3, 8]
sf$[0,0]="tv"  :sf$[0,1]="use"  :sf$[0,2]="use"   :sf$[0,3]=" There's a TV on a table."       			     :sf$[0,4]="an old CRT TV, it is switched off." :sf$[0,5]="the TV is now on."         :sf$[0,6]="you turned the TV off." :sf$[0,7]="you turned the TV on." 
sf$[1,0]="door":sf$[1,1]="open" :sf$[1,2]="close" :sf$[1,3]=" You can see the front door from here."	     :sf$[1,4]="a metal door, it is closed."        :sf$[1,5]="the door is now open."     :sf$[1,6]="you closed the door."   :sf$[1,7]="you opened the door."
sf$[2,0]="key" :sf$[2,1]="use"  :sf$[2,2]="use"   :sf$[2,3]=" There's a box under the table, it has a lock." :sf$[2,4]="a wooden box, it is closed."        :sf$[2,5]="the box is open and empty.":sf$[2,6]="you closed the box."    :sf$[2,7]="you closed the box."

rem *** Location and state ***
dim sfl![3,4]
sfl![0,0] = 3 :sfl![0,1] = 0:sfl![0,2] = 255: sfl![0,3] = 255
sfl![1,0] = 2 :sfl![1,1] = 0:sfl![1,2] = 0  : sfl![1,3] = 1
sfl![2,0] = 3 :sfl![2,1] = 0:sfl![2,2] = 255: sfl![2,3] = 255

rem ************************* procs & funcs ****************************

rem **************** Custom procs/code
rem *** This code needs to be created for individual games, it is not
rem *** generic

proc customcode(i!)
	if i! = 0 then \l![2,3]= 3: \l![3,2]=2 
	if i! = 1 then \l![2,3]= 255: \l![3,2]=255 
	if i! = 2 then rem do nothing
endproc

rem **************** Generic procs

rem *** save the ganme
proc savegame(i#)
	save "@0:gamesave", 8, i#, i# + 1
	print ferr()
endproc

rem *** load the ganme
proc loadgame(i#)
	load "gamesave", 8, i#
	print ferr()
endproc


rem *** flip bit 
fun flipbit!(i!)
	on i! goto case0, case1
	case0:
		return 1
	case1:
		return 0 
endfun

rem *** Look at surroundings ***
proc look(location!)
	
	rem *** print description
	print "{CR}{CR}";
	print \d$[location!];
	
	rem *** print fixture
		for i=0 to \fixtures!
		rem *** if you are in an interactive room
		if \sfl![i,0] = \lc! then print \sf$[i,3]
	next i

	rem *** print exirs
	print "{CR}{CR}Exits to the: ";
	if \l![\lc!,0] <> 255 then print "north ";
	if \l![\lc!,1] <> 255 then print "south ";
	if \l![\lc!,2] <> 255 then print "west ";
	if \l![\lc!,3] <> 255 then print "east ";
	
	rem ***look at objects***
	print "{CR}{CR}You can also see the following objects:"
	for i=0 to \O!
		if \obl![i]=\lc! then print \ob$[i,0];:print " ";
	next
	print "{CR}"
endproc

rem *** Separate words ***
rem *** output to globals vars w1 and w2
proc sepwords(str$, sep$)
	dim buffer![\inlen]
	b$ = @buffer!
	windex! = strpos!(str$, sep$)
	strncpy b$, str$, windex!
	\w1$ = b$
	\w2$ = str$ + windex! + 1 
endproc

rem *** Examine objects ***
proc examine(str$)
	print "{CR}" 
	for i=0 to \O!
		if \obl![i] = \lc! or \obl![i] = 255 then if strcmp(\ob$[i,0], str$) = 0 then print \ob$[i,1]:goto endp
	next
	rem *** go to examine static fixture
	print "you can't examine that"
	endp:
endproc

rem *** move around ***
proc walk(w1$, w2$, lc!)
	let nl! = 255
	if strcmp(w1$, "n") = 0  or strcmp(w2$, "north") = 0  then nl!=\l![lc!,0]
	if strcmp(w1$, "s") = 0  or strcmp(w2$, "south") = 0  then nl!=\l![lc!,1]
	if strcmp(w1$, "w") = 0  or strcmp(w2$, "west") = 0  then nl!=\l![lc!,2]
	if strcmp(w1$, "e") = 0  or strcmp(w2$, "east") = 0  then nl!=\l![lc!,3]
	if nl!=255 then print "{CR}{CR}you can't go that way"
	if nl!<>255 then \lc!=nl!:call look(\lc!)
endproc 

rem ***get object***
proc getobj(str$)
	print "{CR}"
	for i=0 to \O!
		if strcmp(\ob$[i,0], str$) = 0 and \obl![i]=\lc! then \obl![i] = 255:print "Got the ";:print str$: goto endp
	next
	print "I can't do that."
	endp:
endproc

rem ***drop object***
proc drpobj(str$)
	print "{CR}"
	for i=0 to \O!
		if strcmp(\ob$[i,0], str$) = 0 and \obl![i]=255 then \obl![i] = \lc!:print "Dropped the ";:print str$: goto endp
	next
	print "I can't do that."
	endp:
endproc

rem ***inventory***
proc inventory
	print "{CR}{CR}You have the the following items:{CR}"
	for i=0 to \O!
		if \obl![i]=255 then print \ob$[i,0];:print " ";
	next
	print "{CR}"
endproc

rem *** flip interactive fixtures ***
proc fix(vrb$, nun$)
	for i=0 to \fixtures!
		rem *** if you are in an interactive room
		if \sfl![i,0] = \lc! then goto secondcheck	
	next i
	print "{CR}{CR}you can't do that here.":goto endp
	secondcheck: 
	for i=0 to \fixtures!
		rem *** if word 2 is valid proceed 
		if strcmp(\sf$[i,0], nun$) = 0 then goto thirdstep
	next i
	print "{CR}{CR}there's another way.":goto endp
	thirdstep:
	
	rem *** now let's look at the verb
	rem print \sf$[i,1]: print "-": print \sf$[i,2]
	
	if strcmp(\sf$[i,1], \sf$[i,2]) = 0 then if strcmp(\sf$[i,1], vrb$) = 0 then if \sfl![0,1] = 0 then print "{CR}": print \sf$[i,5]: \sfl![i,1] = flipbit!(\sfl![i,1]): goto endp 
	if strcmp(\sf$[i,1], \sf$[i,2]) = 0 then if strcmp(\sf$[i,2], vrb$) = 0 then if \sfl![0,1] = 1 then print "{CR}": print \sf$[i,6]: \sfl![i,1] = flipbit!(\sfl![i,1]): goto endp 
	
	if strcmp(\sf$[i,1], vrb$) = 0 then print "{CR}": print \sf$[i,5]: \sfl![i,1] = flipbit!(\sfl![i,1]): call customcode(\sfl![i,2]): goto endp 
	if strcmp(\sf$[i,2], vrb$) = 0 then print "{CR}":print \sf$[i,6]: \sfl![i,1] = flipbit!(\sfl![i,1]): call customcode(\sfl![i,3])
	
	endp:
endproc

rem ********************************************************************

poke 53280,0:poke 53281,0  
print "{CLR}{GREEN}{LOWER_CASE}       *** Adventure Template ***"
print "{CR}Game start"
call look(lc!)

rem *** a buffer is needed to handle the input
dim buff![inlen]
command$ = @buff!

rem *** game loop ***
let quit! = 0
repeat
	print "{CR}>";
	input command$, cast!(inlen)
	call sepwords(command$, " ")
	if strcmp(w1$, "look") = 0 then call look(lc!)
	if strcmp(w1$, "examine") = 0 then call examine(w2$)
	if strcmp(w1$, "n") = 0 then call walk(w1$, w2$, lc!)
	if strcmp(w1$, "s") = 0 then call walk(w1$, w2$, lc!)
	if strcmp(w1$, "e") = 0 then call walk(w1$, w2$, lc!)
	if strcmp(w1$, "w") = 0 then call walk(w1$, w2$, lc!)
	if strcmp(w1$, "go") = 0 then call walk(w1$, w2$, lc!)
	if strcmp(w1$, "get") = 0 or strcmp(w1$, "take") = 0 then call getobj(w2$)
	if strcmp(w1$, "drop") = 0 then call drpobj(w2$)
	if strcmp(w1$, "inv") = 0 or strcmp(w1$, "inventory") = 0 then call inventory
	if strcmp(w1$, "save") = 0 then call savegame(@lc!)
	if strcmp(w1$, "load") = 0 then call loadgame(@lc!)
	if strcmp(w1$, "quit") = 0 then quit! = 1
	
	rem *** this part deals with interactive fixtures
	for i=0 to fixtures!
		rem *** if word 2 is valid proceed 
		if strcmp(sf$[i,0], w2$) = 0 then call fix(w1$, w2$):goto endloop
	next i
	endloop:
until quit! = 1
```