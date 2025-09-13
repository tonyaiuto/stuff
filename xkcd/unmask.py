"""Unmask the puzzle cards.

xkck whatif prank.
"""

import sys
import argparse
from gen_convert import punched2char


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
            '#' if mask_row[col] == '#' and card_row[col] == '#' else '-'
            for col in range(80)
        ]
        # print(''.join(new_row))
        ret.append(new_row)
    return ret

def punch2text(card):
    """Convert card image to text."""
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


def invert_card(card):
    return [card[row] for row in range(11,-1,-1)]


def unmask(mask_file, puzzle_file):
    mask = read_card(mask_file)
    puzzle =read_card(puzzle_file)

    unmasked = apply_mask(mask, puzzle)
    text = punch2text(unmasked)
    print(text)

    mask_inv = invert_card(mask)
    unmasked = apply_mask(mask_inv, puzzle)
    text = punch2text(unmasked)
    print(text)


if __name__ == '__main__':
  unmask(sys.argv[1], sys.argv[2])
