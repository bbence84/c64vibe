'***********************************************************************
'JJ PACMAN!
'
'From an idea by AGPX@itch.io
'Code rewritten by JJFlash@itch.io
'
'Written and tested under XC=BASIC 3.1.9 !

'--- Will improve and translate the comments if any interest is there! ---
'***********************************************************************


poke $DC0D, $7F 'spegne l'interrupt di sistema (si guadagna qualche ciclo di clock in più...)
poke 53280, 0 : poke 53281, 0 'non uso BORDER e BACKGROUND perché al momento mi sembra abbiano problemi con l'ottimizzatore, sprecando un sacco di byte

memcpy @pacSprites, $8000, @endOfData - @pacSprites
memcpy @pacCharset, $B800, @pacSprites - @pacCharset

sprite multicolor 1, 0

poke $DD00, %00010101 'bank 2
charset 7
screen 1
sys $E544 FAST 'clear screen

VOLUME 15

CONST FALSE = 0
CONST TRUE = 255

type tMonster
    iCoord_X as INT
    bCoord_Y as BYTE
    bDirection as BYTE
    bShapeNumber as BYTE
    bOriginalColour as BYTE
    bInitialMovementTimer as BYTE
    bMovementTimer as BYTE
end type
Dim aMonsters(4) as tMonster

sub resetMonsters() STATIC
    aMonsters(0).iCoord_X = 144
    aMonsters(0).bCoord_Y = 80
    aMonsters(0).bDirection = 1 'est
    aMonsters(0).bShapeNumber = 12
    aMonsters(0).bOriginalColour = 2 'rosso
    aMonsters(0).bInitialMovementTimer = 4
    aMonsters(0).bMovementTimer = 4

    aMonsters(1).iCoord_X = 121 '120 + 1
    aMonsters(1).bCoord_Y = 80
    aMonsters(1).bDirection = 1 'est
    aMonsters(1).bShapeNumber = 12
    aMonsters(1).bOriginalColour = 3 'ciano
    aMonsters(1).bInitialMovementTimer = 4
    aMonsters(1).bMovementTimer = 4

    aMonsters(2).iCoord_X = 186 '184 + 2
    aMonsters(2).bCoord_Y = 80
    aMonsters(2).bDirection = 1 'est
    aMonsters(2).bShapeNumber = 12
    aMonsters(2).bOriginalColour = 10 'rosa
    aMonsters(2).bInitialMovementTimer = 4
    aMonsters(2).bMovementTimer = 4

    aMonsters(3).iCoord_X = 163 '160 + 3
    aMonsters(3).bCoord_Y = 80
    aMonsters(3).bDirection = 1 'est
    aMonsters(3).bShapeNumber = 12
    aMonsters(3).bOriginalColour = 8 'arancione
    aMonsters(3).bInitialMovementTimer = 4
    aMonsters(3).bMovementTimer = 4
    
    sprite 0 MULTI SHAPE 12 COLOR aMonsters(0).bOriginalColour ON
    sprite 1 MULTI SHAPE 12 COLOR aMonsters(1).bOriginalColour ON
    sprite 2 MULTI SHAPE 12 COLOR aMonsters(2).bOriginalColour ON
    sprite 3 MULTI SHAPE 12 COLOR aMonsters(3).bOriginalColour ON
end sub

Dim pacman_iCoord_X as INT, pacman_bCoord_Y as BYTE
Dim pacman_iMap_X as INT, pacman_bMap_Y as BYTE
Dim pacman_iDelta_X as INT, pacman_bDelta_Y as BYTE
Dim pacman_iDirection_X as INT, pacman_bDirection_Y as BYTE
Dim pacman_bSpriteNumber as BYTE, pacman_bSpriteFrameNumber as BYTE

sub resetPacman() STATIC
    pacman_iCoord_X = 152
    pacman_bCoord_Y = 128
    pacman_iMap_X = 19
    pacman_bMap_Y = 16
    pacman_iDelta_X = -1 'pacman va a sinistra
    pacman_bDelta_Y = 0
    pacman_iDirection_X = -8 'pacman va a sinistra
    pacman_bDirection_Y = 0

    pacman_bSpriteNumber = 3 'pacman va a sinistra
    pacman_bSpriteFrameNumber = 0
    
    sprite 7 HIRES COLOR 7  ON 
