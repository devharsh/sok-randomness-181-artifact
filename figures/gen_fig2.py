#!/usr/bin/env python3
"""Write figures/coldcard_faultpath.drawio (Figure 2): intended and actual ColdCard seed paths.
Facts follow the Coinkite backgrounder and advisory and the Block engineering analysis."""
import sys
from xml.sax.saxutils import escape

cells = []
nid = [2]


def add(value, x, y, w, h, style):
    i = "c%d" % nid[0]
    nid[0] += 1
    cells.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
                 '<mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry"/></mxCell>'
                 % (i, escape(value, {'"': "&quot;"}), style, x, y, w, h))
    return i


def edge(src, dst, style):
    i = "c%d" % nid[0]
    nid[0] += 1
    cells.append('<mxCell id="%s" style="%s" edge="1" parent="1" source="%s" target="%s">'
                 '<mxGeometry relative="1" as="geometry"/></mxCell>' % (i, style, src, dst))


F = "fontFamily=Helvetica;fontColor=#000000;html=1;whiteSpace=wrap;fontSize=11;"
box = F + "rounded=1;arcSize=8;strokeWidth=1.3;"
GREEN = box + "fillColor=#d5e8d4;strokeColor=#3a7d34;"
RED = box + "fillColor=#f8cecc;strokeColor=#b85450;"
GREY = box + "fillColor=#f5f5f5;strokeColor=#666666;"
STAR = box + "fillColor=#ffffff;strokeColor=#b85450;dashed=1;"
ATT = box + "fillColor=#ffe6cc;strokeColor=#d79b00;"
A = "endArrow=block;endFill=1;endSize=5;strokeWidth=1.3;html=1;"

W, G = 101, 8
x = [k * (W + G) for k in range(5)]
R = x[4] + W

req = add("Seed request<br><font face='Courier New' style='font-size:10px'>ngu.random<br>.bytes()</font>", x[0], 30, W, 92, GREY)
add("<i>Intended</i>", x[1], 0, 2 * W + G, 14, F + "text;strokeColor=none;fillColor=none;align=left;fontSize=10;")
i1 = add("<font face='Courier New' style='font-size:10px'>rng_get()</font> calls the hardware TRNG wrapper",
         x[1], 16, 2 * W + G, 36, GREEN)
i2 = add("Seed with the intended 128 bits of entropy", x[3], 16, 2 * W + G, 36, GREEN)
add("<i>Shipped, March 2021 to 2026</i>", x[1], 58, 3 * W, 14,
    F + "text;strokeColor=none;fillColor=none;align=left;fontSize=10;")
a1 = add("<font face='Courier New' style='font-size:10px'>rng_get()</font> resolves to the Yasmarang PRNG <b>(S3)</b>",
         x[1], 74, W, 70, RED)
a2 = add("Seeded once from low 32 bits of UID, SysTick, RTC <b>(S4)</b>", x[2], 74, W, 70, RED)
a3 = add("Mk4, Q, Mk5: secure-element bits cut to 32, reseed one state word <b>(S5)</b>",
         x[3], 74, W, 70, RED)
a4 = add("BIP-39 phrase, BIP-32 keys, addresses on the public chain", x[4], 74, W, 70, RED)
edge(req, i1, A + "strokeColor=#3a7d34;exitX=1;exitY=0.2;entryX=0;entryY=0.5;")
edge(i1, i2, A + "strokeColor=#3a7d34;")
edge(req, a1, A + "strokeColor=#b85450;exitX=1;exitY=0.75;entryX=0;entryY=0.5;")
edge(a1, a2, A + "strokeColor=#b85450;")
edge(a2, a3, A + "strokeColor=#b85450;")
edge(a3, a4, A + "strokeColor=#b85450;")

st = add("Build guard tests <font face='Courier New' style='font-size:10px'>#ifndef</font> on a macro defined as 0, so its "
         "<font face='Courier New' style='font-size:10px'>#error</font> never fires and the fallback is linked <b>(S*)</b>",
         x[0], 166, 2 * W + G, 58, STAR)
edge(st, a1, A + "strokeColor=#b85450;dashed=1;exitX=0.75;exitY=0;entryX=0.5;entryY=1;")
att = add("Attacker enumerates candidate seeds offline and matches derived addresses against "
          "funded ones, without access to any device <b>(A1)</b>", x[2] + 10, 166, R - x[2] - 10, 58, ATT)
edge(a4, att, A + "strokeColor=#d79b00;startArrow=block;startFill=1;exitX=0.5;exitY=1;entryX=0.85;entryY=0;")

add("Search space, disputed. Vendor: about 2<sup>40</sup> (Mk2, Mk3) and 2<sup>72</sup> "
    "(Mk4, Mk5, Q). Block: at most 2<sup>32</sup> output streams once the fallback state and "
    "call history are known, raw ceiling about 2<sup>73</sup>.",
    x[0], 238, R, 40, F + "rounded=0;fillColor=#ffffff;strokeColor=#666666;align=left;spacingLeft=6;spacingRight=6;fontSize=10.5;")

xml = ('<mxfile host="drawio"><diagram id="fig2" name="coldcard_faultpath">'
       '<mxGraphModel dx="800" dy="400" grid="0" gridSize="10" guides="1" tooltips="1" '
       'connect="1" arrows="1" fold="1" page="0" pageScale="1" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) +
       '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w").write(xml)
print("wrote", sys.argv[1], "width", R)
