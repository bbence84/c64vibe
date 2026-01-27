====== Syntax ======

===== Vocabulary =====

The following reserved keywords form the basic vocabulary of the language. The keywords may be spelled with either upper or lower case letters, or a mix of both. Therefore ''PRINT'', ''print'' and ''Print'' are equivalent.

<html><tt>
AND AS ASM BACKGROUND BORDER BYTE CALL CASE CHARAT CLOSE CONST CONTINUE DATA DECIMAL DECLARE DIM DO DOKE ELSE END ERR
OR EXIT FAST FILTER FLOAT FOR FUNCTION GET GOSUB GOTO HSCROLL IF INCBIN INCLUDE INLINE INPUT INT INTERRUPT LET LOAD LOCATE LONG LOOP MEMCPY MEMSET MEMSHIFT MOD NEXT NOT OFF ON OPEN OPTION OR ORIGIN OVERLOAD POKE PRINT PRIVATE RANDOMIZE RASTER READ REM RETURN SAVE SCREEN SELECT SHARED SOUND SPRITE STATIC STEP STRING SUB SWAP SYS SYSTEM
 TEXTAT THEN TIMER TO TYPE UNTIL VMODE VOICE VOLUME VSCROLL WHILE WORD WRITE XOR
</tt></html>

<adm note>
In XC=BASIC (unlike CBM BASIC) you must separate keywords from each other or from other identifiers with at least one space. This will not impose any speed or size penalty on the compiled program.
</adm>
===== Identifiers =====

Identifiers are used to name constants, variables, labels, subs and functions in XC=BASIC. You may choose identifiers as you wish, following these rules:

  - The first character must be alphabetic or an underscore (''_'') character
  - The remaining characters must be alphabetic, numeric, or the underscore (''_'') character
  - The ''$'' sign may suffix the identifer, however it doesn't automatically mean that the identifier refers to a string.
  - Either upper or lower case alphabetic characters may be used. Both are considered equivalent. Therefore ''XYZ'' and ''xyz'' are considered the same identifier.
  - An identifer may not duplicate one of the reserved keywords in the basic vocabulary above.

Identifiers can be of any length. Unlike CBM BASIC, where only the first two characters are significant, in XC=BASIC all characters are significant. The length of your identifers will not affect the size of the compiled program. For this reason, you are advised to use descriptive identifiers that are easy to read.

===== Statements =====

Statements can be separated using the colon ('':'') character. The separator is not required if there's only one statement in one line. The following two code pieces will be compiled to the same exact executable.

  FOR i AS INT = 1 TO 5 : PRINT i : NEXT
  
  FOR i AS INT = 1 TO 5
    PRINT i
  NEXT

<adm warning>
XC=BASIC is strict when it comes to line ending. On Windows, it only interprets the CR+LF sequence ("\r\n") as line ending, while on *nix systems, the LF ("\n") character is recognized only. Make sure you convert your source files before you compile anything that was written in another OS.
</adm>

===== Comments =====

