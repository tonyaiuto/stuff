#!/usr/bin/env python3

import io
import sys

from PIL import Image
from PIL import ImageDraw


class Tile(object):

  def __init__(self, r, shelf):
    self.r = r
    self.shelf = shelf
    im = Image.new('L', (self.width*scale, image_height), 255)
    self.draw = ImageDraw.Draw(im)

 
  def draw_tile(self, x, y):
    orig_x = x
    orig_y = y
    s2 = self.shelf / 2
    move to x, y

    draw to x, y-s2
    draw arc center=(x, y-s2-r), 270 to 360
    assert x == orig_x + r
    assert y == orig_y - s2 - r
    move x+s, orig_y - s2 - r
    draw arc center=(orig_x + 2 * r + s, orig_y - s2 - r, 180 to 0
    
