# How This Document Was Built — A Reusable Process for Diagram-Rich Professional DOCX Reports

This is a process guide, not a report about one project. Hand this file to
any other Claude instance (or read it yourself in a future session) and it
should be able to reproduce the same visual style and workflow used to build
`NeelPrajna_Architecture_Diagrams.docx` and the two research volumes before
it — for any subject matter, not just this one.

---

## 1. What this workflow produces

A professional `.docx` with:
- a title page, running header, page-numbered footer, and (optionally) a
  clickable table of contents;
- consistent typography and a small, deliberate color palette used for every
  heading, table, and diagram;
- **diagrams as crisp vector-quality PNGs, hand-built as SVG**, not
  screenshots, not clip art, not an external design tool round-trip;
- one diagram per page, with framing prose before it and a caption after —
  never a bare image with no context.

## 2. Why diagrams are hand-built SVG, not Figma/Canva/Mermaid

This matters enough to state up front, because it is the least obvious
decision in the whole workflow.

Figma's `generate_diagram` tool and Mermaid Chart's `validate_and_render_mermaid_diagram`
render an **interactive widget directly to the user** — they do not return a
file key, node ID, or downloadable asset back to the model in a way that can
be chained into a docx build. They are excellent for live, human-in-the-loop
diagram editing inside a chat, but they are a dead end for an automated
"generate image → embed in Word" pipeline in this environment.

**The fix that works reliably: draw the diagram as SVG directly (full
control over every box, arrow, and label), rasterize it to PNG locally with
`rsvg-convert`, and embed the PNG.** This gives exact control over layout —
critical for "top-to-bottom" architecture diagrams where box order and arrow
direction carry meaning — and has no external dependency or round-trip
latency.

If the person explicitly names Figma or Canva and wants the *editable design
file itself* (not just an image inside a Word doc), that's a legitimate,
different request — hand it to those tools directly. But for "diagrams
inside a professional docx," draw-and-rasterize is the dependable path.

## 3. Environment setup (one-time, per session)

```bash
# SVG → PNG rasterizer (not installed by default)
apt-get install -y librsvg2-bin
which rsvg-convert   # should now resolve

# docx builder (should already be preinstalled per the docx skill — do not
# npm install unless `require('docx')` actually fails)
node -e "require('docx')"
```

Always read `/mnt/skills/public/docx/SKILL.md` before writing any docx code
— it documents the docx-js gotchas (page size, table column widths, list
bullets, etc.) referenced throughout this guide.

## 4. The visual system (reuse these constants every time)

A tiny, fixed palette applied consistently is what makes the output look
designed rather than default. Pick one accent pair per project and never
deviate mid-document:

| Token | Hex | Used for |
|---|---|---|
| `ACCENT` (navy) | `#1F3864` | H1 headings, primary boxes, title text |
| `ACCENT2` (blue) | `#2E74B5` | H2 headings, secondary boxes, arrows |
| `GREY` | `#595959` | Captions, footers, de-emphasized text |
| `LBLUE` / `LBLUE2` | `#DCE6F5` / `#EAF1FB` | Box fills (Core / primary group) |
| `LGREEN` | `#E6F4EA` with stroke `#2E7D32` | Box fills (secondary group, e.g. a plug-in or "acts" role) |
| `GOLD` | `#B8860B` with fill `#FFF3D6` | Highlight / "the one component that matters" |
| `LGREY` | `#F2F2F2` | Neutral/infrastructure boxes |

Typography: `Calibri` body text at 22 half-points (11pt), `Calibri Light`
bold for headings, in navy/blue per the table above. Tables use the accent
color as a solid header-row fill with white text, and alternate light-fill
striping on body rows.

## 5. Step-by-step workflow

### Step 1 — Read source material fully before designing anything
Extract and read every relevant document (specs, existing docs, exports).
Do not start drawing until you can state, in one sentence per diagram, what
it needs to show and in what order top-to-bottom.

### Step 2 — Decide the diagram list first, as prose, before touching code
For each diagram, write one line: what sits at the top, what sits at the
bottom, and why that order is the correct one (upstream→downstream,
authority→action, owner→implementation, etc.). This is the actual design
work; the SVG code is just execution.

### Step 3 — Build (or reuse) the SVG helper library
See §6 below for the full, ready-to-use `diagram_lib.py`. It provides:
`box()` (rounded rectangle + title + optional bullet subtitle lines),
`arrow()` / `elbow_arrow()` (straight or right-angled connectors with
arrowheads), `section_bg()` (a dashed-border grouping region with a label),
`edge_label()` (text badge floating on a connector), and `label()` (free
text). Everything is plain SVG strings — no external graphics library
dependency beyond `rsvg-convert` for rasterizing.