Anything after a single quote (''''') character, up until the end of the line is ignored during compilation.

  x = 5 ' Assigning the value 5 to the variable x

The [[REM]] statement also serves to add comments. However, it must be separated from other statements using the colon ('':'') character if it is on the same line. Anything following the REM keyword up until the end of the line is ignored.

  REM This is a comment
  PRINT x : REM Outputting the value of x


===== Whitespace =====

Whitespace (e.g. spaces and tabs) are required between identifiers and keywords to avoid confusion. You are encouraged to use indentation to make the program more readable:

  FOR i AS INT = 0 TO 10
    FOR j AS INT = 0 TO 10
      PRINT "row ", i, "column ", j
    NEXT j
  NEXT i

===== Labels and Line Numbers =====

Labels can be used to mark points in your code and are referenced by ''GOTO'' and ''GOSUB'' statements. Labels must be appended with a colon ('':'').

  GOSUB intro
  END
  
  intro:
  PRINT "welcome to my program"  
  RETURN

In later sections of this tutorial you will learn more about labels and how they can be useful in your program.

In addition to labels, you can use line numbers as well. Line numbers will be treated like labels by XC=BASIC. However, the following conditions apply:

  * Line numbers do not have to be consecutive
  * The colon ('':'') character must not be appended to line numbers
  * Labels, line numbers or unnumbered/unlabeled lines can be mixed in the program

===== Splitting long lines =====

Starting from [v3.1], the ''_'' (underscore) character can be used to split a logical line to multiple physical lines.

  ' The following is a single command split into
  ' multiple lines for better readability
  SPRITE 2 _
    SHAPE 3 _
    ON _
    AT 50, 50 _
    MULTI _
    UNDER BACKGROUND

<- installation_and_usage|Previous page  ^ syntax|Syntax  ^ datatypes|Next page ->
====== Data Types ======

XC=BASIC offers 7 built-in data types (also called //primitive types//):

^Type   ^Numeric range                                        ^Size in bytes^
|BYTE   |0 to 255                                             | 1          |
|INT |-32,768 to 32,767                                    | 2          |
|WORD   |0 to 65,535                                          | 2          |
|LONG   |-8,388,608 to 8,388,607                              | 3          |
|FLOAT  |±2.93874⨉10<sup>-39</sup> to ±1.69477⨉10<sup>38</sup>| 4          |
|DECIMAL|0 to 9999                                            | 2          |
|STRING |N/A                                                  |1-97       |

===== Numeric types =====

  * BYTE is the smallest and fastest numeric type. Bytes are typically used as array indices, counters in [[FOR]] loops, boolean (true or false) values, and many more.
  * INT (integer) is the most commonly used type in XC=BASIC programs. Integers offer a reasonably high range of values and they support negative numbers while still being computationally fast.
  * WORD is the unsigned version of INT. It's especially useful for specifying memory addresses, e. g in a [[POKE]] or [[PEEK]] statement.
  * LONG is similar to INT, but its numeric range is much larger. A LONG variable reserves 3 bytes in memory.
  * FLOATs are 32-bit floating point numbers with a 24-bit mantissa and an 8-bit exponent. They are similar to the numeric data type in CBM BASIC, but are accurate to only 6-7 decimal digits.

<adm warning>
Floating point variables have great flexibility because they can store very large and very small numbers, including a decimal fraction. However, they are manipulated much more slowly than the other types, and therefore should be used with caution and only when necessary.
</adm>

  * Finally, DECIMAL is a special type and the only reason it exists in XC=BASIC is because DECIMAL (or often called BCD - Binary Coded Decimal) numbers can be displayed on screen without the overhead of binary-decimal conversion. DECIMAL comes in handy when you want to display scores or other numeric information in a game relatively rapidly.

<adm warning>
DECIMAL has strict limitations. It only supports addition and subtraction and can not be converted to or from any other types.
</adm>

<adm note>
When displaying decimals, all the leading zeroes will be displayed. For example the number 99 will be displayed as ''0099''.
</adm>

===== Numeric literals =====

When compiling the program, the compiler must assign a type to all numbers it encounters. The compiler will identify the type of a number through the following rules:

  * A number featuring a decimal dot (''.'') will be recognized as FLOAT. For example, the number ''1.0'' is a FLOAT. You //must// use a decimal point in a FLOAT, even if its fractional part is zero. Without the decimal point the compiler will treat the number as an integral number and the program might be spending precious runtime converting it back to FLOAT.
  * A number appended with a ''d'' will be recognized as DECIMAL. For example, ''9999d'' is a valid DECIMAL.
  * A number between 0 and 255 will be recognized as BYTE
  * A number between -32,768 and 32,767 will be recognized as INT
  * A number between 32,768 and 65,535 will be recognized as WORD
  * A number between -8,388,608 and 8,388,607 will be recognized as LONG
  * Any other number will trigger a compile-time error

<adm note>
You can use scientific notation, e.g ''1.453E-12'' when writing FLOAT literals.
</adm>

==== Numeral systems ====

Numeric literals can be written in decimal, hexadecimal and binary form.

  * A number prepended with a ''$'' sign is recognized as hexadecimal, for example: ''$03FF''.
  * A number prepended with a ''%'' sign is recognized as binary, for example: ''%01110101''.
  * Any other numbers are recognized as decimal.

<adm warning>
Binary and hexadecimal numbers are always assumed unsigned. For example the number $FFFF will be treated as 65535 (WORD) rather than -1 (INT).
</adm>

===== Strings =====

Strings are fixed-length series of PETSCII characters. You can read more about strings on the [[v3:strings]] page.

<- syntax|Previous page ^ datatypes|Data Types  ^ variables|Next page ->

====== Variables ======

XC=BASIC is a statically typed programming language which means that the type of a variable is known at compile time. All variables have a type and that type cannot change.

===== Defining Variables =====

In an XC=BASIC program, all variables must be defined before they're used. Either you define them using the [[DIM]] statement (this is called //explicit// definition) or the compiler will auto-define them in certain situations. The latter is called //implicit// definition.

==== Explicit Definition ====

The ''DIM'' statement may be used to explicitly define variables. Here are some examples of variable definition using ''DIM'':

  DIM enemy_count AS INT
  DIM score AS DECIMAL
  DIM gravity AS FLOAT
  DIM name$ AS STRING * 16

Apart from the ''DIM'' statement, there are other cases where you may explicitly define a variable. You will learn about those later.

<adm note>
Defining variable types by using sigils (the ''#'', ''%'' and ''!'' suffixes) is no longer supported in XC=BASIC. The ''$'' character is allowed at the end of variable names for readability but the variable won't be defined as ''STRING'' just because the ''$'' sign is there. You //must// use ''DIM'' to define Strings.
</adm>

==== Implicit Definition ====

If an undefined variable is encountered by the compiler, it will try to define it silently. For example:

  a = 5
  PRINT a

The above program works because the compiler implicitly defines the variable ''a'' in the first line. But what will its type be? The compiler first checks the right hand side of the assignment, in this case the number ''5''. As stated previously, a number between 0 and 255 is best represented by the Byte type, and therefore the compiler will infer ''a'' to be of type Byte. This is called an //inferred type// because the compiler examines the expression and, using the above stated rules, decides which type best represents it.

This seems very convenient, but it is something you should generally avoid so that the compiler will not automatically assign data types you don't intend and/or produce results that are inaccurate yet hard to track down in code. Take the following example:

  a = 5
  a = a + 300
  PRINT a

In CBM BASIC, where the only numeric type is ''FLOAT'', you can safely expect the result to be ''305''. In XC=BASIC this is not the case. Let's break down the above example and see how the compiler will handle it:

  - The compiler defines ''a'' as ''BYTE'' and assigns the value ''5'' to it.
  - The expression ''a + 300'' is evaluated. Since ''300'' is an ''INT'', the expression will be evaluated as ''INT'', resulting to ''305''.
  - Now the result must be assigned to ''a''. The number ''305'' can't be assigned to a ''BYTE'', so it will be truncated to 8 bits.
  - The result is ''49''. 

Since, on the surface, the result does not make any sense to a human mind, it might be difficult to track down the problem. We can fix the above program by explicitly defining ''a'' as ''INT'':

  DIM a AS INT
  a = 5
  a = a + 300
  ' The result is: 305
  PRINT a

<adm warning>
It is recommended that you define variables explicitly rather than let the compiler guess their types to avoid issues like the example above.
</adm>

<adm note>
Unlike CBM BASIC variables, which are automatically initialized to ''0'', XC=BASIC does not provide any initialization of variables. This means that you cannot assume anything about the value of a variable until you have assigned some value to it. The initial value of a variable is simply whatever happens to be in the memory location XC=BASIC assigns to the variable.
</adm>

====== Constants ======

Constants are simple textual labels that represent numeric values //in compile time//. When the compiler encounters a constant, it will replace it with the value it represents.

The benefits of using constants instead of variables are:

  * As opposed to variables, no memory is allocated for constants
  * Constants are faster to evaluate than variables

<adm note>
Always use constants over variables whenever possible to save memory and speed up program execution. See the [[CONST]] keyword reference page for more information.
</adm>

====== Arrays ======

Arrays are similar to arrays in CBM BASIC.

  * They must be explicitly defined in all cases using ''DIM''
  * The maximum number of dimensions is 3

A few examples of defining arrays:

  DIM cards(52) AS BYTE
  DIM my_cards(5) AS BYTE
  DIM matrix(5, 5) AS FLOAT

Accessing array members is done using the usual BASIC syntax:

  DIM my_array(3, 3) AS LONG
  x = my_array(0, 1)

<adm warning>
Array indices are zero-based which means the first item's index is ''0''.
</adm>

<adm warning>
For performance reasons, array bounds are not checked at runtime. If you use an index that is out of the bounds, the result will be unpredictable.
</adm>

  DIM numbers(10) AS LONG
  ' This will compile fine but
  ' probably break your program because
  ' the last index in the array is 9.
  i = 10
  numbers(i) = 9999

====== Variable Scope ======

There are three scopes in XC=BASIC:

  * SHARED: the widest scope, a shared variable is visible in all Code Modules. A Code Module is a single source file (for example: //program.bas//). Learn more about [[code_modules|Code Modules here]].
  * GLOBAL: the variable is visible in the current Code Module (in the source file where it was defined).
  * LOCAL: the variable is only visible within the ''SUB'' or ''FUNCTION'' where it was defined.

If you define a variable outside a ''SUB'' or ''FUNCTION'', it will be defined in the **Global** scope by default which means that it can be accessed from everywhere within that BAS source file (even from within ''SUB''s and ''FUNCTION''s), but not from other files.

If you define a variable inside a ''SUB'' or ''FUNCTION'', it will be defined in the **Local** scope of that ''SUB'' or ''FUNCTION'' and it won't be accessible from anywhere else.

Using the ''SHARED'' keyword in a ''DIM'' statement, you can make a variable visible from all Code Modules:

<code>
' This file is first.bas
' 'a' is a global variable in this file only
DIM a AS INT
' 'b' is a shared variable visible in other files as well
DIM SHARED b AS INT
a = 5
b = 10
INCLUDE "second.bas"
' Will print: 5
PRINT a
' Will print: 11
PRINT b
</code>
<code>
' This file is second.bas
' 'a' is a global variable in this file only
' It doesn't collide with the other 'a' in first.bas
DIM a AS INT
a = 6
' We can access 'b' from first.bas
b = 11
</code>

====== Fast Variables ======

If you define a variable as ''FAST'', it will be reserved on the zero page, making it faster under the hood to reference and operate on. The space on zero page is limited ([[v3:memory_model|37-74 bytes, depending on target machine]]), but that's enough space to supply a relatively generous number of FAST variables.

<code>
DIM FAST ix AS BYTE
FOR ix = 0 TO 255
  ' A very fast loop
NEXT
</code>

<adm note>
When no more variables can be placed on the zero page, the compiler will emit a warning and ignore the ''FAST'' directive from then on.
</adm>

<- datatypes|Previous page ^ variables|Variables ^ operators|Next page ->

====== Operators ======

XC=BASIC provides the following operators:

===== Arithmetic Operators =====

  * ''*'' (multiplication)
  * ''/'' (division)
  * ''MOD'' (modulo)
  * ''+'' (addition or string concatenation)
  * ''-'' (subtraction)

Operands for the arithmetic operators can be any numeric expressions, with the exception of ''DECIMAL'' types that can only be operands for addition or subtraction.

The ''+'' operator can also be used to concatenate strings. In this case both operands must be strings, otherwise a compile-time error is emitted.

===== Relational Operators =====

  * ''='' (equal to)
  * ''<>'' (not equal to)
  * ''>'' (greater than)
  * ''>='' (greater than or equal to)
  * ''<'' (less than)
  * ''<='' (less than or equal to)

Operands for the relational operators can be any numeric expressions. A relational expression evaluates to ''255'' when the comparison passes (TRUE), and ''0'' when it fails (FALSE).

The relational operators ''='' and ''<>'' can also be used to compare strings. In this case both operands must be strings, otherwise a compile-time error will be emitted.

<adm note>
Comparing strings for ''>'', ''>='', ''<'' and ''<='' is not supported.
</adm>

===== Logical Operators =====

  * ''AND''
  * ''OR''
  * ''XOR''
  * [[SHL]] - logical shift left
  * [[SHR]] - logical shift right

Logical operators can operate on all integral types (BYTE, INT, WORD, LONG and DECIMAL).

===== Unary Operators =====

  * ''@'' ([[address-of|address of]])
  * ''-'' (negation)
  * ''NOT'' (logical reversion)

<- variables|Previous page ^ operators|Operators ^ expressions|Next page ->
====== Arithmetic expressions ======

When no parentheses are present, arithmetic expressions are evaluated from left to right, with multiplication and division having a higher priority than addition and subtraction.

The following table explains operator precedence in XC=BASIC:

| Highest    | ''NOT'', ''-'' (unary) |
|                 | ''*'', ''/'', ''MOD'' |
|                 | ''+'', ''-'' |
|                 | ''<'', ''<='', ''>'', ''='', ''>='', ''>'' |
| Lowest    | ''AND'', ''OR'', ''XOR'' |

The arithmetic operators, ''+'', ''-'', ''*'', and ''/'', work in the expected fashion, however, the result of arithmetic on type BYTE, WORD, INT or LONG cannot have a fractional result. Therefore ''5 / 2'' evaluates as 2, not 2.5. However, ''5.0 / 2.0'' evaluates as 2.5, because the presence of the decimal point tells the compiler that the numbers are of type FLOAT.

  PRINT 5/2 ' Outputs 2
  PRINT 5.0/2.0 ' Outputs 2.5

Operators, except unary operators, accept two operands. These two operands do not have to be of the same type. In a mixed expression, the operands are promoted to the higher type, being BYTE the lowest and FLOAT the highest type. The table below summarizes the results of a partially evaluated expression.

^              ^ BYTE            ^ WORD          ^ INT ^ LONG ^ FLOAT ^ DECIMAL ^
^ BYTE    | BYTE          | WORD        | INT | LONG | FLOAT |  -  |
^ WORD  | WORD        | WORD        | INT | LONG | FLOAT |  -  |
^ INT        | INT             | INT              | INT | LONG | FLOAT |  -  |
^ LONG   | LONG | LONG | LONG | LONG | FLOAT |  -  |
^ FLOAT  | FLOAT        | FLOAT        | FLOAT | FLOAT | FLOAT |  -  |
^ DECIMAL |  -  |  -  |  -  |  -  |  -  | DECIMAL |

<adm note>
DECIMAL types can not be used together with other types.
</adm>

The type of the data being operated on must be considered. For example, adding two values of type BYTE will always result in a value which is also of type BYTE, even if the result is too large to fit in a BYTE. For example, if ''x'' is a variable of type BYTE which has been previously assigned the value of 254, then the expression ''x + 4'' will NOT have a value of 258, but 2. This is because BYTE variables can only take on values between 0 and 255, so that when you add 4 to 254, the result is (258-256) = 2.

Likewise, adding or multiplying two numeric literals is subject to overflow, even if the left hand side of the assignment is a variable that could otherwise fit the result.

  DIM a AS INT
  a = 250 + 6
  PRINT a ' Outputs 0

Since both 250 and 6 are of type BYTE, the result will also be of type BYTE, regardless the type of ''a''. To overcome this problem, use the typecasting functions [[v3:cbyte|]], [[v3:cword|]], [[v3:cint|]] and [[v3:cfloat|]].

  DIM a AS INT
  a = CINT(250) + CINT(6)
  PRINT a ' Outputs 256

<- operators|Previous page ^ expressions|Arithmetic expressions ^ strings|Next page ->
====== Strings ======

Strings are fixed-length series of PETSCII characters. The maximum length of a string is 96 characters.

===== String literals =====

String literals must be enclosed between double quote (''"'') characters and may contain any ASCII character. Every ASCII character that has a PETSCII equivalent will be translated to PETSCII.

For characters that don't have an ASCII equivalent, you can use PETSCII escape sequences. An escape sequence is a number or an alias in curly braces. For example:

  PRINT "{CLR}" : REM clear screen
  PRINT "{147}" : REM same as above
  PRINT "{WHITE}text in white"

Refer to [[:petscii_escape_sequences|this page]] for all supported escape sequences.
===== Defining string variables =====

As opposed to numeric variables, string variables cannot be implicitly defined. You must use the ''DIM'' keyword to create a variable of STRING type. The statement must define the variable name, the type, and the maximum string length, as in this example:

  DIM varname$ AS STRING * 16
  
This will create a STRING variable named ''varname$'' with a maximum length of 16 characters.

<adm note>
The ''$'' postfix in the variable name is optional and may be omitted.
</adm>

<adm warning>
The maximum allowed string length is 96 characters.
</adm>
===== Value assignment =====

Variables of STRING type, just like any other variables, may be assigned values using the ''='' operator:

  varname$ = "hello world"
  
There's one caveat that you must be aware of: if the right-hand side of the assignment is longer than the variable's maximum length, the string will be truncated to fit into the variable. For example:

  DIM varname$ AS STRING * 5
  varname$ = "hello world"
  PRINT varname$ : REM will output "hello"
  
<adm warning>
Strings will be truncated to the maximum length that will fit into the variable. So if a STRING variable was defined with a length of 32, for example, then only the first 32 string characters of the assigned value will be stored.
</adm>
===== String operators =====

Use the ''+'' operator to concatenate two strings.

  DIM name$ AS STRING * 16
  DIM greet$ AS STRING * 23
  INPUT "enter your name: "; name$
  greet$ = "hello, " + name$
  
You can use the comparison operators ''='' and ''<>'' to verify two strings are identical.
===== String functions =====

You can find all functions that operate on strings on the [[functionref]] page.

===== Direct string manipulation =====

If you intend to manipulate strings directly, for example to examine and/or replace individual characters, you may use [[PEEK]] and [[POKE]] to read and write individual characters within strings. For this you must understand how strings are stored in memory. When you define a string variable, as in this example:

  DIM mystr$ AS STRING * 8

...the compiler will allocate 9 bytes in memory - one for holding the string length, and the rest for the characters that make up the string value. Now when you assign a value to this variable, such as:

  mystr$ = "hello"

...the memory area will be set like this (numbers in hexadecimal):

{{:v3:str_hello.png?nolink&400|}}

The first byte will contain the string length (five characters in this case) and the following 5 bytes will represent the encoded PETSCII characters. Since the fixed size of this string is 8 characters, but the actual string is only 5 characters long, the last three bytes are unused and their values are undefined and insignificant. However, XC=BASIC does not perform "garbage collection" like some others languages do, so those 3 bytes will remain in memory for the entire runtime of the program as unused space unless you alter the string by assigning a new value. Therefore, for the sake of efficient memory use, it is best to ensure all strings are defined to a length that is as short as possible for the needs of the program.

The "@" operator returns the memory address of a variable. With this address, you can easily manipulate the string. For example, you can change its first character to an "A", as in the following example:

  POKE @mystr$ + 1, 65
  PRINT mystr$

Here is how the compiler will handle this example:

  * The expression ''@mystr$'' will be resolved to the address of ''mystr$'' as a WORD. This is the 1st byte of the string in memory, the one that holds the length of the string.
  * Adding 1 will resolve to the first character of the string (2nd byte).
  * The number 65 is the PETSCII-code of the letter 'A'

If the above code is compiled and run, the output will be "AELLO".

<- expressions|Previous page ^ strings|Strings ^ flowcontrol|Next page ->
====== Control Flow Statements ======

===== Conditional branching =====

With the ''IF'' statement you can test a condition and then run code based on whether the condition test passed or failed.

  IF <condition> THEN
      <statements>
  END IF

The ''IF'' clause runs the statements under it when the **<condition>** is evaluated to be **TRUE** (pass). If the **<condition>** evaluates to **FALSE** (fail), nothing is run.

You can optionally include **<statements>** that are run when the **<condition>** fails by adding an ''ELSE'' clause

  IF <condition> THEN
      <statements>
  ELSE  
      <statements>
  END IF

XC=BASIC doesn't contain a boolean data type to represent true or false, it uses a ''BYTE'' instead. The value of 0 represents **FALSE**. Any other value greater than 0 represents **TRUE**.

When the **<condition>** contains a comparison operator, such as ''='' or ''>'', the result of the comparison is set to 255 when the comparison passes, and 0 when it fails. The result is then processed as normal, with 0 representing **FALSE** and any other number representing **TRUE**.

If the **<condition>** is a numerical expression, such as ''1'' or ''10 - 10'', the result is evaluated the same way as previously described.

==== Single Line Variation ====

The ''IF'' statement can be written on a single line:

  IF <condition> THEN <statements> [ELSE <statements>]

One or more code **<statements>** must be added to the **THEN** clause. If multiple statements are added, they must be separated by a colon.

The ''ELSE'' clause is optional, and must contain at least one code **<statement>**. Multiple statements can be used if separated by a colon.

The single line ''IF'' statement runs the same as the normal multi line ''IF'' statement described in the previous section.

===== Multiple branching =====

The [[ON]] statement allows you to define multiple branches and an //index// expression. This expression will be evaluated as a number N and the program will continue at the Nth label in the list of branches.

<adm note>
The maximum allowed number of labels in the list is 256.
</adm>

  DIM x$ AS STRING * 8
  INPUT "enter a number "; x$
  ON SGN(VAL(x$)) + 1 GOTO negative, zero, positive
  negative:
  PRINT "you entered a negative number"
  END
  zero:
  PRINT "you entered zero"
  END
  positive:
  PRINT "you entered a positive number"

<adm warning>
Unlike CBM BASIC, where the first label (or line number) corresponds to the number 1, in XC=BASIC labels are zero-based. The first label is used for value 0, the second for 1, and so on.
</adm>

<adm warning>
If index is evaluated to a number that has no matching label in the list, for example if the number is bigger than the allowed number of labels, the program may crash or behave abnormally.
</adm>

''ON'' can also be used in combination with [[GOSUB]].
===== Looping =====

==== FOR ... NEXT loop ====

Syntax:

  FOR <variable> [AS <type>] = <start_value> TO <end_value> [STEP <step_value>]
    <statements>
  NEXT [<variable>]

The ''FOR ... NEXT'' loop initializes a counter variable and executes the statements until the counter variable equals the value in the ''TO'' clause. After each iteration, the counter variable is incremented by the step value or 1 in case the step value was not specified. For example:

  DIM i AS BYTE
  FOR i = 1 TO 30 STEP 3
    PRINT i
  NEXT i

In the above, the counter variable is pre-defined. If the variable is not pre-defined, you can use the ''AS'' keyword to specify the type and this way the compiler will automatically define the variable before starting the loop. The following code is identical to the one above:

  FOR i AS BYTE = 1 TO 30 STEP 3
    PRINT i
  NEXT i

<adm warning>
The counter variable, the start value, the end value and the step value must all be of the same numeric type and this type is concluded from the counter variable. All the other expresions will be converted to this type if possible, otherwise a compile-time error will be thrown.
</adm>

<adm note>
The variable name can be omitted in the ''NEXT'' statement.
</adm>

You can use the ''CONTINUE FOR'' command to skip the rest of the statements in the ''FOR ... NEXT'' block and go to the next iteration, for example:

  REM -- print numbers from 1 to 10, except 5 and 7
  FOR num AS BYTE = 1 TO 10
    IF num = 5 OR num = 7 THEN CONTINUE FOR
    PRINT num
  NEXT

Finally, you can use the ''EXIT FOR'' statement to early exit a ''FOR ... NEXT'' loop.

  DIM a$ AS STRING * 1
  FOR i AS BYTE = 1 TO 10
    PRINT "iteration #"; i : INPUT "do you want to continue? (y/n)"; a$
    IF a$ = "n" THEN EXIT FOR
    PRINT i
  NEXT i

==== DO ... LOOP loop ====

The ''DO ... LOOP'' loop can be used as either a pre-test or post test loop.

=== Pre-test syntax ===

  DO WHILE|UNTIL <condition>
    <statements>
  LOOP

=== Post-test syntax ===

  DO
    <statements>
  LOOP WHILE|UNTIL <condition>

The former is used to test the condition //before// entering the loop body and the latter is used to test the condition //after// each iteration. This effectively means that post-test loop will be executed at least once, whereas in a pre-test loop the condition may fail the very first time and therefore it may happen that the statements in the loop will not be executed at all.

In both types, you can either use the ''WHILE'' or the ''UNTIL'' keywords. ''WHILE'' means that the loop is //entered// if the condition evaluates to true, ''UNTIL'' means that the loop is //exited// if the condition evaluates to true.

Similarly to ''EXIT FOR'', you can use the ''EXIT DO'' command to prematurely exit a ''DO ... LOOP'' block, or ''CONTINUE DO'' to skip rest of the block and go to the next iteration.

<- strings|Previous page ^ flowcontrol|Control Flow Statements ^ subroutines|Next page ->
====== Subroutines ======

While you can use the [[GOSUB]] command in pair with [[RETURN]] to call parts of code as subroutines, the more sophisticated way of implementing subroutines is using the ''SUB ... END SUB'' block.

===== Defining Subroutines =====

Subroutines are named routines that accept zero or more arguments. The simplest syntax to define a subroutine is the following:

  SUB <rountine_name> ([arg1 AS <type>, arg2 AS <type>, ...])
    <statements>
  END SUB

It is worth noting that the argument list is optional. If you omit the arguments, you still must add the empty parentheses after the routine name, like so:

  SUB <routine_name> ()
    <statements>
  END SUB

===== Calling Subroutines =====

You can use the [[CALL]] keyword to call a subroutine. It behaves similarly to [[GOSUB]] with an important difference: ''CALL'' can pass arguments to the subroutine. Consider the following example:

  SUB greet (name$ AS STRING * 10)
    PRINT "Hello, "; name$
  END SUB
  
  CALL greet("Emily") ' will display: Hello, Emily
  CALL greet("Mark") ' will display: Hello, Mark

The ''CALL'' command will evaluate the argument list in the parentheses, pass all arguments to the subroutine and then instruct the computer to continue the program at the top of the subroutine.

===== Exiting Subroutines =====

The subroutine will be exited at the ''END SUB'' statement. If you want to exit a subroutine earlier, use the ''EXIT SUB'' command:

  SUB test (a AS INT)
    IF a < 0 THEN PRINT "positive number please" : EXIT SUB
    PRINT SQR(a)
  END SUB
  CALL test(-1)
===== Local and Global Variables =====

Variables defined inside a subroutine are local variables, i. e. they are only accessible within that subroutine. Global variables (the ones defined outside subroutines) are visible from within all subroutines.

  globalvar = 1
  SUB test ()
    PRINT globalvar : REM this is okay as globalvar is visible form here
    localvar = 5
  END SUB
  CALL test()
  PRINT localvar : REM ERROR: localvar is not defined in the global scope

==== Shadowing ====

A local variable may have the same name as a global variable. In such cases the local variable will be used inside the subroutine. This is know as a "shadow variable." Consider the following example:

  a = 42
  SUB test ()
    a = 5
    PRINT a
  END SUB
  CALL test() : REM will output 5
  PRINT a : REM will output 42


===== Static vs. Dynamic =====

It is important to understand how arguments may be passed to a subroutine. XC=BASIC offers two methods:

  * //Dynamic// arguments: the arguments are created dynamically in memory. Before the subroutine is called, a new area in memory - a //stack frame// - is allocated, and this area holds the passed arguments. The advantage of dynamic memory allocation is that it allows recursive subroutine calls, i. e. the subroutine can call itself without harming its data. However, there is a penalty: dynamic arguments operate much slower than static arguments.
  * //Static// arguments: the arguments are stored in a pre-allocated memory area. When the subroutine is called, the arguments are simply copied to this area. This is much faster than dynamic frame allocation but it doesn't support recursion.

The default method of passing arguments is //dynamic//. If you'd like to pass arguments statically, append the ''STATIC'' keyword to the subroutine definition:

  SUB <subroutine_name> (arg AS <type>) STATIC

<adm note>
The ''STATIC'' keyword in a subroutine definition not only applies to the subroutine's arguments but to all its local variables as well.
</adm>

<adm warning>
Always define your subroutines ''STATIC'' unless you intend to make recursive calls. The compiler will try to detect possible recursion and warn you about this in case you forget the ''STATIC'' keyword.
</adm>

==== Static Variables Inside Dynamic Subroutines ====

You can mix static and dynamic behaviour using the ''STATIC'' keyword instead of ''DIM'' to mark local variables static when a subroutine is otherwise dynamic.

  SUB test (arg AS INT)
    DIM a AS INT : REM a is dynamic
    STATIC b AS INT : REM b is static
  END SUB

<adm note>
Static local variables' values are preserved between subroutine calls. Upon entering a subroutine, static local variables have the same value as when the subroutine last exited. They are not overwritten.
</adm>

If a subroutine is defined as ''STATIC'', all its local variables will be static, regardless of whether you use the ''DIM'' or ''STATIC'' keyword to define them:

  SUB test (arg AS INT) STATIC
    DIM a AS INT : REM a is static
    STATIC b AS INT : REM b is also static
  END SUB

<adm warning>
The stack frame that is allocated on each subroutine call must not be larger than 128 bytes. The compiler detects if a subroutine requires a larger stack frame, and emits a compile-time error in such cases. Therefore it is recommended to keep as many variables ''STATIC'' as possible.
</adm>

===== Overloading =====

Subroutine overloading, commonly known as method overloading in object-oriented programming languages, refers to the ability to create multiple subroutines with the same name but different parameters. This feature allows a programmer to define different ways to call a subroutine based on the types and number of arguments passed.

Overloaded subroutines have the same name but differ in the type, number, or both type and number of parameters.

==== Compile-Time Polymorphism ====

The appropriate subroutine to call is determined at compile-time based on the arguments provided in the call.

Consider the following example:

  SUB PrintMessage(msg AS STRING * 16)
      PRINT msg
  END SUB
  
  SUB PrintMessage(msg AS STRING * 16, num AS INT) OVERLOAD
      PRINT msg; " "; num
  END SUB
  
  CALL PrintMessage("Hello, XC=BASIC!")
  CALL PrintMessage("The number is", 42)

<adm warning>
You must use the ''OVERLOAD'' keyword when defining the second and subsequent overloaded variations of a subroutine. This tells the compiler that the duplicate subroutine names are intentional overloads and not a programming mistake.
</adm>

<adm note>
It is possible to overload the built-in XC=BASIC functions in your code, too.
</adm>
===== Forward Declaration =====

A subroutine can not be called before it was defined. This often makes it hard to organize your code in a clean and readable way. You may want to put subroutines at the end of your code and that's a perfectly valid requirement.

This is where forward declaration comes in handy. Forward declaration means that you declare a subroutine's all important properties (or the //header// of the subroutine) beforehand, and leave the actual code implementation for later. Consider the following example:

  REM -- the top of the program
  DECLARE SUB somesub (arg AS FLOAT) STATIC
  REM -- the subroutine will be implemented later but it is already callable
  CALL somesub(3.1415)
  REM -- the bottom of the program
  SUB somesub (arg AS FLOAT) STATIC
    PRINT "two times the argument is: "; arg * 2.0
  END SUB

<adm warning>
The implementation of the subroutine later in the code must use the same number and type of arguments as the declaration. Overloading is still possible, though: you may declare overloaded variations of the subroutine and implement each variation later on in the program.
</adm>
===== Subroutine Visibility =====

Subroutines, as well as variables, may be defined with different visibility levels. XC=BASIC offers two options:

  * //Global// visibility: the subroutine is callable from within the entire code module it was defined (but not outside the code module).
  * //Shared// visibility: the subroutine is callable from within all code modules.

<adm note>
The default visibility for subroutines is //global//.
</adm>

To define a subroutine as shared, append the ''SHARED'' keyword to its definition:

  SUB <subroutine_name> (arg AS <type>) SHARED
  
  END SUB

This will ensure the subroutine is callable from within other code modules. Read more about [[code_modules|Code Modules here]].

<- flowcontrol|Previous page ^ subroutines|Subroutines ^ functions|Next page ->


====== Functions ======

Functions in XC=BASIC are essentially the same as [[subroutines|Subroutines]], with one important difference: functions //must// return a value. Everything else that is described on the [[subroutines|previous page]] is true for functions and will not be repeated here.

===== Defining the return type =====

A function must always return a type, that is, the type of the value that it returns. You must define the return type in the function definition line using the ''AS'' keyword:

  FUNCTION <fn_name> AS <type> (<arg> AS <type>)
    <statements>  
  END FUNCTION

===== Calling a function =====

Functions can not be called using the ''CALL'' keyword, but rather they must be invoked as part of an expression. A function call is treated like an expression and its type is concluded from the function's return type. For example:

  FUNCTION test AS LONG ()
    REM -- function body here
  END FUNCTION
  
  x = test()
  REM -- The variable x will be implicitly defined as LONG
  REM -- because the right hand side is a LONG type

<adm note>
For the above reason, there are no void functions in XC=BASIC. [[subroutines|Subroutines]] serve as void functions.
</adm>
===== Returning a value =====

There are two ways to return a value from a function:

  * The QBASIC style, by assigning a value to the function name.
  * Using the ''RETURN'' keyword.

Both styles are accepted in XC=BASIC. Here are two examples to demonstrate each:

  REM -- returning value the QBASIC style
  FUNCTION test AS BYTE ()
    test = 42
  END FUNCTION
  PRINT test() : REM will output 42

  REM -- returning value using the RETURN keyword
  FUNCTION test AS BYTE ()
    RETURN 42
  END FUNCTION
  PRINT test() : REM will output 42

The above two codes are identical, but the ''RETURN'' keyword comes with a restriction: it immediately exits the function. There can be, however, situations where you want to continue executing the function even after specifying the return value, for example:

  (TODO: provide example)

Note the use of the ''EXIT FUNCTION'' command that is used to early exit the function.

<adm warning>
If the code exits from a function before any return value was specified, an undefined value will be returned.
</adm>


====== User-Defined Types ======

User-defined types (or UDT's) allow you to create your own data structures. In its simplest form, a type definition is a bunch of field definitions inside a ''TYPE ... END TYPE'' block. The following example illustrates a very simple type definition:

  TYPE EMPLOYEE
    firstname AS STRING * 16
    lastname AS STRING * 16
    salary AS LONG
  END TYPE

A type can have any number of fields, but there is one restriction: the size of a single instance of the type may not exceed 64 bytes. In the above example, //firstname// and //lastname// take up 17 bytes each, and //salary//, being of LONG type takes 3 bytes. That's 37 bytes total, well below the limit.

Having defined the new type as above, you can define variables of EMPLOYEE type and assign values to its fields using the dot (''.'') notation:

  DIM emp AS EMPLOYEE
  emp.firstname = "Mark"
  emp.lastname = "Cunnigham"
  emp.salary = 45500

To read a field value you can use the same dot-notation:

  PRINT emp.firstname : REM outputs: "Mark"

<adm note>
Variables defined as UDT's are called //instances// of that type. In the above example, ''emp'' is an //instance// of the EMPLOYEE type.
</adm>
===== Arrays of user defined types variables =====

Multiple instances of UDT's can be organized in arrays, for example:

  DIM employees(50) AS EMPLOYEE

Now to access field values of a specific member in the array, you can combine the array notation and the dot notation:

  DIM sum AS LONG : sum = 0
  FOR i AS BYTE = 0 TO 49
    sum = sum + employees(i).salary
  NEXT i
  PRINT "the average salary at the company is "; sum / 50

<adm warning>
Arrays can be dimensioned as user-defined type, however TYPE definitions cannot contain array fields.
</adm>
===== Nested UDT's =====

A field in a TYPE definition can be of another TYPE, and so on, as long as a single insance does not exceed the 64 bytes limit explained above.

  TYPE VECTOR
    x AS INT
    y AS INT
  END TYPE
  
  TYPE SPRITE
    pos AS VECTOR
    color AS BYTE
  END TYPE

To access fields within the nested type, you can extend the dot notation like in the following example:

  DIM monster AS SPRITE
  monster.pos.x = 160
  monster.pos.y = 100
  monster.color = 3

===== Type methods =====

You can define [[Subroutines]] and [[Functions]] within a type declaration that allows you to define routines that work with data in a single instance of that type. These routines are called //type methods// and are very similar to object methods in object-oriented programming. Extending the example above, let's write a routine that moves the imaginary monster on the horizontal axis:

  TYPE VECTOR
    x AS INT
    y AS INT
  END TYPE
  
  TYPE SPRITE
    pos AS VECTOR
    color AS BYTE
    SUB move (amount AS INT) STATIC
      THIS.pos.x = THIS.pos.x + amount
    END SUB
  END TYPE
  
  DIM monster AS SPRITE
  monster.pos.x = 100
  CALL monster.move(5)
  PRINT monster.pos.x : REM outputs 105

===== The THIS keyword =====


Note the usage of the [[THIS]] keyword in the above example. ''THIS'' is a special variable that refers to the instance on which the method was called. In the above example, ''THIS'' refers to the variable that the ''move'' method was called on, in this case: //monster//.

<adm note>
Adding methods to a TYPE definition does not increase an instance's size and therefore methods do not count in the 64 bytes size limit.
</adm>

Defining functions within type definitions allows you to write methods that return a value. The following example is a theoretical game where two players fight each other, hitting in rounds, with a random damage. The method ''hit(damage)'' subtracts the damage from a fighter's energy and the method ''isdead()'' tells if the fighter is out of energy.

  TYPE FIGHTER
    energy as INT
    SUB hit (damage AS BYTE) STATIC
      THIS.energy = THIS.energy - CINT(damage)
    END SUB
    FUNCTION isdead AS BYTE () STATIC
      RETURN THIS.energy <= 0
    END FUNCTION
  END TYPE
  
  DIM player1 AS FIGHTER
  DIM player2 AS FIGHTER
  player1.energy = 1000
  player2.energy = 1000
  
  RANDOMIZE TI()
  DO
    CALL player1.hit(CBYTE(RNDL()))
    CALL player2.hit(CBYTE(RNDL()))
    PRINT "p1 energy: "; player1.energy; ", p2 energy: "; player2.energy
  LOOP UNTIL player1.isdead() OR player2.isdead()
  PRINT "game over"

As seen above, you can organize code in a very well-structured way with the help of UDT's.
 
<- functions|Previous page ^ udt|User-Defined Types ^ code_modules|Next page ->
====== Code Modules ======

A Code Module (or simply module) is a file containing XC=BASIC statements. An XC=BASIC program consists of one or more modules.

<adm note>
Modules usually have the //.bas// extension, although the compiler does not care about the extension. The //.bas// extension is to help text editors to detect what kind of code you're editing.
</adm>

Although completely optional, it is a good idea to organize code in multiple modules for better readability and maintainability if the program is growing exceedingly large.

===== Including modules =====

The [[INCLUDE]] directive instructs the compiler to load the given module, compile it, and "inject" the code into the current module at the exact point where the ''INCLUDE'' directive is.

//main.bas//
  REM -- a simple game
  INCLUDE "instructions.bas"
  INCLUDE "play.bas"
  CALL instructions ()
  DO
    CALL gameplay ()
  LOOP WHILE 1
//instructions.bas//
  SUB instructions () SHARED STATIC
    PRINT "welcome. use joystick in port 2. press fire to jump."
  END SUB
//play.bas//
  SUB gameplay () SHARED STATIC
    ' actual game code here...
  END SUB

The above example is a program that consists of three modules. The main module is //main.bas// and it includes two other modules, //instructions.bas// and //play.bas//.

As opposed to other languages, like C for example, you do not have to compile each module and have a linker to link them in one executable. You only have to compile the main module and the rest will be resolved by the compiler.

<adm note>
Included modules are resolved recursively. You can include modules in included modules, to any depth.
</adm>

Refer to the [[INCLUDE]] page to learn more - for example, how the compiler resolves the path of included modules.

===== Sharing identifiers among modules =====

<adm note>
We'll use the term "identifier" to refer to variables, constants, subroutines and functions.
</adm>

As you might have previously read [[variables#variable_scope|here]] and [[subroutines#subroutine_visibility|here]], variables, as well as constants, subroutines and functions, have three levels of visibility. The default visibility is GLOBAL, which means that the identifier is visible everywhere within the module where it was defined but not in other modules. The exception to this rule is when a variable or constant is defined within a subroutine or function. In this case, the default visibility is LOCAL.

To share an identifier with other modules, you must use the [[SHARED]] keyword. A few examples:

  SHARED CONST PI = 3.14159
  DIM a AS INT SHARED
  SUB clear_screen () SHARED STATIC



====== Error Handling ======

===== Defining an error handling routine =====

Starting from XC=BASIC version 3, certain runtime errors are trappable using the ''ON ERROR GOTO'' statement. You can specify a custom error handling routine that makes it possible to recover from errors when needed. The following example demonstrates this functionality:

  ON ERROR GOTO errhandler
  DIM d$ AS STRING * 6
  
  start:
    INPUT "enter divisor "; d$
    PRINT "10/"; d$; "="; 10.0 / VAL(d$)
    END
  
  errhandler:
    IF ERR() = 20 THEN
      PRINT "division by zero error"
      GOTO start
    END IF

===== Getting the error code =====

When an error occurs, the ''ERR()'' function returns the error code, a number between 0 and 255. The following are built-in errors in XC=BASIC:

^ Code      ^ Error message       ^
|1              |TOO MANY FILES   |
|2              |FILE OPEN              |
|3              |FILE NOT OPEN      |
|4              |FILE NOT FOUND   |
|5              |DEVICE NOT PRESENT |
|6              |NOT INPUT FILE      |
|7              |NOT OUTPUT FILE  |
|8              |MISSING FILENAME|
|9              |ILLEGAL DEVICE NUMBER |
|10            |DEVICE NOT READY |
|11            |OTHER READ ERROR |
|14            |ILLEGAL QUANTITY |
|15            |OVERFLOW |
|20            |DIVISION BY ZERO |
|21            |ILLEGAL DIRECT |

===== User-defined errors =====

Apart from the built-in errors, you can define your own error codes, too. You can use the ''ERROR'' command to trigger any error, built-in or custom.

  ON ERROR GOTO errhandler
  ERROR 99
  END
  errhandler:
    IF ERR() = 99 THEN PRINT "my custom error occured" ELSE PRINT "other error"

