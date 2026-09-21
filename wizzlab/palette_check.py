"""Port fiel do validador de paleta (six checks) para Python.

Thresholds e o modelo de simulacao de daltonismo (Machado, Oliveira &
Fernandes, 2009, severidade 1.0) sao os mesmos do validador de referencia.
"""
from __future__ import annotations
import math, sys

BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}
CHROMA_FLOOR = 0.10
CVD_TARGET, CVD_FLOOR = 8.0, 6.0
NORMAL_FLOOR = 15.0
CONTRAST_MIN = 3.0
DEFAULT_SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}

MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868),
               (0.114503, 0.786281, 0.099216),
               (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968),
               (0.280085, 0.672501, 0.047413),
               (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779),
               (-0.078411, 0.930809, 0.147602),
               (0.004733, 0.691367, 0.303900)),
}


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(hexstr: str):
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(_srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def oklab_from_lin(rgb):
    r, g, b = rgb
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (v ** (1 / 3) if v > 0 else -((-v) ** (1 / 3)) for v in (l, m, s))
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def oklch(hexstr: str):
    L, a, b = oklab_from_lin(lin(hexstr))
    return L, math.hypot(a, b), (math.degrees(math.atan2(b, a)) % 360)


def rel_lum(hexstr: str) -> float:
    r, g, b = lin(hexstr)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def simulate(hexstr: str, kind: str):
    r, g, b = lin(hexstr)
    M = MACHADO[kind]
    return tuple(min(1.0, max(0.0, M[i][0] * r + M[i][1] * g + M[i][2] * b)) for i in range(3))


def delta_e(h1: str, h2: str, kind: str | None = None) -> float:
    a = oklab_from_lin(simulate(h1, kind) if kind else lin(h1))
    b = oklab_from_lin(simulate(h2, kind) if kind else lin(h2))
    return 100 * math.dist(a, b)


def validate(palette, mode="light", surface=None, pairs="adjacent"):
    surface = surface or DEFAULT_SURFACE[mode]
    lo, hi = BAND[mode]
    report, ok = [], True

    offband = [(c, round(oklch(c)[0], 3)) for c in palette if not (lo <= oklch(c)[0] <= hi)]
    ok &= not offband
    report.append(("Lightness band", "pass" if not offband else "fail",
                   f"fora da banda: {offband}" if offband else f"todas dentro de L {lo}-{hi}"))

    lowc = [(c, round(oklch(c)[1], 3)) for c in palette if oklch(c)[1] < CHROMA_FLOOR]
    ok &= not lowc
    report.append(("Chroma floor", "pass" if not lowc else "fail",
                   f"abaixo do piso (le como cinza): {lowc}" if lowc else f"todas >= {CHROMA_FLOOR}"))

    n = len(palette)
    if pairs == "all":
        pairlist = [(i, j) for i in range(n) for j in range(i + 1, n)]
    else:
        pairlist = [(i, i + 1) for i in range(n - 1)]

    worst = None
    for kind in ("protan", "deutan"):
        for i, j in pairlist:
            d = delta_e(palette[i], palette[j], kind)
            if worst is None or d < worst[0]:
                worst = (d, kind, palette[i], palette[j])
    tri = min((delta_e(palette[i], palette[j], "tritan") for i, j in pairlist), default=99.0)
    wd = worst[0] if worst else 99.0
    state = "pass" if wd >= CVD_TARGET else ("floor" if wd >= CVD_FLOOR else "fail")
    ok &= state != "fail"
    report.append(("CVD separation", state,
                   f"pior {pairs} {worst[3]}<->{worst[2]} dE {wd:.1f} ({worst[1]}) - tritan {tri:.1f}"
                   if worst else "par unico ou vazio: nao aplicavel"))

    nworst = min(((delta_e(palette[i], palette[j]), palette[i], palette[j]) for i, j in pairlist),
                 default=(99.0, "", ""))
    ok &= nworst[0] >= NORMAL_FLOOR
    report.append(("Normal-vision floor", "pass" if nworst[0] >= NORMAL_FLOOR else "fail",
                   f"pior {pairs} {nworst[2]}<->{nworst[1]} dE {nworst[0]:.1f}"
                   if nworst[1] else "par unico ou vazio: nao aplicavel"))

    low = [(c, round(contrast(c, surface), 2)) for c in palette if contrast(c, surface) < CONTRAST_MIN]
    report.append(("Contrast vs surface", "relief" if low else "pass",
                   f"abaixo de {CONTRAST_MIN}:1 - exige rotulo visivel ou tabela: {low}"
                   if low else f"todas >= {CONTRAST_MIN}:1"))
    return ok, report


def main(argv):
    palette = [c.strip() for c in argv[1].split(",") if c.strip()]
    mode = "dark" if "--mode" in argv and argv[argv.index("--mode") + 1] == "dark" else "light"
    surface = argv[argv.index("--surface") + 1] if "--surface" in argv else None
    pairs = argv[argv.index("--pairs") + 1] if "--pairs" in argv else "adjacent"
    ok, report = validate(palette, mode, surface, pairs)
    width = max(len(r[0]) for r in report)
    for name, state, detail in report:
        print(f"  {name.ljust(width)}  {state.upper():6}  {detail}")
    print("\nRESULTADO:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
