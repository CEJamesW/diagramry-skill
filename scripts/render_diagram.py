#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from schemdraw import Drawing, dsp, elements as elm, flow, segments


CJK_FONT_CANDIDATES = [
    "Microsoft YaHei",
    "SimHei",
    "DengXian",
    "SimSun",
]

CIRCUIT_ELEMENTS = {
    "Arrow": elm.Arrow,
    "Battery": elm.Battery,
    "BjtNpn": elm.BjtNpn,
    "BjtPnp": elm.BjtPnp,
    "Capacitor": elm.Capacitor,
    "Capacitor2": elm.Capacitor2,
    "Diode": elm.Diode,
    "Dot": elm.Dot,
    "Ground": elm.Ground,
    "Inductor": elm.Inductor,
    "Inductor2": elm.Inductor2,
    "Line": elm.Line,
    "NFet": elm.NFet,
    "Opamp": elm.Opamp,
    "PFet": elm.PFet,
    "Potentiometer": elm.Potentiometer,
    "Resistor": elm.Resistor,
    "ResistorIEC": elm.ResistorIEC,
    "SourceI": elm.SourceI,
    "SourceV": elm.SourceV,
    "Switch": elm.Switch,
    "Zener": elm.Zener,
}

FLOW_ELEMENTS = {
    "Box": flow.Box,
    "Data": flow.Data,
    "Decision": flow.Decision,
    "Ellipse": flow.Ellipse,
    "RoundBox": flow.RoundBox,
    "Start": flow.Start,
    "Subroutine": flow.Subroutine,
    "Terminal": flow.Terminal,
}

DSP_ELEMENTS = {
    "Adc": dsp.Adc,
    "Amp": dsp.Amp,
    "Circle": dsp.Circle,
    "Dac": dsp.Dac,
    "Filter": dsp.Filter,
    "Mixer": dsp.Mixer,
    "Oscillator": dsp.Oscillator,
    "Square": dsp.Square,
    "Sum": dsp.Sum,
}

CONNECTORS = {
    "Arrow": flow.Arrow,
    "Line": flow.Line,
}