end sub

Dim game_bPacmanCaught as BYTE, game_iScaredTimer as INT, game_bPowerPelletAnimTimer as BYTE
Dim game_iDotsToEat as INT, game_bPacmanTries as BYTE, game_dScore as DECIMAL
CONST DOTS_NUM = 306

Dim snd_bDotEaten_Timer as BYTE, snd_wDotEaten_Frequency as WORD, snd_wDotEaten_IncrementDirection as WORD
CONST SND_DOT_EATEN_TIMER_START = 3
CONST SND_DOT_EATEN_FREQUENCY_START = 1250
Dim snd_bPowerDotEaten_Timer as BYTE, snd_wPowerDotEaten_Frequency as WORD
CONST SND_POWERDOT_EATEN_TIMER_START = 45
CONST SND_POWERDOT_EATEN_FREQUENCY_START = 1500
Dim snd_bMonsterEaten_Timer as BYTE, snd_wMonsterEaten_Frequency as WORD
CONST SND_MONSTER_EATEN_TIMER_START = 6
CONST SND_MONSTER_EATEN_FREQUENCY_START = 2000

Dim wScreenTable(22) as WORD @screenTable
screenTable:
DATA AS WORD $8400, $8428, $8450, $8478, $84A0, $84C8, $84F0, $8518, $8540, $8568
DATA AS WORD $8590, $85B8, $85E0, $8608, $8630, $8658, $8680, $86A8, $86D0, $86F8
DATA AS WORD $8720, $8748

Dim bAnimFrameCounter as BYTE

Dim bFrameAnimNumber(8) as BYTE @FrameAnimData
FrameAnimData:
DATA AS BYTE 0, 0, 1, 1, 2, 2, 1, 1

Dim bDirections_Y(4) as BYTE @directionValues_Y
Dim iDirections_X(4) as INT @directionValues_X
directionValues_Y:
DATA AS BYTE 255, 0, 1, 0 'nord (-1), est, sud, ovest
directionValues_X:
DATA AS INT    0, 1, 0,-1 'nord     , est, sud, ovest

Dim bShortFrame as BYTE

sub initSounds() STATIC   
    VOICE 1 ADSR 8, 0, 6, 0  WAVE TRI 
    snd_bDotEaten_Timer = 0
    snd_wDotEaten_Frequency = SND_DOT_EATEN_FREQUENCY_START
    snd_wDotEaten_IncrementDirection = 1250
    
    VOICE 2 ADSR 0, 0, 15, 4  WAVE SAW
    snd_bPowerDotEaten_Timer = 0
    snd_wPowerDotEaten_Frequency = SND_POWERDOT_EATEN_FREQUENCY_START
    
    VOICE 3 ADSR 0, 0, 15, 4  WAVE SAW
    snd_bMonsterEaten_Timer = 0
    snd_wMonsterEaten_Frequency = SND_MONSTER_EATEN_FREQUENCY_START
end sub

sub soundHandler() STATIC
    if snd_bDotEaten_Timer then
        VOICE 1 TONE snd_wDotEaten_Frequency  ON
        snd_bDotEaten_Timer = snd_bDotEaten_Timer - 1
        snd_wDotEaten_Frequency = snd_wDotEaten_Frequency + snd_wDotEaten_IncrementDirection
        if snd_bDotEaten_Timer then
        else
            VOICE 1 OFF
            snd_wDotEaten_IncrementDirection = NOT (snd_wDotEaten_IncrementDirection) + 1 'inverte la direzione dell'aggiornamento frequenza suono!
        end if
    end if
    
    if snd_bPowerDotEaten_Timer then
        VOICE 2 TONE snd_wPowerDotEaten_Frequency  ON
        snd_bPowerDotEaten_Timer = snd_bPowerDotEaten_Timer - 1
        snd_wPowerDotEaten_Frequency = snd_wPowerDotEaten_Frequency + 100
        if snd_bPowerDotEaten_Timer then
        else
            VOICE 2 OFF
            snd_wPowerDotEaten_Frequency = SND_POWERDOT_EATEN_FREQUENCY_START
        end if
    end if
    
    if snd_bMonsterEaten_Timer then
        VOICE 3 TONE snd_wMonsterEaten_Frequency  ON
        snd_bMonsterEaten_Timer = snd_bMonsterEaten_Timer - 1
        snd_wMonsterEaten_Frequency = snd_wMonsterEaten_Frequency + 1000
        if snd_bMonsterEaten_Timer then
        else
            VOICE 3 OFF
            snd_wMonsterEaten_Frequency = SND_MONSTER_EATEN_FREQUENCY_START
        end if
    end if
