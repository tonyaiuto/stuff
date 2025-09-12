#!/usr/bin/python

"""Convert a keypunch card image into SVG.

This produces crappy, but servicable SVG which you can use on your local
laser cutter.
"""

from string import Template
import sys

FILLERS = ' -.'

DPI=90

CARD_WIDTH_IN = 7.375
CARD_HEIGHT_IN = 3.25

CARD_WIDTH_PX = DPI * CARD_WIDTH_IN
CARD_HEIGHT_PX = DPI * CARD_HEIGHT_IN

CELL_WIDTH = CARD_WIDTH_PX / 84
CELL_HEIGHT = CARD_HEIGHT_PX / 13

PUNCH_WIDTH=CELL_WIDTH * 12 / 16
PUNCH_HEIGHT=CELL_HEIGHT * 7 / 16

LEFT_MARGIN_PX = CELL_WIDTH * 2
TOP_MARGIN_PX = CELL_HEIGHT / 2


SVG_PREAMBLE="""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   width="${width_px}"
   height="${height_px}"
   id="svg2"
   version="1.1"
   inkscape:version="0.48.3.1 r9886"
   sodipodi:docname="card_x.svg">
  <defs
     id="defs4" />
  <sodipodi:namedview
     id="base"
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1.0"
     inkscape:pageopacity="0.0"
     inkscape:pageshadow="2"
     inkscape:zoom="1"
     inkscape:cx="318.21509"
     inkscape:cy="146.25"
     inkscape:document-units="px"
     inkscape:current-layer="layer1"
     showgrid="true"
     width="1052.36px"
     units="in"
     showguides="false"
     inkscape:window-width="1217"
     inkscape:window-height="752"
     inkscape:window-x="1151"
     inkscape:window-y="26"
     inkscape:window-maximized="0"
     inkscape:snap-bbox="true"
     inkscape:snap-page="true" />
  <metadata
     id="metadata7">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title />
      </cc:Work>
    </rdf:RDF>
  </metadata>
"""


PUNCH_RECT = """<rect
  style="fill:#222222;fill-rule:evenodd;stroke:#000000;stroke-width:.5px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
  id="${id}" x="${x}" y="${y}" width="${width}" height="${height}" />
"""



def DoCard(f):
  preamble = Template(SVG_PREAMBLE)
  punch = Template(PUNCH_RECT)
  print preamble.substitute(width_px=CARD_WIDTH_PX, height_px=CARD_HEIGHT_PX)
  print """<g inkscape:label="layer1" inkscape:groupmode="layer"
              id="layer1">"""

  row = 0
  for line in f:
    for col in range(80):
      if line[col] not in FILLERS:
        id = 'rect%02d%02d' % (row, col)
        x = col * CELL_WIDTH + LEFT_MARGIN_PX
        y = row * CELL_HEIGHT + TOP_MARGIN_PX
        print punch.substitute(id=id, x=x, y=y,
                               width=PUNCH_WIDTH, height=PUNCH_HEIGHT)
    row += 1
  print '</g>'
  print '</svg>'


DoCard(sys.stdin)
sys.exit(0)

"""
  <g
     inkscape:label="Layer 1"
     inkscape:groupmode="layer"
     id="layer1"
     transform="translate(0,-759.8622)">
    <rect
       style="fill:#0000ff;fill-rule:evenodd;stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       id="rect2989"
       width="5.3739581"
       height="18.424999"
       x="637.19788"
       y="267.93332"
       transform="translate(0,759.8622)" />
    <rect
       style="fill:#0000ff;fill-rule:evenodd;stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
       id="rect2993"
       width="6.1416664"
       height="18.424999"
       x="620.30835"
       y="18.428129"
       transform="translate(0,759.8622)" />
"""