def load_spec(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render SchemDraw diagrams from JSON specs.")
    parser.add_argument("--input", required=True, help="Path to diagram JSON spec.")
    parser.add_argument("--output", required=True, help="Output .svg or .png path.")
    return parser.parse_args()


def point(value: List[float]) -> Tuple[float, float]:
    return float(value[0]), float(value[1])


def resolve_anchor(ref: str, registry: Dict[str, Any]) -> Any:
    elem_id, anchor = ref.split(".", 1)
    if elem_id not in registry:
        raise KeyError(f"Unknown element reference: {elem_id}")
    return getattr(registry[elem_id], anchor)


def default_font(spec: Dict[str, Any], item: Dict[str, Any] | None = None) -> str:
    output = spec.get("output", {})
    theme = output.get("theme", {})
    if item and item.get("font"):
        return item["font"]
    if theme.get("font"):
        return theme["font"]
    return ",".join(CJK_FONT_CANDIDATES)


def resolve_font_name(font_family: str) -> str:
    candidates = [part.strip() for part in font_family.split(",") if part.strip()]
    for candidate in candidates:
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
            return candidate
        except Exception:
            continue
    return candidates[0] if candidates else "sans-serif"


def resolve_font_for_canvas(font_family: str, canvas: str) -> str:
    candidates = [part.strip() for part in font_family.split(",") if part.strip()]
    for candidate in candidates:
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
            return candidate
        except Exception:
            continue
    return candidates[0] if candidates else "sans-serif"


def drawing_from_output(spec: Dict[str, Any], output_path: Path) -> Drawing:
    output = spec.get("output", {})
    theme = output.get("theme", {})
    path_fmt = output_path.suffix.lstrip(".").lower()
    fmt = path_fmt or output.get("format") or "svg"
    canvas = output.get("canvas")
    if canvas is None or (fmt == "png" and canvas == "svg") or (fmt == "svg" and canvas == "matplotlib"):
        canvas = "matplotlib" if fmt == "png" else "svg"

    kwargs: Dict[str, Any] = {
        "show": False,
        "canvas": canvas,
    }
    if "bgcolor" in theme:
        kwargs["bgcolor"] = theme["bgcolor"]
    if "color" in theme:
        kwargs["color"] = theme["color"]
    if "unit" in theme:
        kwargs["unit"] = theme["unit"]
    if "fontsize" in theme:
        kwargs["fontsize"] = theme["fontsize"]
    if "font" in theme:
        kwargs["font"] = resolve_font_for_canvas(theme["font"], canvas)
    return Drawing(**kwargs)


def estimate_text_size(text: str, font_family: str, fontsize: float, linespacing: float = 1.15) -> Tuple[float, float]:
    lines = text.splitlines() or [""]
    prop = FontProperties(family=resolve_font_name(font_family))
    widths: List[float] = []
    heights: List[float] = []
    for line in lines:
        if not line:
            widths.append(fontsize * 0.4)
            heights.append(fontsize)
            continue
        bbox = TextPath((0, 0), line, size=fontsize, prop=prop).get_extents()
        widths.append(float(bbox.width))
        heights.append(float(bbox.height) if bbox.height > 0 else fontsize)
    total_height = sum(heights) + max(0, len(lines) - 1) * fontsize * (linespacing - 1.0)
    return max(widths) if widths else fontsize, total_height


def fit_fontsize(
    text: str,
    font_family: str,
    target_w: float,
    target_h: float,
    base_fontsize: float,
    unit_scale: float,
    min_fontsize: float = 8,
) -> float:
    available_w = max(target_w * unit_scale, 1.0)
    available_h = max(target_h * unit_scale, 1.0)
    size = float(base_fontsize)
    while size > min_fontsize:
        text_w, text_h = estimate_text_size(text, font_family, size)
        if text_w <= available_w and text_h <= available_h:
            return size
        size -= 0.5
    return float(min_fontsize)


def add_text_overlay(
    drawing: Drawing,
    xy: Tuple[float, float],
    text: str,
    font_family: str,
    fontsize: float,
    color: str | None = None,
) -> None:
    canvas = getattr(drawing, "canvas", None) or "svg"
    overlay = elm.Element().at(xy)
    overlay.segments.append(
        segments.SegmentText(
            (0, 0),
            text,
            align=("center", "center"),
            fontsize=fontsize,
            font=resolve_font_for_canvas(font_family, canvas),
            color=color,
        )
    )
    overlay.params["drop"] = (0, 0)
    drawing.add(overlay)


def apply_common_element_ops(element: Any, item: Dict[str, Any], registry: Dict[str, Any], spec: Dict[str, Any]) -> Any:
    direction = item.get("direction")
    if direction:
        length = item.get("length")
        method = getattr(element, direction)
        element = method(length) if length is not None else method()

    if "at" in item:
        element = element.at(point(item["at"]))
    if "at_ref" in item:
        element = element.at(resolve_anchor(item["at_ref"], registry))
    if "anchor" in item:
        element = element.anchor(item["anchor"])
    if "to" in item:
        element = element.to(point(item["to"]))
    if "to_ref" in item:
        element = element.to(resolve_anchor(item["to_ref"], registry))
    if "tox" in item:
        element = element.tox(item["tox"])
    if "tox_ref" in item:
        element = element.tox(resolve_anchor(item["tox_ref"], registry))
    if "toy" in item:
        element = element.toy(item["toy"])
    if "toy_ref" in item:
        element = element.toy(resolve_anchor(item["toy_ref"], registry))
    if item.get("flip"):
        element = element.flip()
    if item.get("reverse"):
        element = element.reverse()
    if "theta" in item:
        element = element.theta(item["theta"])
    if "label" in item:
        label_kwargs: Dict[str, Any] = {}
        if "label_loc" in item:
            label_kwargs["loc"] = item["label_loc"]
        if "fontsize" in item:
            label_kwargs["fontsize"] = item["fontsize"]
        canvas = getattr(registry.get("_drawing"), "canvas", None) if registry else None
        label_kwargs["font"] = resolve_font_for_canvas(default_font(spec, item), canvas or "svg")
        element = element.label(item["label"], **label_kwargs)
    return element


def render_circuit(drawing: Drawing, spec: Dict[str, Any]) -> None:
    registry: Dict[str, Any] = {"_drawing": drawing}
    for item in spec.get("items", []):
        kind = item["kind"]
        if kind not in CIRCUIT_ELEMENTS:
            raise KeyError(f"Unsupported circuit kind: {kind}")
        ctor = CIRCUIT_ELEMENTS[kind]
        kwargs: Dict[str, Any] = {}
        if kind == "Arrow" and "double" in item:
            kwargs["double"] = bool(item["double"])
        element = ctor(**kwargs)
        element = apply_common_element_ops(element, item, registry, spec)
        placed = drawing.add(element)
        item_id = item.get("id")
        if item_id:
            registry[item_id] = placed


def render_blocks(drawing: Drawing, spec: Dict[str, Any]) -> None:
    registry: Dict[str, Any] = {}
    theme = spec.get("output", {}).get("theme", {})
    unit_scale = float(theme.get("unit", 3.0)) * 11.0
    base_fontsize = float(theme.get("fontsize", 14))
    base_color = theme.get("color")
    label_overlays: List[Dict[str, Any]] = []
    for node in spec.get("nodes", []):
        kind = node["kind"]
        ctor = FLOW_ELEMENTS.get(kind) or DSP_ELEMENTS.get(kind)
        if ctor is None:
            raise KeyError(f"Unsupported block kind: {kind}")

        kwargs: Dict[str, Any] = {}
        if "w" in node:
            kwargs["w"] = node["w"]
        if "h" in node:
            kwargs["h"] = node["h"]
        element = ctor(**kwargs)
        element = element.at(point(node["xy"]))
        if "anchor" in node:
            element = element.anchor(node["anchor"])
        placed = drawing.add(element)
        registry[node["id"]] = placed

        if "label" in node:
            bbox = placed.get_bbox(transform=True, includetext=False)
            center = ((bbox.xmin + bbox.xmax) / 2.0, (bbox.ymin + bbox.ymax) / 2.0)
            pad_x = float(node.get("text_pad_x", 0.18))
            pad_y = float(node.get("text_pad_y", 0.14))
            target_w = max((bbox.xmax - bbox.xmin) - (pad_x * 2.0), 0.3)
            target_h = max((bbox.ymax - bbox.ymin) - (pad_y * 2.0), 0.3)
            font_family = default_font(spec, node)
            fontsize = fit_fontsize(
                node["label"],
                font_family,
                target_w=target_w,
                target_h=target_h,
                base_fontsize=float(node.get("fontsize", base_fontsize)),
                unit_scale=unit_scale,
                min_fontsize=float(node.get("min_fontsize", 8)),
            )
            label_overlays.append(
                {
                    "xy": center,
                    "text": node["label"],
                    "font_family": font_family,
                    "fontsize": fontsize,
                    "color": node.get("color") or base_color,
                }
            )

    for conn in spec.get("connectors", []):
        kind = conn.get("kind", "Arrow")
        if kind not in CONNECTORS:
            raise KeyError(f"Unsupported connector kind: {kind}")
        if kind == "Arrow":
            connector = CONNECTORS[kind](double=bool(conn.get("double", False)))
        else:
            connector = CONNECTORS[kind]()
        connector = connector.at(resolve_anchor(conn["from"], registry)).to(resolve_anchor(conn["to"], registry))
        drawing.add(connector)

    for overlay in label_overlays:
        add_text_overlay(
            drawing,
            xy=overlay["xy"],
            text=overlay["text"],
            font_family=overlay["font_family"],
            fontsize=overlay["fontsize"],
            color=overlay["color"],
        )


def style_kwargs(item: Dict[str, Any]) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {}
    for key in ("color", "lw", "ls", "fill", "fontsize"):
        if key in item:
            kwargs[key] = item[key]
    return kwargs


def add_shape_element(drawing: Drawing, item: Dict[str, Any], spec: Dict[str, Any]) -> None:
    base = elm.Element()
    if "xy" in item:
        base = base.at(point(item["xy"]))
    elif item["kind"] == "circle":
        base = base.at(point(item["center"]))
    else:
        base = base.at((0, 0))

    kind = item["kind"]
    skw = style_kwargs(item)
    if kind == "rect":
        w = float(item["w"])
        h = float(item["h"])
        base.segments.append(
            segments.SegmentPoly(
                [(0, 0), (w, 0), (w, h), (0, h)],
                closed=True,
                cornerradius=float(item.get("cornerradius", 0)),
                **{k: v for k, v in skw.items() if k != "fontsize"},
            )
        )
    elif kind == "circle":
        radius = float(item["radius"])
        base.segments.append(
            segments.SegmentCircle(
                (0, 0),
                radius,
                **{k: v for k, v in skw.items() if k != "fontsize"},
            )
        )
    elif kind == "line":
        base.segments.append(
            segments.Segment(
                [point(p) for p in item["points"]],
                **{k: v for k, v in skw.items() if k != "fontsize"},
            )
        )
    elif kind == "arrow":
        line_kwargs = {k: v for k, v in skw.items() if k != "fontsize"}
        line_kwargs["arrow"] = "->"
        base.segments.append(segments.Segment([point(p) for p in item["points"]], **line_kwargs))
    elif kind == "text":
        canvas = getattr(drawing, "canvas", None) or "svg"
        base.segments.append(
            segments.SegmentText(
                (0, 0),
                item["text"],
                align=item.get("align"),
                fontsize=item.get("fontsize", 14),
                font=resolve_font_for_canvas(default_font(spec, item), canvas),
                color=item.get("color"),
            )
        )
    else:
        raise KeyError(f"Unsupported shape kind: {kind}")

    base.params["drop"] = (0, 0)
    placed = drawing.add(base)

    if kind in {"rect", "circle"} and "label" in item:
        bbox = placed.get_bbox(transform=True, includetext=False)
        center = ((bbox.xmin + bbox.xmax) / 2.0, (bbox.ymin + bbox.ymax) / 2.0)
        width = max(bbox.xmax - bbox.xmin, 0.3)
        height = max(bbox.ymax - bbox.ymin, 0.3)
        font_family = default_font(spec, item)
        fit_size = fit_fontsize(
            item["label"],
            font_family,
            target_w=max(width - 0.22, 0.2),
            target_h=max(height - 0.18, 0.2),
            base_fontsize=float(item.get("fontsize", 14)),
            unit_scale=33.0,
            min_fontsize=float(item.get("min_fontsize", 8)),
        )
        add_text_overlay(
            drawing,
            xy=center,
            text=item["label"],
            font_family=font_family,
            fontsize=fit_size,
            color=item.get("color") or spec.get("output", {}).get("theme", {}).get("color"),
        )


def render_shapes(drawing: Drawing, spec: Dict[str, Any]) -> None:
    for item in spec.get("items", []):
        add_shape_element(drawing, item, spec)


def save_drawing(drawing: Drawing, spec: Dict[str, Any], output_path: Path) -> None:
    fmt = (output_path.suffix.lstrip(".") or spec.get("output", {}).get("format")).lower()
    if fmt not in {"svg", "png"}:
        raise ValueError(f"Unsupported output format: {fmt}")
    dpi = spec.get("output", {}).get("dpi", 160)
    fig = drawing.draw(show=False)
    fig.save(str(output_path), dpi=dpi)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spec = load_spec(input_path)
    drawing = drawing_from_output(spec, output_path)
    diagram_type = spec["type"]

    if diagram_type == "circuit":
        render_circuit(drawing, spec)
    elif diagram_type == "blocks":
        render_blocks(drawing, spec)
    elif diagram_type == "shapes":
        render_shapes(drawing, spec)
    else:
        raise ValueError(f"Unsupported diagram type: {diagram_type}")

    save_drawing(drawing, spec, output_path)
    print(str(output_path))


if __name__ == "__main__":
    main()