end sub

sub updateMonster(bMonsterNum as BYTE) STATIC
    Dim bThis_ShapeNumber as BYTE FAST
    Dim FAST iThis_Coord_X as INT, bThis_Coord_Y as BYTE FAST
    Dim FAST iThis_Map_X as INT, bThis_Map_Y as BYTE FAST
    Dim FAST iOffset_Map_X as INT, bOffset_Map_Y as BYTE FAST
    Dim FAST iTargetTile_X as INT, bTargetTile_Y as BYTE FAST
    Dim FAST bThis_Direction as BYTE
    Dim FAST bOppositeDirection as BYTE, bDirectionToGo as BYTE FAST
    Dim FAST iThis_Distance as INT, iShortestDistance as INT FAST
    Dim FAST iPartialDistance as INT
    Dim FAST bHalfSprite_Coord_X as BYTE, bHalfSprite_Coord_Y as BYTE FAST
    Dim FAST bStepMultiplier as BYTE

    bThis_ShapeNumber = aMonsters(bMonsterNum).bShapeNumber
    
    iThis_Coord_X = aMonsters(bMonsterNum).iCoord_X 
    bThis_Coord_Y = aMonsters(bMonsterNum).bCoord_Y
    bHalfSprite_Coord_X = CBYTE(iThis_Coord_X AND 7)
    bHalfSprite_Coord_Y = bThis_Coord_Y AND 7
    
    bStepMultiplier = 0
    if bThis_ShapeNumber = 14 then bStepMultiplier = ((bHalfSprite_Coord_X OR bHalfSprite_Coord_Y) AND 1) XOR 1

    bDirectionToGo = aMonsters(bMonsterNum).bDirection 'si dà per scontato che il Mostro deve proseguire nella direzione attuale

    if bHalfSprite_Coord_X OR bHalfSprite_Coord_Y then 'se questo Mostro non sta su una posizione multipla di 8...
        if iThis_Coord_X = 156 then
            select case bThis_Coord_Y
                case 80
                    bDirectionToGo = 0 'nord
                    if bThis_ShapeNumber = 14 then
                        aMonsters(bMonsterNum).bShapeNumber = 12
                        aMonsters(bMonsterNum).bInitialMovementTimer = 4
                        aMonsters(bMonsterNum).bMovementTimer = 4
                        sprite bMonsterNum SHAPE 12 COLOR aMonsters(bMonsterNum).bOriginalColour
                        if (bMonsterNum AND 1) then bDirectionToGo = 1 else bDirectionToGo = 3 'est, ovest
                    end if
                case 64
                    if bDirectionToGo = 0 then 'nord
                        if (bMonsterNum AND 1) then bDirectionToGo = 1 else bDirectionToGo = 3 'est, ovest
                    else
                        if bThis_ShapeNumber = 14 then bDirectionToGo = 2 'sud
                    end if
            end select
        end if
        
        if bThis_ShapeNumber = 13 then
            if game_iScaredTimer < 121 then
                if (game_iScaredTimer AND 8) = 0 then sprite bMonsterNum COLOR 15 else sprite bMonsterNum COLOR 6 'alterna fra grigio chiaro (15) e blu (6)
            end if
        end if
 
    else
        aMonsters(bMonsterNum).bMovementTimer = aMonsters(bMonsterNum).bInitialMovementTimer
        
        if iThis_Coord_X = 24 then
           iThis_Coord_X = 288
        else
            if iThis_Coord_X = 288 then
                iThis_Coord_X = 24
            end if
        end if
        iThis_Map_X = shr(iThis_Coord_X, 3) : bThis_Map_Y = shr(bThis_Coord_Y, 3)

        bOppositeDirection = (bDirectionToGo + 2) AND 3

        'Di default, un Mostro va addosso a Pacman
        iTargetTile_X = pacman_iMap_X
        bTargetTile_Y = pacman_bMap_Y
        select case bThis_ShapeNumber
            case 12
                select case bMonsterNum
                    case 1 'Mostro 1 punta a 8 caselle avanti a Pacman
                        iTargetTile_X = pacman_iMap_X + pacman_iDirection_X
                        bTargetTile_Y = pacman_bMap_Y + pacman_bDirection_Y
                    case 2 'Mostro 2 punta a 8 caselle INDIETRO a Pacman   
                        iTargetTile_X = pacman_iMap_X - pacman_iDirection_X
                        bTargetTile_Y = pacman_bMap_Y - pacman_bDirection_Y
                    case 3 'Mostro 3 punta a Pacman, MA se è "distante" meno di 12 (distanza "Manhattan"), scappa all'angolo in basso a sinistra
                        iThis_Distance = ABS(CINT(pacman_bMap_Y) - CINT(bThis_Map_Y)) + ABS(pacman_iMap_X - iThis_Map_X)
                        if iThis_Distance < 12 then
                            iTargetTile_X = 4
                            bTargetTile_Y = 20
                        end if
                end select
                'per sicurezza si controlla che la casella bersaglio finale non esca fuori dalla mappa...
                if iTargetTile_X < 3 then iTargetTile_X = 3
                if iTargetTile_X > 36 then iTargetTile_X = 36
                if bTargetTile_Y > 127 then bTargetTile_Y = 1
                if bTargetTile_Y > 20 then bTargetTile_Y = 20
            case 14
                if bThis_Map_Y = 8 then
                    iTargetTile_X = 19
                else
                    if iThis_Map_X < 19 then iTargetTile_X = 14 else iTargetTile_X = 25
                end if
                bTargetTile_Y = 8
        end select

        iShortestDistance = 32767
        
        for bThis_Direction = 0 to 3
            if bThis_Direction = bOppositeDirection then continue for
            
            iOffset_Map_X = iThis_Map_X + iDirections_X(bThis_Direction)
            bOffset_Map_Y = bThis_Map_Y + bDirections_Y(bThis_Direction)

            if (peek(wScreenTable(bOffset_Map_Y) + iOffset_Map_X) AND %00110000) = %00100000 then continue for
            
            iPartialDistance = ABS(CINT(bTargetTile_Y) - CINT(bOffset_Map_Y))
            iThis_Distance = iPartialDistance * iPartialDistance
            iPartialDistance = ABS(iTargetTile_X - iOffset_Map_X)
            iThis_Distance = iThis_Distance + (iPartialDistance * iPartialDistance)
            if bThis_ShapeNumber = 13 then iThis_Distance = 1424 - iThis_Distance

            if iThis_Distance < iShortestDistance then
                iShortestDistance = iThis_Distance
                bDirectionToGo = bThis_Direction
            end if
        next bThis_Direction
        
        if iShortestDistance = 32767 then bDirectionToGo = bOppositeDirection 'se il Mostro sta nel recinto, così può fare dietrofront
        
    end if

    '**** Momento del rilevamento della collisione! ****
    'https://www.youtube.com/watch?v=LwMNPEG4OPo
    dim FAST xD as INT, yD as INT FAST
    xD = ABS((iThis_Coord_X + 7) - (pacman_iCoord_X + 8))
    yD = ABS(CINT(bThis_Coord_Y + 7) - CINT(pacman_bCoord_Y + 8))
    if xD < 9 AND yD < 9 then
        select case bThis_ShapeNumber
            case 12
                game_bPacmanCaught = TRUE
            case 13
                aMonsters(bMonsterNum).bShapeNumber = 14 : sprite bMonsterNum SHAPE 14
                aMonsters(bMonsterNum).bInitialMovementTimer = 255
                aMonsters(bMonsterNum).bMovementTimer = 255
                game_dScore = game_dScore + 500d
                snd_bMonsterEaten_Timer = SND_MONSTER_EATEN_TIMER_START
                textat 31, 24, game_dScore
        end select
    end if
    
    if aMonsters(bMonsterNum).bMovementTimer then
        aMonsters(bMonsterNum).iCoord_X = iThis_Coord_X + shl(iDirections_X(bDirectionToGo), bStepMultiplier)
        aMonsters(bMonsterNum).bCoord_Y = bThis_Coord_Y + shl(bDirections_Y(bDirectionToGo), bStepMultiplier)
        aMonsters(bMonsterNum).bMovementTimer = aMonsters(bMonsterNum).bMovementTimer - 1
    else
        aMonsters(bMonsterNum).bMovementTimer = aMonsters(bMonsterNum).bInitialMovementTimer       
    end if
    aMonsters(bMonsterNum).bDirection = bDirectionToGo
