"""Unmask the puzzle cards.

xkck whatif prank.
"""

import sys

punched2char =  {0: ' ', 2048: '&', 1024: '-', 512: '0', 256: '1', 128: '2', 64: '3', 32: '4', 16: '5', 8: '6', 4: '7', 2: '8', 1: '9', 2304: 'A', 2176: 'B', 2112: 'C', 2080: 'D', 2064: 'E', 2056: 'F', 2052: 'G', 2050: 'H', 2049: 'I', 1280: 'J', 1152: 'K', 1088: 'L', 1056: 'M', 1040: 'N', 1032: 'O', 1028: 'P', 1026: 'Q', 1025: 'R', 768: '/', 640: 'S', 576: 'T', 544: 'U', 528: 'V', 520: 'W', 516: 'X', 514: 'Y', 513: 'Z', 2178: '¢', 2114: '.', 2082: '<', 2066: '(', 2058: '+', 2054: '|', 1154: '!', 1090: '$', 1058: '*', 1042: ')', 1034: ';', 1030: '¬', 578: ',', 546: '%', 530: '_', 522: '>', 518: '?', 130: ':', 66: '#', 34: '@', 18: "'", 10: '=', 6: '"'}


def read_card(file):
    with open(file, 'r', encoding='utf-8') as f:
        card = [f.readline() for i in range(12)]
    return card  

def apply_mask(mask, card):
    ret = []
    for row in range(12):
        mask_row = mask[row]
        card_row = card[row]
        #print(mask_row)
        #print(card_row)
        #if row == 11:
        #  for col in range(70):
        #     print("%2d" % col,  mask_row[col], card_row[col])
        new_row = [
            mask_row[col] == '#' and card_row[col] == '#'
            for col in range(80)
        ]
        ret.append(new_row)
    return ret

def punch2text(card):
    """Convert card image to text."""
    ret = []
    for col in range(80):
        punched = 0
        for row in range(12):
            punched = punched << 1 | (1 if card[row][col] else 0)
        
        if punched in punched2char:
           ret.append(punched2char[punched])
        else:
           ret.append('<%d>' % punched)
    return ''.join(ret)

def unmask(mask_file, puzzle_file):
    mask = read_card(mask_file)
    puzzle =read_card(puzzle_file)
    unmasked = apply_mask(mask, puzzle)
    text = punch2text(unmasked)
    print(text)


if __name__ == '__main__':
  unmask(sys.argv[1], sys.argv[2])
"""

import sys

PUNCH = '#'
FILL = '.'


def punches(s):
  rows = []
  for row in range(12):
    rows.append([FILL for x in range(80)])
  col = 0
  for c in s:
    c = c.upper()
    i = ord(c)

    if c == ' ':
      pass
    elif c == '&' or c == '+':
      rows[0][col] = PUNCH
    elif c == '-':
      rows[1][col] = PUNCH
    elif '0' <= c and c <= '9':
      rows[2 + i - ord('0')][col] = PUNCH
    elif 'A' <= c and c <= 'I':
      rows[0][col] = PUNCH
      rows[3 + (i - ord('A'))][col] = PUNCH
    elif 'J' <= c and c <= 'R':
      rows[1][col] = PUNCH
      rows[3 + (i - ord('J'))][col] = PUNCH
    elif c == '/':
      rows[2][col] = PUNCH
      rows[3][col] = PUNCH
    elif 'S' <= c and c <= 'Z':
      rows[2][col] = PUNCH
      rows[4 + (i - ord('S'))][col] = PUNCH
    elif c == '.':
      rows[0][col] = PUNCH
      rows[5][col] = PUNCH
      rows[10][col] = PUNCH
    elif c == ',':
      rows[2][col] = PUNCH
      rows[5][col] = PUNCH
      rows[10][col] = PUNCH
    else:
      raise ValueError('can not punch (%c)' % c)

    col = col + 1

  for row in range(12):
    rows[row] = ''.join(rows[row])
  return rows

text = ' '.join(sys.argv[1:])
x = punches(text)
i = 0
for row in x:
  print(row)
  # print('%2d %s' % (i-2, row))
  i = i + 1

"""
