"""card to text.

xkcd what-if prank.
"""

import sys
from gen_convert import punched2char

# punched2char =  {0: ' ', 2048: '&', 1024: '-', 512: '0', 256: '1', 128: '2', 64: '3', 32: '4', 16: '5', 8: '6', 4: '7', 2: '8', 1: '9', 2304: 'A', 2176: 'B', 2112: 'C', 2080: 'D', 2064: 'E', 2056: 'F', 2052: 'G', 2050: 'H', 2049: 'I', 1280: 'J', 1152: 'K', 1088: 'L', 1056: 'M', 1040: 'N', 1032: 'O', 1028: 'P', 1026: 'Q', 1025: 'R', 768: '/', 640: 'S', 576: 'T', 544: 'U', 528: 'V', 520: 'W', 516: 'X', 514: 'Y', 513: 'Z', 2178: '¢', 2114: '.', 2082: '<', 2066: '(', 2058: '+', 2054: '|', 1154: '!', 1090: '$', 1058: '*', 1042: ')', 1034: ';', 1030: '¬', 578: ',', 546: '%', 530: '_', 522: '>', 518: '?', 130: ':', 66: '#', 34: '@', 18: "'", 10: '=', 6: '"'}

def pad80(s):
    need = 80 - len(s)
    if need > 0:
       s = s + ' ' * need
    return s

def card2text(file):
    """Convert card image to text."""
    card = [pad80(file.readline()) for i in range(12)]
    ret = []
    for col in range(80):
        punched = 0
        for row in range(12):
            punched = punched << 1 | (1 if card[row][col] == '#' else 0)
        if punched in punched2char:
            ret.append(punched2char[punched])
        else:
            ret.append('<%d>' % punched)
    return ''.join(ret)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='UTF-8') as inp:
            print(card2text(inp))
    else:
        print(card2text(sys.stdin))