end sub

sub scareTheMonsters() STATIC
    if aMonsters(0).bShapeNumber = 12 then
        aMonsters(0).bDirection = (aMonsters(0).bDirection + 2) AND 3
        aMonsters(0).bShapeNumber = 13
        sprite 0 SHAPE 13
        aMonsters(0).bInitialMovementTimer = 1
        aMonsters(0).bMovementTimer = 1
    end if
    sprite 0 COLOR 6 'blu
    
    if aMonsters(1).bShapeNumber = 12 then
        aMonsters(1).bDirection = (aMonsters(1).bDirection + 2) AND 3
        aMonsters(1).bShapeNumber = 13
        sprite 1 SHAPE 13
        aMonsters(1).bInitialMovementTimer = 1
        aMonsters(1).bMovementTimer = 1
    end if
    sprite 1 COLOR 6 'blu
    
    if aMonsters(2).bShapeNumber = 12 then
        aMonsters(2).bDirection = (aMonsters(2).bDirection + 2) AND 3
        aMonsters(2).bShapeNumber = 13
        sprite 2 SHAPE 13 
        aMonsters(2).bInitialMovementTimer = 1
        aMonsters(2).bMovementTimer = 1
    end if
    sprite 2 COLOR 6 'blu
    
    if aMonsters(3).bShapeNumber = 12 then
        aMonsters(3).bDirection = (aMonsters(3).bDirection + 2) AND 3
        aMonsters(3).bShapeNumber = 13
        sprite 3 SHAPE 13
        aMonsters(3).bInitialMovementTimer = 1
        aMonsters(3).bMovementTimer = 1
    end if
    sprite 3 COLOR 6 'blu
    
    game_iScaredTimer = 350 '7 secondi * 50 frame/sec = 350
    snd_bPowerDotEaten_Timer = SND_POWERDOT_EATEN_TIMER_START
