#!/usr/bin/python

"""Print a punching guide around punch card bits

Add row and column marks to punch.py output. This makes it eaiser to read when
you are hand punching cards.

Usage:
  punch.py 'Hello world' | guide.py
"""

import sys


MARKERS = '&Y0123456789'

l = ''
for tens in range(1,9):
  l += 9 * ' '
  l += str(tens)
  l += ' '
l += '\n'
for c in range(1,81):
  l += str(c % 10)
  if c % 10 == 0:
    l += ' '
print(l)
print()


row = 0
for line in sys.stdin:
  l = line.strip().replace('-','.').replace('#', MARKERS[row])
  row += 1

  out = ''
  for c in range(8):
    out += l[(c * 10):(c * 10 + 10)]
    out += ' '
  print(out)
