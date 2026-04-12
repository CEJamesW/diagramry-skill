# Spec Format

The renderer accepts JSON specs with three families:

- `circuit`
- `blocks`
- `shapes`

Common output block:

```json
{
  "output": {
    "format": "svg",
    "canvas": "svg",
    "dpi": 160,
    "theme": {
      "bgcolor": "white",
      "color": "black",
      "unit": 3.0,
      "fontsize": 14,
      "font": "Microsoft YaHei,SimHei,DengXian,SimSun"
    }
  }
}
```

## circuit

Use for sequential electrical schematics.

Supported kinds:

- `SourceV`, `SourceI`, `Battery`
- `Resistor`, `ResistorIEC`, `Potentiometer`
- `Capacitor`, `Capacitor2`
- `Inductor`, `Inductor2`
- `Diode`, `Zener`
- `Ground`, `Dot`
- `Line`, `Arrow`
- `Opamp`
- `BjtNpn`, `BjtPnp`, `NFet`, `PFet`
- `Switch`

Good fits:

- passive analog circuits such as RC/RLC filters
- op-amp schematics and feedback networks
- transistor-level small diagrams and sensor front ends

Useful fields:

- `id`
- `kind`
- `direction`
- `length`
- `label`
- `label_loc`
- `font`
- `fontsize`
- `at`
- `at_ref`
- `anchor`
- `to`
- `to_ref`
- `tox`
- `toy`
- `tox_ref`
- `toy_ref`

Reference syntax is `<id>.<anchor>`.

Practical anchors:

- `Opamp`: `in1`, `in2`, `out`, `vd`, `vs`, `n1`, `n2`, `n1a`, `n2a`
- `Dot`: `center`, `start`, `end`

See `assets/examples/opamp-inverting-zh.json` for a compact op-amp example.

## blocks

Use for flowcharts, DSP chains, and control diagrams with absolute placement.

Node kinds:

- Flow: `Terminal`, `Start`, `Box`, `RoundBox`, `Subroutine`, `Decision`, `Data`, `Ellipse`
- DSP: `Square`, `Circle`, `Sum`, `Mixer`, `Amp`, `Adc`, `Dac`, `Filter`, `Oscillator`

Node fields:

- `id`
- `kind`
- `xy`
- `anchor`
- `label`
- `w`, `h`
- `font`
- `fontsize`
- `min_fontsize`
- `text_pad_x`
- `text_pad_y`

Text is overlaid and auto-fitted against the node bounding box.

Connector fields:

- `kind`: `Arrow` or `Line`
- `from`
- `to`
- `double`

## shapes

Use for low-level geometry or manual annotations.

Shape kinds:

- `rect`
- `circle`
- `line`
- `arrow`
- `text`

Examples:

- `rect`: `xy`, `w`, `h`, `label`, `cornerradius`
- `circle`: `center`, `radius`, `label`
- `line`: `points`
- `arrow`: `points`
- `text`: `xy`, `text`, `align`

For `rect` and `circle`, text is centered and auto-fitted.