end sub

sub restoreTheMonsters() STATIC
    if aMonsters(0).bShapeNumber = 13 then
        aMonsters(0).bShapeNumber = 12
        aMonsters(0).bInitialMovementTimer = 4
        aMonsters(0).bMovementTimer = 4
        sprite 0 SHAPE 12 COLOR aMonsters(0).bOriginalColour
    end if
    
    if aMonsters(1).bShapeNumber = 13 then
        aMonsters(1).bShapeNumber = 12
        aMonsters(1).bInitialMovementTimer = 4
        aMonsters(1).bMovementTimer = 4
        sprite 1 SHAPE 12 COLOR aMonsters(1).bOriginalColour
    end if
    
    if aMonsters(2).bShapeNumber = 13 then
        aMonsters(2).bShapeNumber = 12
        aMonsters(2).bInitialMovementTimer = 4
        aMonsters(2).bMovementTimer = 4
        sprite 2 SHAPE 12 COLOR aMonsters(2).bOriginalColour
    end if
    
    if aMonsters(3).bShapeNumber = 13 then
        aMonsters(3).bShapeNumber = 12
        aMonsters(3).bInitialMovementTimer = 4
        aMonsters(3).bMovementTimer = 4
        sprite 3 SHAPE 12 COLOR aMonsters(3).bOriginalColour
    end if

end sub