### Step 4 — Write one small Python script per diagram
Do not try to build a generic "auto-layout" system — for a handful of
diagrams, hand-placed coordinates are faster to get right and easier to
debug than a layout engine. Each script:
1. imports the helper library,
2. creates a `Diagram(width, height)` canvas sized generously (extra
   vertical room is cheap; cramped text is not),
3. places boxes top-to-bottom with arrows between them,
4. calls `.save(svg_path)`.

### Step 5 — Rasterize every SVG to PNG at a fixed width
```bash
rsvg-convert -w 1300 diagram.svg -o diagram.png    # 1300–1400px is a good default
```
Higher width = crisper text when Word displays it at a smaller physical
size. Record each PNG's actual pixel dimensions — you'll need them (or a
hardcoded lookup) when placing the image at a controlled physical width in
the docx (see §7, gotcha 2).

### Step 6 — Build the docx with docx-js
One `ImageRun` per diagram, centered, at a fixed physical width (550–570px
maps to roughly 5.7–6in — leaves comfortable margin on a US Letter page).
Follow it immediately with a small italic caption paragraph.

### Step 7 — Force one diagram per page
**Do this even if you think the content will naturally paginate correctly**
— see gotcha 3 in §7. Insert an explicit `PageBreak` before every diagram's
heading.

### Step 8 — Verify by converting to PDF and inspecting
```bash
python /mnt/skills/public/docx/scripts/office/soffice.py --headless --convert-to pdf report.docx
pdfinfo report.pdf | grep Pages          # sanity check: expected page count?
pdfimages -list report.pdf               # one row-pair (image+smask) per page, per diagram
pdftoppm -jpeg -r 70 report.pdf page      # then visually inspect page-NN.jpg with the view tool
```
`pdfimages -list` is the single most useful check: it reports the actual
placed width/height and ppi of every embedded image. If ppi is very low (an
image stretched far beyond its native resolution) or several images share
one page number, something is wrong — fix it before declaring the document
done.

### Step 9 — Copy to the outputs directory and present
```bash
cp report.docx /mnt/user-data/outputs/
```
then call `present_files` with that path. Never skip this step — the person
cannot access a file that only exists in the working directory.

## 6. The reusable diagram helper library (`diagram_lib.py`)

Copy this file verbatim into a new project; it has no project-specific
content.

