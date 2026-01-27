Const SCREEN_ADDR = 1024
Const WALL = 160 : Const SPACE = 32 : Const MOUSE = 81

Dim ScreenPosition as WORD fast : Dim NEWScreenPosition as WORD fast

Dim NextDirection as BYTE fast: Dim FirstNextDirection as BYTE fast
Dim Steps as WORD fast: Dim MaxSteps as WORD fast

Dim FinalScrPosition as WORD fast

Dim DirArray(4) as INT @loc_DirArray
loc_DirArray:
DATA AS INT 2, -80, -2, 80

function random as BYTE (max as BYTE) STATIC 'Thanks to Teppo Koskinen!
    Dim mask as BYTE : mask = 2
    do while mask <= max
        mask = shl(mask, 1)
    loop
    
    mask = mask - 1
    do
        random = RNDB() AND mask
    loop while random > max
end function

print "press a key (i need randomness)"
poke 198, 0: wait 198, 1

poke 53280,0 : poke 53281,0

randomize (ti() )
'the first numbers are not that random...
For I as BYTE = 0 to 11 : NextDirection = RNDB() : next I 'NextDirection used as a dummy variable!

restart:
memset SCREEN_ADDR, 1000, WALL
memset SCREEN_ADDR, 40, SPACE 'line 0, 40 spaces
memset 1984, 40, SPACE 'line 24, 40 spaces

ScreenPosition = 1103 'line 1, column 39
FOR I = 1 to 23
    'No SPACEing at the column 0!
    Poke ScreenPosition, SPACE
    ScreenPosition = ScreenPosition + 40
Next I

Steps = 0 : MaxSteps = 0

ScreenPosition = SCREEN_ADDR + 81 + (80 * cword(Random(9))) + 2 * Random(9) 'CWORD is VERY IMPORTANT *** 

poke ScreenPosition, 4 ' "D"

DigAnotherLocation:
    NextDirection = Random(3) : FirstNextDirection = NextDirection
    if Steps > MaxSteps then MaxSteps = Steps: FinalScrPosition = NEWScreenPosition

TryDiggingAgain:
    NEWScreenPosition = ScreenPosition + DirArray(NextDirection)
    If Peek(NEWScreenPosition) = WALL Then
        Poke NEWScreenPosition, NextDirection
        Poke ScreenPosition + SHR(DirArray(NextDirection), 1), SPACE
        ScreenPosition = NEWScreenPosition
        Steps = Steps + 1
        Goto DigAnotherLocation
    End If

    NextDirection = (NextDirection + 1) AND 3 'Keep NextDirection between 0 and 3
    If NextDirection <> FirstNextDirection then Goto TryDiggingAgain
    
    NextDirection = Peek(ScreenPosition) : Poke ScreenPosition, SPACE
    Steps = Steps - 1
    If NextDirection < 4 then
        ScreenPosition = ScreenPosition - DirArray(NextDirection) 'Backtrack!
        Goto DigAnotherLocation
    end If
    
    Poke ScreenPosition, 1 : Poke FinalScrPosition, 2 '"A", "B"
    Print "{HOME} max steps: " ; MaxSteps ; " - final loc: " ; FinalScrPosition
    
'   ****MOUSE****
    Poke ScreenPosition, MOUSE : NextDirection = 2
Mouse:
    wait $d011, 128, 128 : wait $d011, 128 'wait for frame
    NEWScreenPosition = ScreenPosition + SHR(DirArray(NextDirection), 1)
    if NEWScreenPosition = FinalScrPosition then goto restart
    If Peek(NEWScreenPosition) = SPACE then
        Poke NEWScreenPosition, MOUSE : Poke ScreenPosition, SPACE
        ScreenPosition = NEWScreenPosition
        NextDirection = (NextDirection - 2) AND 3
    End If
    NextDirection = (NextDirection - 1) AND 3
    goto Mouse