sub updatePacman() STATIC
    Dim bJoy2 as BYTE
    Dim wPacmanAddress as WORD
    bJoy2 = JOY(2)
    
    if (pacman_iCoord_X AND 7) <> 0 OR (pacman_bCoord_Y AND 7) then 'se Pacman non sta su una posizione multipla di 8...
        if (bJoy2 AND 4) AND pacman_iDelta_X = 1 then pacman_iDelta_X = -1 
        if (bJoy2 AND 8) AND pacman_iDelta_X = -1 then pacman_iDelta_X = 1 
        if (bJoy2 AND 1) AND pacman_bDelta_Y = 1 then pacman_bDelta_Y = CBYTE(-1)
        if (bJoy2 AND 2) AND pacman_bDelta_Y = CBYTE(-1) then pacman_bDelta_Y = 1
    else
        if (bJoy2 AND 12) <> 0 AND (bJoy2 AND 3) <> 0 AND (pacman_iDelta_X <> 0 OR pacman_bDelta_Y) then bJoy2 = 0
        
        if pacman_iCoord_X = 24 then
           pacman_iCoord_X = 288
        else
            if pacman_iCoord_X = 288 then
                pacman_iCoord_X = 24
            end if
        end if
        
        pacman_iMap_X = shr(pacman_iCoord_X, 3) : pacman_bMap_Y = shr(pacman_bCoord_Y, 3)

        wPacmanAddress = wScreenTable(pacman_bMap_Y) + pacman_iMap_X
        if (peek(wPacmanAddress) AND %11111110) = 30 then
            game_iDotsToEat = game_iDotsToEat - 1
            game_dScore = game_dScore + 10d
            if peek(wPacmanAddress) = 30 then
                call scareTheMonsters()
                game_dScore = game_dScore + 40d
            end if
            textat 31, 24, game_dScore
            poke wPacmanAddress, 29
            snd_bDotEaten_Timer = SND_DOT_EATEN_TIMER_START
        end if

        if (bJoy2 AND 1) then 'Bit #0 is set if joystick is being pulled up
            pacman_bDelta_Y = CBYTE(-1)
        end if 
        if (bJoy2 AND 2) then 'Bit #1 is set if joystick is being pulled down
            pacman_bDelta_Y = 1
        end if                
        if (bJoy2 AND 4) then 'Bit #2 is set if joystick is being pulled left
            pacman_iDelta_X = -1
        end if
        if (bJoy2 AND 8) then 'Bit #3 is set if joystick is being pulled right
            pacman_iDelta_X = 1
        end if
        
        if (peek(wPacmanAddress + pacman_iDelta_X) AND %00110000) = %00100000 then pacman_iDelta_X = 0
        if (peek(wScreenTable(pacman_bMap_Y + pacman_bDelta_Y) + pacman_iMap_X) AND %00110000) = %00100000 then pacman_bDelta_Y = 0
        
        if pacman_iDelta_X <> 0 AND pacman_bDelta_Y then 'se è possibile muoversi in diagonale...
            if (bJoy2 AND 12) then pacman_bDelta_Y = 0
            if (bJoy2 AND 3)  then pacman_iDelta_X = 0
        end if

    end if
    
    pacman_iCoord_X = pacman_iCoord_X + pacman_iDelta_X
    pacman_bCoord_Y = pacman_bCoord_Y + pacman_bDelta_Y

    pacman_bSpriteFrameNumber = pacman_bSpriteFrameNumber + 1 : pacman_bSpriteFrameNumber = pacman_bSpriteFrameNumber AND 7
    select case pacman_bDelta_Y
        case 255 '-1
            pacman_bSpriteNumber = 9 'sprite a nord
            pacman_bDirection_Y = CBYTE(-8)
            pacman_iDirection_X = 0
        case 0
            select case pacman_iDelta_X
                case -1
                    pacman_bSpriteNumber = 3 'sprite a ovest
                    pacman_bDirection_Y = 0
                    pacman_iDirection_X = -8
                case 0
                    pacman_bSpriteFrameNumber = 0 'reimposta il primo frame a zero (bocca chiusa)
                case 1
                    pacman_bSpriteNumber = 0 'sprite a est
                    pacman_bDirection_Y = 0
                    pacman_iDirection_X = 8
            end select
        case 1
            pacman_bSpriteNumber = 6 'sprite a sud
            pacman_bDirection_Y = 8
            pacman_iDirection_X = 0
    end select
