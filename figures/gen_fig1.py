#!/usr/bin/env python3
"""Write figures/taxonomy_pipeline.drawio (Figure 1): pipeline stages, SP 800-90 coverage,
corpus examples per stage, and the cross-cutting build and integration surface."""
import sys
from xml.sax.saxutils import escape

cells = []
nid = [2]


def add(value, x, y, w, h, style, vertex=True):
    i = "c%d" % nid[0]
    nid[0] += 1
    cells.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
                 '<mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry"/></mxCell>'
                 % (i, escape(value, {'"': "&quot;"}), style, x, y, w, h))
    return i


def edge(src, dst, style, pts=None):
    i = "c%d" % nid[0]
    nid[0] += 1
    cells.append('<mxCell id="%s" style="%s" edge="1" parent="1" source="%s" target="%s">'
                 '<mxGeometry relative="1" as="geometry"/></mxCell>' % (i, style, src, dst))
    return i


FONT = "fontFamily=Helvetica;fontColor=#000000;"
W, G, X0 = 80, 10, 0
xs = [X0 + k * (W + G) for k in range(6)]
right = xs[5] + W

band = FONT + "rounded=0;whiteSpace=wrap;html=1;fontSize=11.5;strokeColor=#4d4d4d;"
# Standards coverage bands
add("NIST SP 800-90C: assembly of a complete generator", xs[0], 0, xs[4] + W - xs[0], 19,
    band + "fillColor=#eeeeee;")
add("SP 800-90B: entropy source", xs[0], 22, xs[1] + W - xs[0], 18, band + "fillColor=#eeeeee;")
add("SP 800-90A: deterministic generator (DRBG)", xs[2], 22, xs[4] + W - xs[2], 18,
    band + "fillColor=#eeeeee;")
add("Outside<br>SP 800-90", xs[5], 0, W, 40,
    band + "fillColor=#ffffff;dashed=1;fontStyle=2;")

stage = FONT + "rounded=1;arcSize=8;whiteSpace=wrap;html=1;fontSize=12;strokeWidth=1.3;"
names = ["<b>S1</b><br>Entropy<br>source", "<b>S2</b><br>Accumulate,<br>condition",
         "<b>S3</b><br>Generation<br>algorithm", "<b>S4</b><br>Seeding,<br>instantiation",
         "<b>S5</b><br>State<br>lifecycle", "<b>S6</b><br>Consumption<br>by protocols"]
ids = []
for k, n in enumerate(names):
    fill = "#dae8fc;strokeColor=#2b5797" if k < 5 else "#d5e8d4;strokeColor=#3a7d34"
    ids.append(add(n, xs[k], 48, W, 54, stage + "fillColor=" + fill + ";"))
arrow = "endArrow=block;endFill=1;endSize=5;html=1;strokeWidth=1.3;strokeColor=#333333;"
for a, b in zip(ids, ids[1:]):
    edge(a, b, arrow + "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")

ex = "fontFamily=Helvetica;text;html=1;whiteSpace=wrap;align=center;verticalAlign=top;fontSize=10.5;fontStyle=2;fontColor=#333333;strokeColor=none;fillColor=none;"
examples = ["Ps and Qs,<br>AMD RDSEED", "/dev/random<br>robustness",
            "Dual EC,<br>Milk Sad", "Netscape,<br>DUHK", "VM reset,<br>OpenSSL fork",
            "PS3,<br>biased nonces"]
exids = [add(e, xs[k] - 5, 106, W + 10, 34, ex) for k, e in enumerate(examples)]

cross = FONT + ("rounded=1;arcSize=10;whiteSpace=wrap;html=1;fontSize=11.5;dashed=1;"
                "strokeWidth=1.3;strokeColor=#b85450;fillColor=#f8cecc;align=center;")
cx = add("<b>S*</b> Build and integration (cross-cutting): symbol collisions, build flags that "
         "disable a source, patches that remove entropy, substituted constants<br>"
         "<i>Debian OpenSSL (2008), Juniper Dual EC (2016), ColdCard (2026)</i>",
         xs[0], 162, right - xs[0], 46, cross)
up = ("endArrow=block;endFill=1;endSize=4;html=1;dashed=1;strokeColor=#b85450;"
      "strokeWidth=1;exitY=0;entryY=1;")
for k, e in enumerate(exids):
    fx = (xs[k] + W / 2 - xs[0]) / (right - xs[0])
    edge(cx, e, up + "exitX=%.4f;entryX=0.5;" % fx)

xml = ('<mxfile host="drawio"><diagram id="fig1" name="taxonomy_pipeline">'
       '<mxGraphModel dx="800" dy="400" grid="0" gridSize="10" guides="1" tooltips="1" '
       'connect="1" arrows="1" fold="1" page="0" pageScale="1" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) +
       '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w").write(xml)
print("wrote", sys.argv[1], "width", right)
