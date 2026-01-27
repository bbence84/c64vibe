' -----------------------------------
' -- PURALAX!
' --
' -- C64 port of the game found at
' -- http://www.puralax.com/
' --
' -- Written in XC=BASIC
' -- by Csaba Fekete
'
' porting from XCB2, a bit of optimizing & additional comments by @jjflash@mastodon.social
' -----------------------------------

OPTION FASTINTERRUPT

const RASTER_LINE = $D012

const LEVEL_COUNT = 25

const SPR_SHAPE_SQUA = 159
const SPR_SHAPE_FRAM = 164

const LEVEL_SIZE_SMALL = 0
const LEVEL_SIZE_BIG = 1

' -----------------------------------
' -- global vars
' -----------------------------------

Dim current_level_no as BYTE 
Dim current_target_color as BYTE
Dim current_level_size as BYTE
dim current_level_colors(64) as BYTE
dim current_level_dots(64) as BYTE
Dim current_level_shifted as BYTE

Dim cursor_posx as BYTE : Dim cursor_posy as BYTE

Dim Spr0_Shape as BYTE
Dim Spr0_X as WORD
Dim Spr0_Y as BYTE

goto start

'DATA variables originally declared at the bottom of the program
Dim logo(36) as BYTE @loc_logo
Dim logo_colors(36) as BYTE @loc_logo_colors
Dim square_pattern(16) as BYTE @loc_square_pattern
Dim square_pattern_sm(9) as BYTE @loc_square_pattern_sm
Dim square_pos(40) as WORD @loc_square_pos
Dim square_pos_sm(64) as WORD @loc_square_pos_sm 
Dim levelpass(100) as BYTE @loc_levelpass 
Dim levelsettings(25) as BYTE @loc_levelsettings 
Dim leveldata(1600) as BYTE @loc_leveldata


' -----------------------------------
' -- music and graphics data
' -----------------------------------

origin $1000
incbin "another_time.sid"

origin $2000
incbin "charset_inv.bin"

origin $2600
incbin "sprites.bin"

' -----------------------------------
' -- clear the screen
' -----------------------------------

sub cls() STATIC
  poke 646, 15 'foreground, light grey
  sys $E544 FAST 'clear screen
end sub

' -----------------------------------
' - Configure sprites
' -----------------------------------

sub configure_sprites() STATIC
    ' all sprites off for now
    ' sprites double size
    ' single color sprites
    SPRITE 0 OFF XYSIZE 1, 1
end sub

' -----------------------------------
' -- draw one square in the given 
' -- position
' -----------------------------------

sub draw_square(var_pos as BYTE, color as BYTE, dots as BYTE) STATIC
  dim offset as WORD : offset = square_pos(var_pos)
  if offset = 0 then exit sub
  offset = offset + cword(current_level_shifted) * 86
  Dim color_offset as WORD : color_offset = offset + $D400
  Dim char as BYTE : char = 0
  for i as BYTE = 0 to 3
    for j as BYTE = 0 to 3
      poke offset, square_pattern(char)
      poke color_offset, color
      offset = offset + 1
      color_offset = color_offset + 1
      char = char + 1
    next j
    offset = offset + 36
    color_offset = color_offset + 36
  next i
  offset = square_pos(var_pos) + cword(current_level_shifted) * 86
  if dots = 0 then exit sub
  poke offset, 79
  if dots = 1 then exit sub
  if dots = 2 then poke offset + 1, 80 else poke offset + 1, 81
end sub

' -----------------------------------
' -- draw one small square in the  
' -- given position
' -----------------------------------

sub draw_square_sm(var_pos as BYTE, color as BYTE, dots as BYTE) STATIC
  dim offset as WORD : offset = square_pos_sm(var_pos)
  dim color_offset as WORD : color_offset = offset + $D400
  dim char as BYTE : char = 0
  for i as BYTE = 0 to 2
    for j as BYTE = 0 to 2
      poke offset, square_pattern_sm(char)
      poke color_offset, color
      offset = offset + 1
      color_offset = color_offset + 1
      char = char + 1
    next j
    offset = offset + 37
    color_offset = color_offset + 37
  next i
  offset = square_pos_sm(var_pos)
  if dots = 0 then exit sub
  poke offset, 79
  if dots = 1 then exit sub
  if dots = 2 then poke offset + 1, 80 else poke offset + 1, 81
