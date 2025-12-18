1 rem maze generator by wizofwor
2 rem inspired by the book 10 print

10 print "{clr}{home}             maze generator "
20 print "  push f1 or f3 to change the pattern"
30 gosub 200 
40 p = 5 : q = 205.5

60 rem random maze generator
70 for i=1104 to 1635 : poke i,q+rnd(1)
80 get k$ : if k$<>"" then gosub 310
90 next
100 for i=1651 to 2024 : poke i,q+rnd(1)
110 get k$ : if k$<>"" then gosub 310
120 next
130 goto 60
190 end

200 rem indicator bar
210 for i=0 to 14 : read a : poke 1636+i,a : next
250 for i=0 to 14 : read a : poke 55908+i,a : next
290 return

300 rem key control 
310 if k$=chr$(133) then p=p-1
320 if k$=chr$(134) then p=p+1
330 if p<0 then p=0
340 if p>10 then p=10
350 q = 205 + p/10
360 rem update indicator bar
370 for j = p+1 to 11 : poke 1637+j,100 : next
380 for j = 1 to p+1 : poke 1637+j,224 : next
390 return

490 rem char and color data for indicator bar
500 data 134,177,224,224,224,224,224,224
510 data 100,100,100,100,100,134,179
520 data 10,10,1,1,1,1,1,1
530 data 1,1,1,1,1,7,7
