#!/usr/bin/env python3

"""Encode text in punch card form.

Usage:
  punch.py '0123456789 abcdefghijklmnopqrstuvwxyz +- / .,'
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