end sub

' -----------------------------------
' - load level
' -----------------------------------

sub load_level(level_no as BYTE) STATIC
  dim ptr as WORD : ptr = cword(level_no) * 64
  dim settings as BYTE : settings = levelsettings(level_no)
  current_level_size = LEVEL_SIZE_SMALL
  current_level_shifted = 0
  current_target_color = settings AND %00001111
  Dim leveltype as BYTE : leveltype = shr(settings, 4)
  
  if leveltype = 2 then current_level_size = LEVEL_SIZE_BIG
  if leveltype = 1 then current_level_size = LEVEL_SIZE_SMALL : current_level_shifted = 1

  for i as BYTE = 0 to 63
    current_level_colors(i) = leveldata(ptr) AND %00001111
    current_level_dots(i) = shr(leveldata(ptr), 4)
    ptr = ptr + 1
  next i
  cursor_posx = 3 : cursor_posy = 2
end sub

' -----------------------------------
' - draw the current level
' -----------------------------------

sub draw_level() STATIC
  Dim password$ as STRING * 4 'original XCB2 code -> dim buffer![5] : password$ = @buffer!
  Dim all_passes_ptr as WORD : all_passes_ptr = @loc_levelpass 'original XCB2 code -> all_passes$ = @\levelpass!
  Dim passindex as WORD
  poke @password$, 4 'string is not initialized...

  call cls()
  if current_level_size = LEVEL_SIZE_SMALL then gosub draw_squares else gosub draw_squares_sm

  textat  0, 24, "level"
  textat  6, 24, current_level_no + 1
  textat 16, 24, "target"
  textat 31, 24, "pass"

  passindex = shl(cword(current_level_no), 2)
  memcpy all_passes_ptr + passindex, @password$ + 1, 4 'original XCB2 code -> strncpy password$, all_passes$ + passindex, 4
  textat 36, 24, password$
  
  charat 23, 24, 78, current_target_color
  
  Spr0_X = 167 + current_level_shifted * 48 - current_level_size * 8
  Spr0_Y = 121 + current_level_shifted * 16 - current_level_size * 24
  Spr0_Shape = SPR_SHAPE_FRAM - current_level_size * 6
  SPRITE 0 ON SHAPE Spr0_Shape AT Spr0_X, Spr0_Y COLOR 1 'white

  exit sub

  draw_squares:
    for i as byte = 0 to 39
      call draw_square(i, current_level_colors(i), current_level_dots(i))
    next i
    return

  draw_squares_sm:
    for i as byte = 0 to 63
      call draw_square_sm(i, current_level_colors(i), current_level_dots(i))
    next i
    return
end sub

' -----------------------------------
' - start music
' -----------------------------------

sub start_music() STATIC
  const CONF_MUSIC  = $1000
  const MUSIC_ENTRY = $1003
  CONST ACCU = $030C ' C64 and VIC-20 only

  ON RASTER 228 GOSUB irq_routine

  poke ACCU, 0
  SYS CONF_MUSIC

  RASTER INTERRUPT ON
  
  exit sub

  irq_routine:
    SYS MUSIC_ENTRY FAST
    return
end sub

' -----------------------------------
' - set color/dots under cursor
' -----------------------------------

sub set_under_cursor(color as BYTE, dots as BYTE) STATIC
  Dim var_pos as BYTE : var_pos = cursor_posy * 8 + cursor_posx
  current_level_colors(var_pos) = color
  current_level_dots(var_pos) = dots
  if current_level_size = LEVEL_SIZE_SMALL then 
    call draw_square(var_pos, color, dots)
  else
    call draw_square_sm(var_pos, color, dots)
  end if
end sub

' -----------------------------------
' - paint all neighbours to same
' - color recursively
' -
' - some vars were moved out to
' - the global scope to prevent
' - stack overflow
' -----------------------------------

Dim pn_ocolor as BYTE
Dim pn_tcolor as BYTE

