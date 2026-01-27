'-----------------------------------------------------------------------
'
' Ported from XCB 2 to XCB 3.1 by @jjflash@mastodon.social
'
'-----------------------------------------------------------------------

Const TRUE = 255
Const FALSE = 0

Const SPACE = 32
Const ASTERISK = 42
Const SNAKE_CHAR = 209

dim snake_pieces(256) as WORD

declare sub cls() STATIC
declare sub new_food() STATIC
declare sub move_loop() STATIC
declare sub game_over() STATIC
declare sub get_input() STATIC
declare function check_hit as BYTE () STATIC
declare sub check_eat() STATIC

border 5 'green
background 0 'black
poke 646, 5 'foreground, green
call cls()

textat 7, 8, "welcome to xc-basic snake!"
textat 15, 10, "controls:"
poke 1523, 137 'letter "I"
poke 1562, 138 'letter "J"
poke 1564, 140 'letter "K"
poke 1603, 139 'letter "L"
textat 14, 16, "press a key"
poke 198, 0 : wait 198, 1
randomize (ti() )

do 'GAME LOOP
	call cls()
	Dim snake_length as BYTE : snake_length = 4
	Dim head_x as BYTE : head_x = 19
	Dim head_y as BYTE : head_y = 10
	Dim dx as BYTE : dx = 1
	Dim dy as BYTE : dy = 0
	Dim speed as BYTE : speed = 16
	Dim head_offset as WORD

	For I as WORD = 0 To cword(snake_length)
		snake_pieces(I) = 415 + I
		poke 1439 + I, SNAKE_CHAR ' poke 1024 + snake_pieces(I), SNAKE_CHAR
	next I
	
	call new_food()
	call move_loop()
	call game_over()
loop

sub cls() STATIC
	sys $E544 FAST 'kernel clear screen

	textat 0, 0, "length: 4    xc-basic snake    speed: 1"

	For I as WORD = 1024 To 1063
		poke I, peek(I) OR 128 'reverse chars
	next i
end sub

sub new_food() STATIC
	Dim food_loc as INT
	Dim food_loc_offset as WORD
	do
		food_loc = shr(rndi(), 5) ' rnd() / 32

		if food_loc < 0 then food_loc = abs(food_loc)

		if food_loc < 1000 then
			food_loc_offset = 1024 + food_loc
			if peek(food_loc_offset) = SPACE then
				poke food_loc_offset, ASTERISK
				exit sub
			end if
		end if
	loop
end sub

sub move_loop() STATIC
	do
		poke 1024 + snake_pieces(0), SPACE
		call get_input()

		head_x = head_x + dx
		head_y = head_y + dy
		head_offset = cword(head_x) + cword(40) * cword(head_y)

		if check_hit() then exit sub

		for J as BYTE = 0 to snake_length - 1
			snake_pieces(J) = snake_pieces(J + 1)
		next J
		snake_pieces(snake_length) = head_offset

		call check_eat()

		For J as BYTE = 1 to speed + 8 ' + 8 is to compensate for the differences in speed between XCB 2.3 and XCB 3.1
			'wait for frame
			do : loop while cbyte(scan()) < 250
		Next J

		'update screen
		poke 1024 + snake_pieces(snake_length), SNAKE_CHAR

	loop
end sub

sub game_over() STATIC
	textat 16, 10, "game over"
	textat 15, 11, "press a key"
	poke 198, 0 : wait 198, 1
end sub

sub get_input() STATIC
	Const I_KEY = 61186
	Const J_KEY = 61188
	Const K_KEY = 61216
	Const L_KEY = 57092
	
	if key(I_KEY) then
		if dy = 1 then exit sub
		dx = 0
		dy = 255 '-1
		exit sub
	end if
	
	if key(J_KEY) then
		if dx = 1 then exit sub
		dx = 255 '-1
		dy = 0
		exit sub
	end if
	
	if key(K_KEY) then
		if dy = 255 then exit sub 'if dy = -1
		dx = 0
		dy = 1
		exit sub
	end if
	
	if key(L_KEY) then
		if dx = 255 then exit sub 'if dx = -1
		dx = 1
		dy = 0
		exit sub
	end if
end sub

function check_hit as BYTE () STATIC
	select case head_x
		case 255, 40 '-1, 40
			return TRUE
	end select

	select case head_y
		case 0, 25
			return TRUE
	end select

	if peek(1024 + head_offset) = SNAKE_CHAR then return TRUE

	return FALSE
end function

sub check_eat() STATIC
	if peek(1024 + head_offset) = SPACE then exit sub

	if snake_length < 255 then snake_length = snake_length + 1
	snake_pieces(snake_length) = head_offset

	textat 8, 0, "   "
	textat 8, 0, snake_length
	'reverse textat chars
	poke 1032, peek(1032) OR 128
	poke 1033, peek(1033) OR 128
	poke 1034, peek(1034) OR 128
	
	speed = 16 - shr(snake_length, 4) 'snake_length / 16
	
	textat 38,0 , "  "
	textat 38,0 , 17 - speed
	'reverse textat chars
	poke 1062, peek(1062) OR 128
	poke 1063, peek(1063) OR 128
	
	call new_food()
end sub