end sub

sub drawActors() STATIC
    sprite 0 at aMonsters(0).iCoord_X + 21, aMonsters(0).bCoord_Y + 48
    sprite 1 at aMonsters(1).iCoord_X + 21, aMonsters(1).bCoord_Y + 48
    sprite 2 at aMonsters(2).iCoord_X + 21, aMonsters(2).bCoord_Y + 48
    sprite 3 at aMonsters(3).iCoord_X + 21, aMonsters(3).bCoord_Y + 48
    sprite 7 shape pacman_bSpriteNumber + bFrameAnimNumber(pacman_bSpriteFrameNumber) AT pacman_iCoord_X + 21, pacman_bCoord_Y + 48 'anziché + 24 (-3), anziché 50 (-2)
end sub

sub animatePowerPellets() STATIC
    if (game_bPowerPelletAnimTimer AND 7) then
    else
        poke $D87C, peek( $D87C) XOR 3
        poke $D89B, peek( $D89B) XOR 3
        poke $DA84, peek( $DA84) XOR 3
        poke $DAA3, peek( $DAA3) XOR 3
    end if
    game_bPowerPelletAnimTimer = game_bPowerPelletAnimTimer - 1
end sub

sub resetGameMap() STATIC
    memcpy @pacScreen, $8400, @pacScreenColor - @pacScreen
end sub

sub resetGameMapColours() STATIC
    memcpy @pacScreenColor, $D800, @pacCharset - @pacScreenColor
end sub

sub waitForNextFrame(bFrameQuantity as BYTE) STATIC
    do
        do until scan() < 220  : loop
        do until scan() >= 220 : loop
        bFrameQuantity = bFrameQuantity - 1
    loop while bFrameQuantity
end sub

sub waitForJoystick() STATIC
    do while JOY(2) : loop
    do until JOY(2) : loop
end sub

sub pacmanAppears() STATIC
    'prima di scrivere "ready!", mi salvo quello che c'è sotto...
    memcpy $85F1, $0400, 6 'la memoria "classica" del video è ora a disposizione come area d'appoggio
    textat 17, 12, "ready{92}", 7 'giallo - al carattere "£" (ASCII 92) c'è ridisegnato il punto esclamativo
    
    sprite 7 SHAPE 4 'la forma 4 è Pacman rivolto a sinistra con la bocca semi-aperta
    VOICE 1 ADSR 0, 0, 15, 9  WAVE PULSE  PULSE 2048 TONE 10000  ON  OFF
    For bAnimFrameCounter = 1 to 21
        if (bAnimFrameCounter AND 1) then
            sprite 7 ON
        else
            sprite 7 OFF
        end if
        call waitForNextFrame(2)
    next bAnimFrameCounter
    
    memset $D9F1, 6, 15 'si rimette a posto il colore grigio chiaro dei "puntini" da mangiare
    memcpy $0400, $85F1, 6 'si rimettono a posto gli effettivi "puntini" che c'erano prima
end sub

sub pacmanDies() STATIC
    VOICE 1 OFF
    VOICE 3 OFF
    
    VOICE 2 OFF  ADSR 0, 0, 15, 9  WAVE PULSE  PULSE 2048  TONE 1250  ON  OFF
    
    For bAnimFrameCounter = 1 to 21
        if (bAnimFrameCounter AND 1) then
            sprite 7 OFF
        else
            sprite 7 ON
        end if
        call waitForNextFrame(2)
    next bAnimFrameCounter

    call waitForNextFrame(30)
end sub

sub levelCompleted() STATIC
    VOICE 1 OFF
    VOICE 2 OFF
    VOICE 3 OFF
    call waitForNextFrame(90)
    
    'spegne tutti i Mostri
    sprite 0 OFF
    sprite 1 OFF
    sprite 2 OFF
    sprite 3 OFF
    for bAnimFrameCounter = 1 to 10
        if (bAnimFrameCounter AND 1) then
            memset $D800, 880, 1 'colora la mappa di bianco
        else
            memset $D800, 880, 6 'colora la mappa di blu
        end if
        call waitForNextFrame(15)
    next bAnimFrameCounter
    
    call waitForNextFrame(75)
