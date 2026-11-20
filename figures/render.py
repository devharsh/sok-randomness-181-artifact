#!/usr/bin/env python3
"""Render an uncompressed .drawio (mxGraphModel) file to PDF and PNG with mxGraph in headless Chrome.

Usage: python3 render.py in.drawio out.pdf
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "node_modules/mxgraph/javascript/src")
LIB = os.path.join(HERE, "node_modules/mxgraph/javascript/mxClient.js")


def main(inp, out):
    xml = open(inp).read()
    page = os.path.join(HERE, "page.html")
    open(page, "w").write(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:#fff;font-family:Helvetica,Arial,sans-serif}"
        "#g{position:relative;overflow:visible}</style>"
        f"<script>var mxBasePath='file://{SRC}';var mxLoadResources=false;var mxLoadStylesheets=false;</script>"
        f"<script src='file://{LIB}'></script></head><body><div id='g'></div></body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page(device_scale_factor=3)
        pg.goto("file://" + page)
        dims = pg.evaluate("""(xml) => {
            const doc = mxUtils.parseXml(xml);
            const model = doc.getElementsByTagName('mxGraphModel')[0];
            const c = document.getElementById('g');
            const graph = new mxGraph(c);
            graph.setHtmlLabels(true); graph.setEnabled(false);
            new mxCodec(model.ownerDocument).decode(model, graph.getModel());
            const bb = graph.getGraphBounds();
            graph.view.setTranslate(-bb.x + 2, -bb.y + 2);
            const w = Math.ceil(bb.width + 4), h = Math.ceil(bb.height + 4);
            c.style.width = w + 'px'; c.style.height = h + 'px';
            return {w, h};
        }""", xml)
        pg.pdf(path=out, width=f"{dims['w']}px", height=f"{dims['h']}px",
               print_background=True, page_ranges="1")
        pg.screenshot(path=out[:-4] + ".png", clip={"x": 0, "y": 0, "width": dims["w"], "height": dims["h"]})
        b.close()
    print(json.dumps(dims))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