sub paint_neighbours(posx as BYTE, posy as BYTE)
  STATIC pn_pos as BYTE
  STATIC pn_color as BYTE
  
  if posy > 0 then posy = posy - 1 : gosub test : posy = posy + 1
  if posx < 7 then posx = posx + 1 : gosub test : posx = posx - 1
  if posy < 7 then posy = posy + 1 : gosub test : posy = posy - 1
  if posx > 0 then posx = posx - 1 : gosub test : posx = posx + 1 
  exit sub

  test:
    pn_pos = posy * 8 + posx
    pn_color = current_level_colors(pn_pos)
    if pn_color <> pn_ocolor OR pn_color = pn_tcolor then return
    current_level_colors(pn_pos) = pn_tcolor
    
    if current_level_size = LEVEL_SIZE_SMALL then 
      call draw_square(pn_pos, pn_tcolor, current_level_dots(pn_pos))
    else 
      call draw_square_sm(pn_pos, pn_tcolor, current_level_dots(pn_pos))
    end if
          
    call paint_neighbours(posx, posy)
    return
end sub

' -----------------------------------
' - test if level is done
' -----------------------------------

sub test_level_done(result as WORD) STATIC
  Dim nonmatching as BYTE : nonmatching = 0
  Dim color as BYTE
  
  for i as BYTE = 0 to 63
    color = current_level_colors(i)
    if color <> current_target_color and color <> $0b then
      if color <> $0c then nonmatching = nonmatching + 1
    end if
  next i
  if nonmatching = 0 then poke result, 1 else poke result, 0
end sub

' -----------------------------------
' - test if level is stuck
' -----------------------------------

sub test_level_stuck(result as WORD) STATIC
  Dim dots as BYTE : dots = 0
  for i as BYTE = 0 to 63
    dots = dots + current_level_dots(i)
  next i
  if dots > 0 then poke result, 0 else poke result, 1
end sub

' -----------------------------------
' - play level
' - arg success will be set to 0 or 1
' -----------------------------------

