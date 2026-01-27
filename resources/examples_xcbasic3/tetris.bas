  REM -- TETRIS
  REM -- An XC=BASIC tutorial game
  
  CONST VICII_RASTER = $d012
    
  INCLUDE "xcb-ext-joystick.bas"
  
  REM -- Clear the screen
  MEMSET 1024, 1000, 32
  REM -- Clear color RAM
  MEMSET 55296, 1000, 0
  
  REM -- Set border and background
  POKE 53280, 13 : POKE 53281, 1
  
  REM -- Switch to upper case
  POKE 53272, 21
  
  REM -- Disable SHIFT + Commodore key
  POKE 657,128 
  
  REM -- Draw the playfield using a series of PRINT statements
  PRINT "{GRAY}"
  CURPOS 14, 3
  PRINT "{REV_ON}{176}{195}{195}{195}{195}{195}{195}{195}{195}{195}{195}{174}{REV_OFF}"
  FOR i! = 4 TO 23
    CURPOS 14, i!
    PRINT "{REV_ON}{194}{REV_OFF}          {REV_ON}{194}{REV_OFF}" : REM 10 spaces in the middle
  NEXT
  CURPOS 14, 24
  PRINT "{REV_ON}{173}{195}{195}{195}{195}{195}{195}{195}{195}{195}{195}{189}{REV_OFF}";
  CURPOS 0,0
  
  
  REM -- Write texts
  TEXTAT 27, 10, "level:"
  TEXTAT 27, 13, "score:"
  TEXTAT 27, 16, "hi:"
  TEXTAT 27, 19, "next:"
  
  REM -- Set color where numbers will be displayed
  MEMSET 55763, 2, 5
  MEMSET 55883, 6, 5
  MEMSET 56003, 6, 5
  
  REM -- The playfield, an array of 25 integers
  DIM playfield[25]
  REM -- Level (1-10)
  DIM level!
  REM -- Current score
  DIM score%
  REM -- Highest score of the day
  DIM hiscore%
  REM -- Game status: 0 = game on, 1 = game lost
  DIM game_status!
  REM -- How many rows have been cleared (reset above 100)
  DIM ttl_rows_cleared!
  
  REM -- Shape of current piece
  DIM shape
  REM -- Shape number of current piece
  DIM shape_no!
  REM -- Color of the current piece
  DIM shape_color!
  REM -- X, Y position and rotation of current piece
  DIM piece_x!
  DIM piece_y!
  DIM piece_r!
  
  
  REM -- Shape of next piece
  DIM nxt_shape
  REM -- Shape number of next piece
  DIM nxt_shape_no!
  

  REM -- Initialize the playfield
  REM -- Called when starting a new game
  PROC clear_playfield
    REM -- initialize the playfield
    FOR i! = 0 TO 23
      \playfield[i!] = %0010000000000100
    NEXT
    \playfield[24] = %0011111111111100
    REM -- empty the playfield on screen
    FOR i! = 4 TO 23
      TEXTAT 15, i!, "          " : REM 10 spaces
    NEXT
  ENDPROC
  
  FUN get_shape(shape_no!, rotation!)
    RETURN shapes[LSHIFT!(shape_no!, 2) + rotation!]
    
    REM -- Shapes of all pieces in all rotations
    DATA shapes[] = %0100010001000100, %0000111100000000, %0010001000100010, %0000000011110000, ~
                    %0100010011000000, %1000111000000000, %0110010001000000, %0000111000100000, ~
                    %0100010001100000, %0000111010000000, %1100010001000000, %0010111000000000, ~
                    %1100110000000000, %1100110000000000, %1100110000000000, %1100110000000000, ~
                    %0000011011000000, %1000110001000000, %0110110000000000, %0100011000100000, ~
                    %0000111001000000, %0100110001000000, %0100111000000000, %0100011001000000, ~
                    %0000110001100000, %0100110010000000, %1100011000000000, %0010011001000000
  ENDFUN
  
  REM -- Extract a single row from the shape
  FUN extract_row(shape, row!, x!)
    REM -- Step 1: mask the nibble
    REM -- Step 2: move it to the left end
    REM -- Step 3: move it right by the piece's  X position    
    RETURN RSHIFT(LSHIFT(shape & mask[row!], bitpos![row!]), x!)
    
    REM -- Helper data for bitwise calculations
    DATA mask[] = %1111000000000000, %0000111100000000, ~
                  %0000000011110000, %0000000000001111
    DATA bitpos![] = 0, 4, 8, 12
  ENDFUN
  
  REM -- Check if the piece overlaps the playfield
  REM -- at the given position
  REM -- Returns 1 or 0 (true or false)
  FUN overlaps!(shape_no!, rotation!, x!, y!)
    REM -- Get shape by number and rotation
    tmp_shape = get_shape(shape_no!, rotation!)
    REM -- Check row by row
    FOR i! = 0 TO 3
      playfield_row = \playfield[i! + y!]
      piece_row = extract_row(tmp_shape, i!, x!)
      IF piece_row & playfield_row <> 0 THEN RETURN 1
    NEXT
    RETURN 0
  ENDFUN
  
  REM -- Draw or erase the current shape on screen at the given position
  REM -- draw! > 0 means draw, draw! = 0 means erase
  PROC draw_shape(shape, x!, y!, color!, draw!)
    REM -- This is the memory address where we can start drawing
    REM -- Everything before is invisible
    CONST VISIBLE_AREA_START = 1199
    REM -- Calculate start addresses
    screen_addr = screen_address[y!] + x!
    REM -- Iterate through all bits in the shape
    FOR bit_pos! = 0 TO 15
      REM -- Calculate where to draw
      addr = screen_addr + block_offset![bit_pos!]
      REM -- Only draw if it's in the visible area
      IF addr >= VISIBLE_AREA_START THEN
        REM -- If bit in shape is set
        IF shape & LSHIFT(CAST(1), bit_pos!) <> 0 THEN
          IF draw! = 0 THEN char! = 32 ELSE char! = 160
          REM -- Draw char
          POKE addr, char!
          REM -- Set color
          REM -- Add the distance between screen RAM and Color RAM
          REM -- To get color address without offsets calculating again
          POKE addr + 54272, color!
        ENDIF        
      ENDIF
    NEXT
    REM -- The address in Screen RAM for each row on playfield
    DATA screen_address[] = 1036, 1076, 1116, 1156, 1196, 1236, 1276, 1316, 1356, 1396, 1436, 1476, ~
                            1516, 1556, 1596, 1636, 1676, 1716, 1756, 1796, 1836, 1876, 1916, 1956, 1996
    REM -- For each bit in the shape there is a matching offset where the 
    REM -- character should be drawn relative to the top left of the shape.
    REM -- This offset, added to the screen address will give us where to 
    REM -- plot a character.
    REM -- Note that we're going backwards as Bit #0 is the bottom right position
    DATA block_offset![] = 123, 122, 121, 120, 83, 82, 81, 80, 43, 42, 41, 40, 3, 2, 1, 0
  ENDPROC
  
  REM -- Draw the piece preview
  REM -- Effectively uses the draw_shape routine above
  PROC draw_preview
    REM -- Clear the preview area
    FOR i! = 0 TO 4 : TEXTAT 33, 19 + i!, "    " : NEXT
    REM -- Draw the shape in the appropriate color
    CALL draw_shape(\nxt_shape, 21, 19, \colors![\nxt_shape_no!], 1)
  ENDPROC

  REM -- Make a piece part of the playfield
  PROC lock_piece
    FOR i! = 0 TO 3
      row_no! = \piece_y! + i!
      REM -- Row 23 is the last where we want to do this
      IF row_no! <= 23 THEN
        REM -- Get a row from the piece and merge with playfield
        piece_row = extract_row(\shape, i!, \piece_x!)
        \playfield[row_no!] = \playfield[row_no!] | piece_row
      ENDIF
    NEXT
  ENDPROC
  
  REM -- Clear a row and cascade everything from above
  PROC clear_row(row_no!)
    screen_pos = screen_address[row_no!]
    REM -- Clear row on screen
    MEMSET screen_pos, 10, 32
    REM -- Clear wor in playfield
    \playfield[row_no!] = %0010000000000100
    REM -- Wait approximately half of a sec
    FOR i! = 0 to 25 : WATCH \VICII_RASTER, 255 : NEXT
    REM -- Bring everything down
    FOR row = row_no! - 1 TO 4 STEP -1
      from_pos = screen_address[row]
      targ_pos = from_pos + 40
      REM -- Bring one row down on screen
      MEMCPY from_pos, targ_pos, 10
      REM -- Bring one row down in the playfield
      \playfield[row + 1] = \playfield[row]
    NEXT
    REM -- Clear upper row
    MEMSET 1199, 10, 32
    
    REM -- The address in Screen RAM for each row on playfield
    REM -- Slightly different from as above because we only
    REM -- care about the middle 10 chars of the playfield
    DATA screen_address[] = 1039, 1079, 1119, 1159, 1199, 1239, 1279, 1319, 1359, 1399, 1439, 1479, ~
                            1519, 1559, 1599, 1639, 1679, 1719, 1759, 1799, 1839, 1879, 1919, 1959, 1999
  ENDPROC
  
  REM --
  REM -- The program loop
  REM --
  DISABLEIRQ
  WHILE 1 = 1
  
    TEXTAT 27, 6, "press fire"
  
    REM -- Wait for fire button
    REPEAT
    UNTIL joy_1_fire!() = 1
  
    REM -- Clear messages
    TEXTAT 27, 4, "         "
    TEXTAT 27, 5, "           "
    TEXTAT 27, 6, "          "
  
    REM -- Start new game. Initialize variables
    level! = 1
    delay! = 10
    TEXTAT 26, 11, "  "
    TEXTAT 26, 11, level!
    CALL clear_playfield
    game_status! = 0
    ttl_rows_cleared! = 0
    score% = 0.0
    
    REM -- Get next shape and display preview
    nxt_shape_no! = CAST!(RND%() * 7.0)
    nxt_shape = get_shape(nxt_shape_no!, 0)
    CALL draw_preview
    
    REM --
    REM -- The game loop
    REM --
    REPEAT
      REM -- Copy next shape to current shape
      shape_no! = nxt_shape_no!
      shape = nxt_shape
      shape_color! = colors![shape_no!]
      
      REM -- Get next shape and display preview
      nxt_shape_no! = CAST!(RND%() * 7.0)
      nxt_shape = get_shape(nxt_shape_no!, 0)
      CALL draw_preview
      
      REM -- Get current shape and put piece
      REM -- on top of the playfield
      piece_x! = 7
      piece_y! = 0
      piece_r! = 0
      
      REM -- Display current score
      TEXTAT 27, 14, score%
    
      REM --
      REM -- The update loop
      REM --
      REPEAT
        REM -- Draw the shape
        CALL draw_shape(shape, piece_x!, piece_y!, shape_color!, 1)
        REM -- The player has four chances to move the piece
        REM -- before it falls one position
        FOR i! = 0 TO 3
          REM -- Check if there's input from joystick
          IF PEEK!(JOY_PORT1) <> 255 THEN
            REM -- Copy piece position to temp variables to be able
            REM -- to check for overlapping without actually
            REM -- updating the piece
            tmp_x! = piece_x! : tmp_y! = piece_y! : tmp_r! = piece_r!
            REM -- Check what input comes from joystick
            IF joy_1_left!()  = 1 THEN DEC tmp_x!
            IF joy_1_right!() = 1 THEN INC tmp_x!
            IF joy_1_down!()  = 1 THEN INC tmp_y!
            IF joy_1_fire!()  = 1 THEN \tmp_r! = (\piece_r! + 1) & %00000011
            REM -- Check if move is possible
            IF overlaps!(shape_no!, tmp_r!, tmp_x!, tmp_y!) = 0 THEN
              REM -- It is possible, erase the piece off of screen
              CALL draw_shape(shape, piece_x!, piece_y!, shape_color!, 0)      
              REM -- Update piece position and shape and draw again
              piece_x! = tmp_x! : piece_y! = tmp_y! : piece_r! = tmp_r!
              shape = get_shape(shape_no!, piece_r!)
              CALL draw_shape(shape, piece_x!, piece_y!, shape_color!, 1)      
            ENDIF
          ENDIF
          FOR j! = 0 TO delay! : WATCH VICII_RASTER, 255 : NEXT
        NEXT
        REM -- Erase the shape
        CALL draw_shape(shape, piece_x!, piece_y!, shape_color!, 0)
        REM -- Fall piece by one
        INC piece_y!
      UNTIL overlaps!(shape_no!, piece_r!, piece_x!, piece_y!) = 1
      REM --
      REM -- End of update loop
      REM --
      
      
      REM -- The shape hit the bottom
      REM -- A little correction first - the piece is currently erased!
      DEC piece_y! : CALL draw_shape(shape, piece_x!, piece_y!, shape_color!, 1)
      
      REM -- Lock piece and make it part of the playfield
      CALL lock_piece
      
      REM -- Check if we have topped out
      IF piece_y! > 4 THEN
        REM -- ..no we haven't
        REM -- Check if there are rows to be cleared
        REM -- and remove them
        rows_cleared! = 0
        row_no! = piece_y! + 3 : IF row_no! >= 24 THEN row_no! = 23
        REPEAT
          REM -- Check if row is full
          IF playfield[row_no!] = %0011111111111100 THEN
            CALL clear_row(row_no!)
            INC rows_cleared!
          ELSE
           DEC row_no!
          ENDIF
        UNTIL row_no! = piece_y!
        
        REM -- Update score and check if it's
        REM -- time for next level
        score% = score% + bonus%[rows_cleared!] * CAST%(level!)
        ttl_rows_cleared! = ttl_rows_cleared! + rows_cleared!
        IF ttl_rows_cleared! >= 100 THEN
          INC level!
          delay! = 11 - level!
          TEXTAT 27, 11, level!
          ttl_rows_cleared! = ttl_rows_cleared! - 100
        ENDIF
      ELSE 
        REM -- ...yes, topped out
        REM -- Assigning 1 to game_status will effectively
        REM -- exit the loop
        game_status! = 1
      ENDIF

      REM -- Everything is done, repeat for next shape
      REM -- or exit loop
    UNTIL game_status! = 1
    REM --
    REM -- End of game loop
    REM --
    
    REM -- Game over. Update hiscore and messages
    TEXTAT 27, 4, "game over"
    IF score% > hiscore% THEN
      hiscore% = score%
      TEXTAT 27, 5, "new hiscore"
      TEXTAT 27, 17, hiscore%
    ENDIF
    
  ENDWHILE
  REM -- Program loop ends here
                  
  REM -- Piece color codes
  DATA colors![] = 14, 6, 8, 7, 5, 4, 2
  
  REM -- Bonus added to the score when clearing
  REM --           0,    1,    2,     3,   4 rows
  DATA bonus%[] = 0.0, 40.0, 100.0, 300.0, 1200.0