```python
"""Shared SVG helpers for clean, consistent top-to-bottom architecture diagrams."""
import html

NAVY = "#1F3864"
BLUE = "#2E74B5"
LBLUE = "#DCE6F5"
LBLUE2 = "#EAF1FB"
GREY = "#595959"
LGREY = "#F2F2F2"
GOLD = "#B8860B"
GREEN = "#2E7D32"
LGREEN = "#E6F4EA"
WHITE = "#FFFFFF"
DARK = "#222222"

def esc(t):
    return html.escape(str(t))

class Diagram:
    def __init__(self, width, height, bg="#FFFFFF"):
        self.width = width
        self.height = height
        self.bg = bg
        self.elems = []
        self.defs = []
        self._arrow_marker()

    def _arrow_marker(self):
        self.defs.append('''
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#2E74B5"/>
        </marker>
        <marker id="arrowg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#595959"/>
        </marker>
        ''')

    def box(self, x, y, w, h, title, subtitle_lines=None, fill=LBLUE2, stroke=BLUE,
             title_color=NAVY, text_color=DARK, title_size=15, text_size=11.5,
             rx=10, bold_title=True, align="middle", stroke_width=1.6, dashed=False):
        anchor = {"middle": "middle", "start": "start"}[align]
        tx = x + w/2 if align == "middle" else x + 14
        dash = ' stroke-dasharray="6,4"' if dashed else ''
        self.elems.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
                           f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}/>')
        cy = y + (title_size + 6) if subtitle_lines else y + h/2 + title_size/3
        weight = 'font-weight="700"' if bold_title else ''
        self.elems.append(f'<text x="{tx}" y="{cy}" font-family="Calibri, Arial, sans-serif" '
                           f'font-size="{title_size}" {weight} fill="{title_color}" text-anchor="{anchor}">{esc(title)}</text>')
        if subtitle_lines:
            ly = cy + title_size * 0.9
            for line in subtitle_lines:
                self.elems.append(f'<text x="{tx}" y="{ly}" font-family="Calibri, Arial, sans-serif" '
                                   f'font-size="{text_size}" fill="{text_color}" text-anchor="{anchor}">{esc(line)}</text>')
                ly += text_size + 4
        return (x, y, w, h)

    def label(self, x, y, text, size=12.5, color=GREY, anchor="middle", italic=False, bold=False):
        style = "font-style:italic;" if italic else ""
        w = 'font-weight="700"' if bold else ""
        self.elems.append(f'<text x="{x}" y="{y}" font-family="Calibri, Arial, sans-serif" font-size="{size}" '
                           f'fill="{color}" text-anchor="{anchor}" style="{style}" {w}>{esc(text)}</text>')

    def section_bg(self, x, y, w, h, fill, stroke=None, label_text=None, label_color=GREY):
        s = f' stroke="{stroke}" stroke-width="1.5" stroke-dasharray="4,3"' if stroke else ''
        self.elems.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" ry="14" fill="{fill}"{s}/>')
        if label_text:
            self.elems.append(f'<text x="{x+16}" y="{y+22}" font-family="Calibri, Arial, sans-serif" '
                               f'font-size="12.5" font-weight="700" fill="{label_color}" letter-spacing="0.5">{esc(label_text.upper())}</text>')

    def arrow(self, x1, y1, x2, y2, color=BLUE, width=2, dashed=False, marker="arrow"):
        dash = ' stroke-dasharray="7,5"' if dashed else ''
        self.elems.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
                           f'stroke-width="{width}"{dash} marker-end="url(#{marker})"/>')

    def elbow_arrow(self, x1, y1, x2, y2, color=BLUE, width=2, dashed=False, marker="arrow"):
        midy = (y1 + y2) / 2
        dash = ' stroke-dasharray="7,5"' if dashed else ''
        self.elems.append(f'<path d="M{x1},{y1} L{x1},{midy} L{x2},{midy} L{x2},{y2}" '
                           f'fill="none" stroke="{color}" stroke-width="{width}"{dash} marker-end="url(#{marker})"/>')

    def edge_label(self, x, y, text, size=10.5, color=GREY, bg=True):
        if bg:
            w = len(text) * size * 0.56 + 10
            self.elems.append(f'<rect x="{x-w/2}" y="{y-size-2}" width="{w}" height="{size+6}" fill="white" opacity="0.9"/>')
        self.elems.append(f'<text x="{x}" y="{y}" font-family="Calibri, Arial, sans-serif" font-size="{size}" '
                           f'fill="{color}" text-anchor="middle">{esc(text)}</text>')

    def render(self):
        body = "\n".join(self.elems)
        defs = "\n".join(self.defs)
        return f'''<svg viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" font-family="Calibri, Arial, sans-serif">
<defs>{defs}</defs>
<rect x="0" y="0" width="{self.width}" height="{self.height}" fill="{self.bg}"/>
{body}
</svg>'''

    def save(self, path):
        with open(path, "w") as f:
            f.write(self.render())
```

### Example: one diagram script using the library

```python
import sys
sys.path.insert(0, "/home/claude")
from diagram_lib import Diagram, NAVY, BLUE, LBLUE, LBLUE2, GREY, LGREY, GOLD, GREEN, LGREEN, DARK

d = Diagram(880, 500)                      # generous canvas, trim later via viewBox if needed
d.box(240, 20, 400, 65, "TOP LAYER", ["What sits at the top and why"], fill=LBLUE, stroke=NAVY)
d.arrow(440, 85, 440, 130)                 # straight vertical connector
d.box(240, 130, 400, 65, "NEXT LAYER", ["What it receives from above"], fill=LGREEN, stroke=GREEN)
d.save("/home/claude/diagrams/example.svg")
```

```bash
rsvg-convert -w 1300 /home/claude/diagrams/example.svg -o /home/claude/diagrams/example.png
```

## 7. The docx build script template

