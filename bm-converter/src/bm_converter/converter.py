"""
Convert Model_*.txt planetary interior models to AxiSEM .bm format.

Model_*.txt columns: Depth[km]  Vp[km/s]  Vs[km/s]  Rho[g/cm3]  T[K]  g[m/s2]  P[Pa]
.bm columns:         radius[m]  rho[kg/m3]  vp[m/s]  vs[m/s]

Coordinate: depth-from-surface → radius-from-center, rows reversed (center first).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Layer:
    depth_km: float
    vp_kms: float
    vs_kms: float
    rho_gcm3: float


def read_model_txt(path: Path) -> tuple[list[Layer], float]:
    """Return layers and inferred planet radius (km) from the txt file."""
    layers: list[Layer] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            depth, vp, vs, rho = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
            layers.append(Layer(depth, vp, vs, rho))

    if not layers:
        raise ValueError(f"No data rows found in {path}")

    planet_radius_km = layers[-1].depth_km
    return layers, planet_radius_km


def convert(
    layers: list[Layer],
    planet_radius_km: float,
    name: str,
    anelastic: bool = False,
    anisotropic: bool = False,
) -> str:
    """Return the .bm file content as a string."""
    lines: list[str] = []
    lines.append(f"NAME         {name}")
    lines.append(f"ANELASTIC    {'T' if anelastic else 'F'}")
    lines.append(f"ANISOTROPIC  {'T' if anisotropic else 'F'}")
    lines.append("UNITS        m")
    lines.append("COLUMNS      radius rho vp vs")

    for layer in reversed(layers):
        radius_m = (planet_radius_km - layer.depth_km) * 1000.0
        rho_kgm3 = layer.rho_gcm3 * 1000.0
        vp_ms = layer.vp_kms * 1000.0
        vs_ms = layer.vs_kms * 1000.0
        lines.append(f"  {radius_m:12.1f}  {rho_kgm3:10.4f}  {vp_ms:10.4f}  {vs_ms:10.4f}")

    return "\n".join(lines) + "\n"


def convert_file(
    input_path: Path,
    output_path: Path,
    name: str | None = None,
    planet_radius_km: float | None = None,
    anelastic: bool = False,
    anisotropic: bool = False,
) -> None:
    layers, inferred_radius = read_model_txt(input_path)

    if planet_radius_km is not None:
        radius = planet_radius_km
    else:
        radius = inferred_radius

    if name is None:
        name = input_path.stem

    content = convert(layers, radius, name, anelastic, anisotropic)
    output_path.write_text(content)