end sub

sub titleScreen() STATIC
    memset $D800, 880, 6 'imposta i caratteri tutti blu
    call resetGameMap()
    
    textat 15, 4, "jj pacman{92}", 1 'bianco - ASCII 92 "£" ridisegnato come punto esclamativo
    
    textat 10, 8, "graphics  and map by", 1 'bianco
    textat 14, 9, "agpx@itch{95}io", 7 'giallo - ASCII 95 (freccia a sinistra) ridisegnato come "dot" da mangiare
    
    textat 6, 11, "additional graphics and code", 1 'bianco
    textat 6, 12, "rewriting by ", 1 'bianco
    textat 19, 12, "jjflash@itch{95}io", 7 'giallo - ASCII 95 (freccia a sinistra) ridisegnato come "dot" da mangiare
    
    textat 7, 14, "xc basic 3 by ", 1 'bianco
    textat 21, 14, "csaba fekete", 7 'giallo
    textat 14, 15, "xc-basic{95}net", 5 'verde
    
    textat 5, 18, "use joystick in port 2 to play", 3 'ciano
    
    textat 31, 21, "rev01", 11 'grigio scuro
    
    call waitForJoystick()
end sub

call titleScreen()

textat 5, 23, "tries", 7 'giallo
textat 30, 23, "score", 13 'verde chiaro

do 'loop di *** INIZIO PARTITA ***
    game_bPacmanTries = 3
    game_dScore = 0d
    game_iDotsToEat = DOTS_NUM

    call resetGameMapColours()
    call resetGameMap()
    textat 31, 24, game_dScore, 1 'bianco
    
    do 'loop di ** INIZIO TENTATIVO (VITA) **
        game_bPacmanCaught = FALSE
        game_iScaredTimer = 0
        
        call resetMonsters()
        call resetPacman()
        
        textat 7, 24, game_bPacmanTries, 1 'bianco
        
        call drawActors()
        call pacmanAppears()
        
        call initSounds()
        
        call waitForNextFrame(1)

        do 'loop **** PRINCIPALE! **** -----------------------------------------------------------------------------------------
            bShortFrame = TRUE
            
            call drawActors()
            call animatePowerPellets()
          
            call soundHandler()

            call updateMonster(0)
            call updateMonster(1)
            call updateMonster(2)

            if scan() < 220 then bShortFrame = FALSE
            call updateMonster(3)
            if scan() < 220 then bShortFrame = FALSE

            if game_bPacmanCaught then exit do '-----USCITA ANTICIPATA PER PACMAN ACCHIAPPATO!
            call updatePacman()

            if game_iScaredTimer <> 0 then
                game_iScaredTimer = game_iScaredTimer - 1
                if game_iScaredTimer = 0 then call restoreTheMonsters()
            end if
            
            if bShortFrame then
                do until scan() < 220 : loop
            end if

            do until scan() >= 220 : loop 
  
        loop until game_iDotsToEat = 0 'FINE loop **** PRINCIPALE! **** -------------------------------------------------------------
        
        if game_bPacmanCaught then
            call pacmanDies()
            game_bPacmanTries = game_bPacmanTries - 1
        else
            call levelCompleted()
            game_iDotsToEat = DOTS_NUM
            call resetGameMapColours()
            call resetGameMap()
        end if
        
    loop while game_bPacmanTries '---FINE--- loop di ** INIZIO TENTATIVO (VITA) **
    
    textat 7, 24, game_bPacmanTries 'giusto per scrivere "0" nei Tries e far capire perché è game over...
    textat 15, 8, "game  over", 2 'rosso
    textat 13, 12, "try once more{92}", 3 'ciano - ASCII 92 - "£" ridefinita a punto esclamativo
    
    call waitForJoystick()

loop '---FINE--- loop di *** INIZIO PARTITA ***

'.........................................................................

pacScreen:
incbin "pacMap.bin"
pacScreenColor:
incbin "pacMapColour.bin"
pacCharset:
incbin "pacChars.bin"
pacSprites:
incbin "pacSprites.bin"
endOfData:

'.........................................................................