```javascript
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ImageRun, BorderStyle, PageBreak, PageNumber, Footer, Header,
} = require('docx');
const fs = require('fs');

const ACCENT = "1F3864";
const ACCENT2 = "2E74B5";
const GREY = "595959";

function h1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 140 }, children: [new TextRun({ text: t })] }); }
function p(t)  { return new Paragraph({ spacing: { after: 140, line: 300 }, alignment: AlignmentType.JUSTIFIED, children: [new TextRun({ text: t, size: 22 })] }); }
function caption(t) { return new Paragraph({ spacing: { before: 80, after: 260 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: t, size: 19, italics: true, color: GREY })] }); }

// GOTCHA 2 (see below): hardcode each PNG's actual pixel dimensions rather
// than relying on an image-dimension npm package — versions of that
// ecosystem change their export shape often enough to break silently.
const KNOWN_SIZES = {
  '/home/claude/diagrams/example.png': [1300, 812],   // fill in from `file` or PIL after rendering
};
function sizeOf(path) { const [width, height] = KNOWN_SIZES[path]; return { width, height }; }

function imageParagraph(path, maxWidthPx = 560) {
  const { width, height } = sizeOf(path);
  const w = maxWidthPx;
  const h = Math.round(height * (w / width));
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
    children: [ new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: w, height: h } }) ]
  });
}

const children = [];

// Title page
children.push(
  new Paragraph({ spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Report Title", bold: true, size: 58, color: ACCENT })] }),
  new Paragraph({ children: [new PageBreak()] })
);

// One diagram section — repeat this block per diagram
children.push(new Paragraph({ children: [new PageBreak()] }));   // GOTCHA 3: force new page every time
children.push(h1("Diagram N — Title"));
children.push(p("One or two sentences of framing: what this diagram shows and why the top-to-bottom order is meaningful."));
children.push(imageParagraph("/home/claude/diagrams/example.png", 560));
children.push(caption("Figure N. One-line factual caption."));

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
      heading1: { run: { font: "Calibri Light", size: 30, bold: true, color: ACCENT }, paragraph: { spacing: { before: 320, after: 140 } } },
    }
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1300, right: 1300 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 4 } },
      children: [new TextRun({ text: "Report Title — running header", size: 16, color: GREY })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: GREY })] })] }) },
    children
  }]
});

Packer.toBuffer(doc).then(buf => fs.writeFileSync('/home/claude/report.docx', buf));
```

## 8. Gotchas actually hit while building this document (read before you repeat them)

1. **Figma/Canva diagram tools render an interactive widget, not an
   exportable asset, for this pipeline.** Don't spend time trying to chain
   `generate_diagram` into a file download — draw SVG directly instead (§2).

2. **The `image-size` npm package's export shape changes between versions**
   (`require('image-size')` as a function vs. `{ imageSize }` named export).
   Don't fight it — after rendering each PNG, get its real pixel dimensions
   once (`python3 -c "from PIL import Image; print(Image.open('x.png').size)"`
   or the `file` command) and hardcode them in a small lookup object, as in
   the template above. One extra manual step, zero fragile dependency.

3. **The biggest one: without an explicit page break before each diagram,
   docx-js / LibreOffice can paginate in a way that stacks multiple
   full-height images onto what looks like one page in the flow model, even
   though each image is individually sized correctly.** The symptom is a
   suspiciously low final page count (e.g. 8 diagrams landing on 3 pages).
   The fix is always the same: put a `new Paragraph({ children: [new
   PageBreak()] })` immediately before every diagram's heading, don't rely
   on natural flow to separate large images. Verify with `pdfinfo … | grep
   Pages` — you should get roughly (title + intro + one page per diagram).

4. **Verify with `pdfimages -list`, not just a page count.** It reports the
   actual placed width/height/ppi of every embedded image. One image (plus
   its smask) per page, at a sane ppi (150–250 for a ~6in-wide diagram), is
   the signal everything is correctly sized — not just present.

5. **Generous canvas, then trim by viewBox, beats cramming.** It's much
   faster to give a diagram too much vertical space and have visible
   whitespace at the bottom than to fight text overlap by shrinking
   font sizes repeatedly. Adjust the `Diagram(width, height)` call, not the
   font sizes, when something doesn't fit.

## 9. Checklist before calling a diagram-rich docx "done"

- [ ] Read the docx skill before writing any code
- [ ] One consistent color palette used across every diagram and every table
- [ ] Every diagram genuinely reads top-to-bottom (upstream at top, outcome
      at bottom) — if it doesn't, that's a content problem, not a styling one
- [ ] Every diagram has 1–2 sentences of framing prose before it and a
      one-line factual caption after it — never a bare image
- [ ] Explicit page break before every diagram section
- [ ] Converted to PDF and checked: page count matches expectations,
      `pdfimages -list` shows one image per intended page at a sane ppi
- [ ] Copied to `/mnt/user-data/outputs/` and shared via `present_files`
