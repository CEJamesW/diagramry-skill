---
name: diagramry
description: Render structured diagrams as clean SVG or PNG images with SchemDraw 0.22. Use for work and life visual notes, quick-note cards, planning diagrams, clean workflow charts, mind-map-like outlines, and schematic-style visuals built from boxes, circles, arrows, lines, and labels. Also use for analog circuit schematics, op-amp diagrams, RC/RLC networks, signal-flow charts, and control block diagrams. This skill is Chinese-friendly and should be used when the user wants diagram images rather than prose or code alone.
---

# Diagramry.skill

Render technical or structured visual diagrams from a small JSON spec through `scripts/render_diagram.py`. Prefer this skill when the output should be a precise visual figure, especially when the user asks for work notes, life-planning cards, workflow charts, sketch diagrams, simple mind maps, circuit images, or Chinese-labeled structured figures.

## Quick Start

Create the local virtual environment and install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install schemdraw==0.22 matplotlib
```

Render an example:

```powershell
.\.venv\Scripts\python.exe .\scripts\render_diagram.py `
  --input .\assets\examples\rc-lowpass-zh.json `
  --output .\outputs\rc-lowpass-zh.svg
```

## Workflow

1. Decide the diagram family.
   - `circuit` for sequential electrical schematics.
   - `blocks` for control diagrams, signal chains, and DSP modules.
   - `shapes` for low-level boxes, circles, arrows, and annotations.
2. Draft or update the JSON spec.
3. Render to `svg` first.
4. Inspect spacing, then rerun if labels or routing need adjustment.

## Chinese Text Rules

- Prefer Chinese-safe font chains. Default fallback order is `Microsoft YaHei`, `SimHei`, `DengXian`, `SimSun`.
- For boxes and basic shapes, use the built-in text fitting path in `render_diagram.py` instead of raw element labels.
- Keep Chinese labels concise. Multi-line text is supported, but short labels fit best.
- When a label must stay inside a node, let the renderer auto-shrink font size instead of forcing a large fixed size.

## Resources

- `scripts/render_diagram.py`: Main renderer.
- `references/spec.md`: Spec guide.
- `assets/examples/`: Runnable examples.