sub play_level(success as WORD) STATIC
  Dim boundary_x as BYTE
  Dim boundary_y as BYTE
  Dim distance as BYTE
  Dim shapeoffset as BYTE
  Dim sq_selected as BYTE
  Dim lstate as BYTE
  Dim var_joy as BYTE
  Dim previous_joy as BYTE
  Dim var_pos as BYTE
  Dim color as BYTE
  Dim dots as BYTE
  Dim neighbour_pos as BYTE
  Dim neighbour_color as BYTE
  Dim neighbour_dots as BYTE

  if current_level_size = LEVEL_SIZE_BIG then
    boundary_x = 7 : boundary_y = 7 : distance = 24 : shapeoffset = 250
  else
    boundary_x = 6 : boundary_y = 4 : distance = 32 : shapeoffset = 0
  end if

  sq_selected = 0
  lstate = 0
  loop:
    previous_joy = var_joy : var_joy = peek( $DC00)
    if var_joy = 126 then gosub move_up : goto ack_move
    if var_joy = 125 then gosub move_down : goto ack_move
    if var_joy = 119 then gosub move_right : goto ack_move
    if var_joy = 123 then gosub move_left : goto ack_move
    if var_joy = 111 and previous_joy <> 111 then
        if sq_selected = 0 then gosub select_square : goto ack_move
        if sq_selected = 1 then gosub deselect_square : goto ack_move
    end if
    goto loop
    ack_move:
      for j as WORD = 0 to 1000 : next j
    call test_level_done(@lstate)
    if lstate = 1 then poke success, 1 : return
    call test_level_stuck(@lstate)
    if lstate = 1 then poke success, 0 : return
  goto loop

  move_up:
    if cursor_posy = 0 then return
    if sq_selected = 1 then goto bring_up
    for i as BYTE = 1 to distance
      gosub wait_frame
      Spr0_Y = Spr0_Y - 1
      SPRITE 0 AT Spr0_X, Spr0_Y
    next i
    cursor_posy = cursor_posy - 1
    return

  move_down:
    if cursor_posy = boundary_y then return
    if sq_selected = 1 then goto bring_down
    for i as BYTE = 1 to distance
      gosub wait_frame
      Spr0_Y = Spr0_Y + 1
      SPRITE 0 AT Spr0_X, Spr0_Y
    next i
    cursor_posy = cursor_posy + 1
    return

  move_right:
    if cursor_posx = boundary_x then return
    if sq_selected = 1 then goto bring_right
    for i as BYTE = 1 to distance
      gosub wait_frame
      Spr0_X = Spr0_X + 1
      SPRITE 0 AT Spr0_X, Spr0_Y
    next i
    cursor_posx = cursor_posx + 1
    return

  move_left:
    if cursor_posx = 0 then return
    if sq_selected = 1 then goto bring_left
    for i as BYTE = 1 to distance
      gosub wait_frame
      Spr0_X = Spr0_X - 1
      SPRITE 0 AT Spr0_X, Spr0_Y
    next i
    cursor_posx = cursor_posx - 1
    return

  select_square:
    var_pos = cursor_posy * 8 + cursor_posx
    color = current_level_colors(var_pos)
    if color = $0b OR color = $0c then return
    dots = current_level_dots(var_pos)
    if dots = 0 then return
    Spr0_Shape = SPR_SHAPE_SQUA + shapeoffset + dots
    SPRITE 0 COLOR color SHAPE Spr0_Shape
    sq_selected = 1 
    return

  deselect_square:
    Spr0_Shape = SPR_SHAPE_FRAM + shapeoffset
    SPRITE 0 COLOR 1 SHAPE Spr0_Shape
    sq_selected = 0
    return

  bring_up:
    neighbour_pos = (cursor_posy - 1) * 8 + cursor_posx
    neighbour_color = current_level_colors(neighbour_pos)
    neighbour_dots = current_level_dots(neighbour_pos)
    var_pos = cursor_posy * 8 + cursor_posx
    dots = current_level_dots(var_pos)
    color = current_level_colors(var_pos)
    if neighbour_color = $0b OR neighbour_color = color then return
    if neighbour_color = $0c then gosub bring_up_onto_grey else gosub bring_up_onto_color
    return

    bring_up_onto_grey:
      call set_under_cursor( $0c, 0)
      for i as BYTE = 1 to distance
        gosub wait_frame
        Spr0_Y = Spr0_Y - 1
        SPRITE 0 AT Spr0_X, Spr0_Y
      next i
      cursor_posy = cursor_posy - 1
      call set_under_cursor(color, dots - 1)
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return

    bring_up_onto_color:
      call set_under_cursor(color, dots - 1)
      cursor_posy = cursor_posy - 1
      call set_under_cursor(color, neighbour_dots)
      pn_ocolor = neighbour_color
      pn_tcolor = color
      call paint_neighbours(cursor_posx, cursor_posy)
      cursor_posy = cursor_posy + 1
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return
  ' -- bring_up end

  bring_down:
    neighbour_pos = (cursor_posy + 1) * 8 + cursor_posx
    neighbour_color = current_level_colors(neighbour_pos)
    neighbour_dots = current_level_dots(neighbour_pos)
    var_pos = cursor_posy * 8 + cursor_posx
    dots = current_level_dots(var_pos)
    color = current_level_colors(var_pos)
    if neighbour_color = $0b OR neighbour_color = color then return
    if neighbour_color = $0c then gosub bring_down_onto_grey else gosub bring_down_onto_color
    return

    bring_down_onto_grey:
      call set_under_cursor( $0c, 0)
      for i as BYTE = 1 to distance
        gosub wait_frame
        Spr0_Y = Spr0_Y + 1
        SPRITE 0 AT Spr0_X, Spr0_Y
      next i
      cursor_posy = cursor_posy + 1
      call set_under_cursor(color, dots - 1)
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return

    bring_down_onto_color:
      call set_under_cursor(color, dots - 1)
      cursor_posy = cursor_posy + 1
      call set_under_cursor(color, neighbour_dots)
      pn_ocolor = neighbour_color
      pn_tcolor = color
      call paint_neighbours(cursor_posx, cursor_posy)
      cursor_posy = cursor_posy - 1
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return
  ' -- bring_down end

  bring_right:
    neighbour_pos = cursor_posy * 8 + cursor_posx + 1
    neighbour_color = current_level_colors(neighbour_pos)
    neighbour_dots = current_level_dots(neighbour_pos)
    var_pos = cursor_posy * 8 + cursor_posx
    dots = current_level_dots(var_pos)
    color = current_level_colors(var_pos)
    if neighbour_color = $0b OR neighbour_color = color then return
    if neighbour_color = $0c then gosub bring_right_onto_grey else gosub bring_right_onto_color
    return

    bring_right_onto_grey:
      call set_under_cursor( $0c, 0)
      for i as BYTE = 1 to distance
        gosub wait_frame
        Spr0_X = Spr0_X + 1
        SPRITE 0 AT Spr0_X, Spr0_Y
      next i
      cursor_posx = cursor_posx + 1
      call set_under_cursor(color, dots - 1)
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return

    bring_right_onto_color:
      call set_under_cursor(color, dots - 1)
      cursor_posx = cursor_posx + 1
      call set_under_cursor(color, neighbour_dots)
      pn_ocolor = neighbour_color
      pn_tcolor = color
      call paint_neighbours(cursor_posx, cursor_posy)
      cursor_posx = cursor_posx - 1
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return
  ' -- bring_right end

  bring_left:
    neighbour_pos = cursor_posy * 8 + cursor_posx - 1
    neighbour_color = current_level_colors(neighbour_pos)
    neighbour_dots = current_level_dots(neighbour_pos)
    var_pos = cursor_posy * 8 + cursor_posx
    dots = current_level_dots(var_pos)
    color = current_level_colors(var_pos)
    if neighbour_color = $0b OR neighbour_color = color then return
    if neighbour_color = $0c then gosub bring_left_onto_grey else gosub bring_left_onto_color
    return

    bring_left_onto_grey:
      call set_under_cursor( $0c, 0)
      for i as BYTE = 1 to distance
        gosub wait_frame
        Spr0_X = Spr0_X - 1
        SPRITE 0 AT Spr0_X, Spr0_Y
      next i
      cursor_posx = cursor_posx - 1
      call set_under_cursor(color, dots - 1)
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return

    bring_left_onto_color:
      call set_under_cursor(color, dots - 1)
      cursor_posx = cursor_posx - 1
      call set_under_cursor(color, neighbour_dots)
      pn_ocolor = neighbour_color
      pn_tcolor = color
      call paint_neighbours(cursor_posx, cursor_posy)
      cursor_posx = cursor_posx + 1
      Spr0_Shape = Spr0_Shape - 1
      SPRITE 0 SHAPE Spr0_Shape
      if dots = 1 then gosub deselect_square
      return
  ' -- bring_left end

  wait_frame:
    do : loop while peek(RASTER_LINE) 'exiting on line 0
    return
