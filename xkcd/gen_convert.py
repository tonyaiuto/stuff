# Generate char to row punches map.

key = """
    __________________________________________________________________
    | &-0123456789 ABCDEFGHIJKLMNOPQR/STUVWXYZ ¢.<(+|!$*);¬,%_>?:#@'="
12 Y| x            xxxxxxxxx                   xxxxxx                 
11 X|  x                    xxxxxxxxx                xxxxxx           
   0|   x                            xxxxxxxxx             xxxxx       
   1|    x         x        x        x                                  
   2|     x         x        x        x        x     x          x     
   3|      x         x        x        x        x     x    x     x    
   4|       x         x        x        x        x     x    x     x    
   5|        x         x        x        x        x     x    x     x    
   6|         x         x        x        x        x     x    x     x    
   7|          x         x        x        x        x     x    x     x
   8|           x         x        x        x  xxxxxxxxxxxxxxxxxxxxxxx
   9|            x         x        x        x                        
"""

punched2char = {}
rows = key.split('\n')[2:]
# print(rows)
for col in range(5, len(rows[0])):
   punchval = 0
   for row in range(1, 13):
       punchval = punchval << 1 | (1 if rows[row][col] != ' ' else 0)
   # print(rows[0][col], punchval) 
   punched2char[punchval] = rows[0][col]

# print('punched2char = ', punched2char)