end sub

' -----------------------------------
' - draw game logo
' -----------------------------------

sub drawlogo() STATIC
  Dim charpos as WORD : charpos = 1041
  Dim colorpos as WORD : colorpos = 55313
  
  Dim i as BYTE : i = 0
  for row as BYTE = 0 to 5
    for col as BYTE = 0 to 5
      poke charpos, logo(i)
      poke colorpos, logo_colors(i)
      i = i + 1
      charpos = charpos + 1
      colorpos  = colorpos + 1
    next col
    charpos = charpos + 34
    colorpos = colorpos + 34
  next row

  textat 16, 7, "puralax!", 7 'yellow
end sub

' -----------------------------------
' - intro screen
' -----------------------------------

sub intro() STATIC
  Dim password1$ as STRING * 4 'original XCB2 code -> dim pass1buf![5] : password1$ = @pass1buf!
  Dim password2$ as STRING * 4 'original XCB2 code -> dim pass2buf![5] : password2$ = @pass2buf!
  poke @password2$, 4 'strings are not initialized...
  Dim all_passes_ptr as WORD : all_passes_ptr = @loc_levelpass

  call cls()
  call drawlogo()

  Dim found as BYTE
  Dim k as BYTE

  textat 6,  10, "c64 port written in xc=basic"
  textat 12, 12, "by  csaba fekete"
  textat 10, 16, "f1 - start game", 13 'light green
  textat 10, 18, "f3 - enter level pass", 13 'light green
  textat 1,  24, "music: 'another time' by roman majewski"

  current_level_no = 0

  Dim var_key as BYTE
  found = 0
  do
    get var_key
    if var_key = 133 then exit sub
    if var_key = 134 then gosub enter_code
    if found = 1 then exit sub
  loop

  enter_code:
    locate 10, 20
    print "{YELLOW}pass:         "
    locate 16, 20
    input password1$ ; 'original XCB2 code -> input password1$, 4, "abcdefghijklmnopqrstuvwxyz0123456789"
    
    for k = 0 to 63
      memcpy all_passes_ptr + shl(cword(k), 2), @password2$ + 1, 4 'original XCB2 code -> strncpy password2$, all_passes$ + cast(k! * 4), 4 
      if password1$ = password2$ then found = 1 : exit for 'original XCB2 code -> if strcmp(password1$, password2$) = 0 then found! = 1 : goto exit_check_pass
    next k

    if found then current_level_no = k : return
    locate 16, 20
    print "{LIGHT_RED}no match"
    return
end sub

' -----------------------------------
' - end screen
' -----------------------------------

sub frontend() STATIC
  call cls()
  call drawlogo()
  textat 12, 10, "congratulations!"
  textat 6, 12,  "you have completed all levels"
  textat 4, 14,  "press any key to restart machine"

  poke 198, 0 : wait 198, 1
  sys 64738 FAST
end sub

' -----------------------------------
' - main
' -----------------------------------

start:
  CHARSET 4 'poke VIC_MEMSETUP, %00011000 'screen $0400, chars $2000
  BORDER 11 'gray
  BACKGROUND 11 'gray

  call configure_sprites()
  call start_music()
  call intro()
  
  Dim level_success as BYTE
  game_loop:
    call load_level(current_level_no)
    call draw_level()
    level_success = 0
    call play_level(@level_success)
    SPRITE 0 OFF
    if level_success = 0 then gosub try_again else gosub well_done
    if current_level_no = LEVEL_COUNT then call frontend()
    goto game_loop
  
  try_again:
    textat 15, 24, "try again", 10 'Light Red
    gosub pressfire
    return

  well_done:
    textat 15, 24, "well done", 13 'Light Green
    gosub pressfire  
    current_level_no = current_level_no + 1
    return

  pressfire:
    wait $DC00, 16 : wait $DC00, 16, 16 'wait for fire button to be released first, then for it to be pressed
    return

  end

' -----------------------------------
' - data
' -----------------------------------

loc_logo:
data AS BYTE _
  $4e, $4e, $4e, $4e, $4e, $4e, _
  $4e, $4e, $4e, $4e, $4e, $4e, _
  $4e, $4e, $20, $20, $4e, $4e, _
  $4e, $4e, $20, $20, $4e, $4e, _
  $4e, $4e, $4e, $4e, $4e, $4e, _
  $4e, $4e, $4e, $4e, $4e, $4e

loc_logo_colors:
data AS BYTE _
  $04, $04, $0A, $0A, $07, $07, _
  $04, $04, $0A, $0A, $07, $07, _
  $02, $02, $0E, $0E, $0D, $0D, _
  $02, $02, $0E, $0E, $0D, $0D, _
  $06, $06, $0E, $0E, $0F, $0F, _
  $06, $06, $0E, $0E, $0F, $0F

loc_square_pattern:
data AS BYTE 70, 76, 76, 71, _
             72, 78, 78, 73, _
             72, 78, 78, 73, _
             74, 77, 77, 75

loc_square_pattern_sm:
data AS BYTE 70, 76, 71, _
             72, 78, 73, _
             74, 77, 75

loc_square_pos:
data AS WORD _
  1070, 1074, 1078, 1082, 1086, 1090, 1094,   0, _
  1230, 1234, 1238, 1242, 1246, 1250, 1254,   0, _
  1390, 1394, 1398, 1402, 1406, 1410, 1414,   0, _
  1550, 1554, 1558, 1562, 1566, 1570, 1574,   0, _
  1710, 1714, 1718, 1722, 1726, 1730, 1734,   0

loc_square_pos_sm:
data AS WORD _
  1032, 1035, 1038, 1041, 1044, 1047, 1050, 1053, _
  1152, 1155, 1158, 1161, 1164, 1167, 1170, 1173, _
  1272, 1275, 1278, 1281, 1284, 1287, 1290, 1293, _
  1392, 1395, 1398, 1401, 1404, 1407, 1410, 1413
data AS WORD _
  1512, 1515, 1518, 1521, 1524, 1527, 1530, 1533, _
  1632, 1635, 1638, 1641, 1644, 1647, 1650, 1653, _
  1752, 1755, 1758, 1761, 1764, 1767, 1770, 1773, _
  1872, 1875, 1878, 1881, 1884, 1887, 1890, 1893

' --
' -- Level passwords
' -- 4 chars * 25 levels = 100 bytes
' --

loc_levelpass:
data AS BYTE _
  $37, $38, $4b, $4a, $32, $42, $32, $30, $37, $55, $36, $37, $33, $43, $37, $38, _
  $42, $38, $4c, $50, $39, $57, $53, $47, $42, $34, $56, $39, $35, $31, $33, $43, _
  $31, $39, $31, $53, $44, $31, $33, $37, $51, $36, $36, $32, $36, $52, $39, $58
data AS BYTE _
  $39, $33, $44, $57, $38, $32, $57, $39, $35, $47, $4d, $31, $4e, $47, $55, $4f, _
  $4d, $32, $42, $58, $4b, $39, $34, $31, $47, $44, $53, $4c, $42, $31, $45, $4f, _
  $33, $35, $34, $31, $4e, $33, $4f, $39, $33, $4e, $4a, $32, $38, $48, $31, $39, _
  $55, $35, $48, $35

' --
' -- Level settings
' -- High nibble: 0 - 7x5 level, 1 - 4x4 level, 2 - 8x8 level
' -- Low nibble : target color
' --

loc_levelsettings:
data AS BYTE _
  $0a, $0a, $07, $0a, $0d, $07, $0a, $1d, _
  $14, $1e, $1d, $07, $0d, $04, $24, $1e, _
  $0e, $0d, $0e, $04, $1d, $17, $24, $0e, _
  $0a

' --
' -- Level data (squares)
' -- High nibble: square dots count
' -- Low nibble : square color
' --

loc_leveldata:
data as BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $0c, $0b, $0b, $0b, _
    $0b, $0b, $0c, $1a, $0d, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $0c, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b

data AS BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $0c, $0b, $0b, $0b, _
    $0b, $0b, $2a, $0c, $0d, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $0c, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data as BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $04, $0b, $0b, $0b, _
    $0b, $0b, $27, $0c, $04, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $04, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $0c, $0b, $0b, $0b, _
    $0b, $0b, $3a, $0c, $07, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0d, $0c, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $07, $07, $0b, $0b, $0b, _
    $0b, $0b, $3d, $0c, $04, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $04, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $0c, $0b, $0b, $0b, _
    $0b, $0b, $1a, $0c, $17, $0b, $0b, $0b, _
    $0b, $0b, $0c, $1d, $0c, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0d, $1d, $0b, $0b, $0b, _
    $0b, $0b, $2a, $0c, $07, $0b, $0b, $0b, _
    $0b, $0b, $0c, $0c, $07, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $04, $04, $0d, $1d, $0b, $0b, $0b, $0b, _
    $1a, $0c, $0c, $0a, $0b, $0b, $0b, $0b, _
    $0a, $0c, $0c, $1a, $0b, $0b, $0b, $0b, _
    $17, $07, $1e, $0e, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $04, $14, $0d, $1d, $0b, $0b, $0b, $0b, _
    $0a, $0c, $0c, $0a, $0b, $0b, $0b, $0b, _
    $0a, $0c, $0c, $2a, $0b, $0b, $0b, $0b, _
    $17, $17, $0e, $0c, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0a, $0a, $0d, $0d, $0b, $0b, $0b, $0b, _
    $0a, $0e, $1e, $0d, $0b, $0b, $0b, $0b, _
    $0c, $07, $07, $0c, $0b, $0b, $0b, $0b, _
    $0c, $37, $37, $0c, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0e, $07, $0c, $07, $0b, $0b, $0b, $0b, _
    $0a, $07, $2d, $07, $0b, $0b, $0b, $0b, _
    $0a, $0c, $2d, $0c, $0b, $0b, $0b, $0b, _
    $1e, $0c, $0c, $0c, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0d, $2d, $0c, $04, $04, $0b, $0b, _
    $0b, $0d, $0c, $0c, $0c, $24, $0b, $0b, _
    $0b, $0c, $0c, $27, $0c, $0c, $0b, $0b, _
    $0b, $2a, $0c, $0c, $0c, $0e, $0b, $0b, _
    $0b, $0a, $0a, $0c, $2e, $0e, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $04, $17, $0c, $17, $04, $0b, $0b, _
    $0b, $17, $0c, $1a, $0c, $17, $0b, $0b, _
    $0b, $0c, $1a, $3d, $1a, $0c, $0b, $0b, _
    $0b, $17, $0c, $1a, $0c, $17, $0b, $0b, _
    $0b, $04, $17, $0c, $17, $04, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0a, $1d, $0c, $1d, $0a, $0b, $0b, _
    $0b, $1d, $0c, $17, $0c, $1d, $0b, $0b, _
    $0b, $0c, $17, $14, $17, $0c, $0b, $0b, _
    $0b, $1d, $0c, $04, $0c, $1d, $0b, $0b, _
    $0b, $0a, $1d, $0c, $2d, $0a, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data as BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $14, $07, $07, $07, $07, $0c, $0c, $07, _
    $0c, $07, $0c, $0c, $07, $07, $0c, $07, _
    $0c, $0d, $0c, $0c, $0c, $07, $07, $07, _
    $3a, $0c, $0c, $0c, $0c, $0c, $0c, $07, _
    $3a, $0c, $0c, $0c, $0c, $0c, $0c, $0c, _
    $0c, $0c, $3d, $0c, $3e, $0c, $3d, $0c, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0a, $1a, $0c, $0a, $0b, $0b, $0b, $0b, _
    $0c, $1d, $0c, $0d, $0b, $0b, $0b, $0b, _
    $0c, $0d, $0c, $0d, $0b, $0b, $0b, $0b, _
    $1e, $0d, $3e, $0d, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0a, $2a, $0c, $0d, $0d, $0b, $0b, _
    $0b, $0a, $0c, $0c, $0c, $2d, $0b, $0b, _
    $0b, $0c, $0c, $14, $0c, $0c, $0b, $0b, _
    $0b, $27, $0c, $0c, $0c, $0e, $0b, $0b, _
    $0b, $07, $07, $0c, $2e, $0e, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $27, $17, $17, $17, $17, $0b, $0b, _
    $0b, $0c, $0c, $0c, $0c, $0c, $0b, $0b, _
    $0b, $0d, $0d, $0d, $0d, $2d, $0b, $0b, _
    $0b, $0c, $0c, $0c, $0c, $0c, $0b, $0b, _
    $0b, $2a, $1a, $1a, $1a, $1a, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0d, $17, $27, $0c, $0d, $0b, $0b, _
    $0b, $0c, $0c, $0c, $0c, $0d, $0b, $0b, _
    $0b, $3a, $24, $0d, $07, $1d, $0b, $0b, _
    $0b, $0c, $0c, $0c, $0c, $0d, $0b, $0b, _
    $0b, $0e, $0e, $2e, $0c, $0d, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0e, $0c, $07, $07, $07, $0c, $0e, $0b, _
    $0a, $3d, $0d, $04, $0d, $3d, $0a, $0b, _
    $1a, $0a, $04, $14, $04, $3a, $1a, $0b, _
    $0c, $17, $0c, $1e, $0c, $17, $0c, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $04, $14, $0e, $0d, $0b, $0b, $0b, $0b, _
    $07, $07, $0e, $0d, $0b, $0b, $0b, $0b, _
    $0a, $0a, $17, $17, $0b, $0b, $0b, $0b, _
    $1d, $0a, $14, $04, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $07, $04, $04, $1e, $0b, $0b, $0b, $0b, _
    $04, $04, $1d, $0d, $0b, $0b, $0b, $0b, _
    $0a, $1a, $17, $07, $0b, $0b, $0b, $0b, _
    $0d, $0a, $0a, $0e, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0d, $0d, $0a, $0a, $0d, $0d, $0b, _
    $0b, $1a, $0d, $17, $07, $0d, $1a, $0b, _
    $0b, $14, $0e, $0d, $0d, $2e, $04, $0b, _
    $0b, $0a, $0d, $07, $07, $0d, $0a, $0b, _
    $0b, $1d, $0d, $0a, $0a, $0d, $1d, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $0d, $0d, $0d, $0d, $17, $07, $07, $0b, _
    $07, $0a, $0a, $1e, $0a, $0a, $0d, $0b, _
    $07, $04, $14, $0e, $04, $04, $0d, $0b, _
    $07, $0a, $0a, $0e, $1a, $0a, $1d, $0b, _
    $1d, $0d, $0d, $07, $07, $07, $07, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
data AS BYTE _
    $07, $17, $0a, $0d, $0d, $0e, $04, $0b, _
    $04, $0e, $07, $1d, $0e, $1a, $0a, $0b, _
    $14, $0e, $14, $17, $07, $14, $04, $0b, _
    $1a, $0d, $0d, $1e, $0a, $07, $07, $0b, _
    $0a, $0d, $17, $0e, $0a, $04, $17, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b, _
    $0b, $0b, $0b, $0b, $0b, $0b, $0b, $0b
