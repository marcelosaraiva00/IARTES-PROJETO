"""Gera fig-corr-06-pipeline.png — pipeline IARTES em layout em S para artigo."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

COLOR_PRIMARY = "#1e3a5f"
COLOR_SECONDARY = "#6b7f94"
COLOR_TEXT = "#ffffff"
COLOR_ARROW = "#2c3e50"

STEPS = [
    "Entrada",
    "Parsing",
    "Normalização",
    "Classificação",
    "Trie / DAG\n+ otimização",
    "Recomendação\n(sequência)",
    "Avaliação\n(métricas)",
]

# S-shape: 4 no topo (→), 3 embaixo (→) com curva 4→5
POSITIONS = [
    (1.5, 5.0),
    (4.8, 5.0),
    (8.1, 5.0),
    (11.4, 5.0),
    (1.5, 2.2),
    (4.8, 2.2),
    (8.1, 2.2),
]

BOX_W, BOX_H = 2.7, 1.4
CORNER = 0.2


def _color(i: int) -> str:
    return COLOR_PRIMARY if i % 2 == 0 else COLOR_SECONDARY


def _rounded_band(ax, xy, w, h, label: str) -> None:
    band = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        facecolor="#eef2f6",
        edgecolor="#b8c5d0",
        linewidth=0.9,
        linestyle=(0, (4, 3)),
        zorder=0,
    )
    ax.add_patch(band)
    ax.text(xy[0] + 0.2, xy[1] + h - 0.22, label, fontsize=8.5, color="#5a6a7a", style="italic", zorder=1)


def _box(ax, x: float, y: float, text: str, index: int) -> None:
    c = _color(index)
    shadow = FancyBboxPatch(
        (x - BOX_W / 2 + 0.07, y - BOX_H / 2 - 0.07),
        BOX_W,
        BOX_H,
        boxstyle=f"round,pad=0.02,rounding_size={CORNER}",
        facecolor="#000000",
        alpha=0.1,
        edgecolor="none",
        zorder=2,
    )
    ax.add_patch(shadow)
    patch = FancyBboxPatch(
        (x - BOX_W / 2, y - BOX_H / 2),
        BOX_W,
        BOX_H,
        boxstyle=f"round,pad=0.02,rounding_size={CORNER}",
        facecolor=c,
        edgecolor="white",
        linewidth=1.3,
        zorder=3,
    )
    ax.add_patch(patch)
    ax.add_patch(
        plt.Circle(
            (x - BOX_W / 2 + 0.38, y + BOX_H / 2 - 0.34),
            0.24,
            facecolor="white",
            edgecolor=c,
            linewidth=1.1,
            zorder=4,
        )
    )
    ax.text(
        x - BOX_W / 2 + 0.38,
        y + BOX_H / 2 - 0.34,
        str(index + 1),
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=c,
        zorder=5,
    )
    ax.text(
        x,
        y - 0.04,
        text,
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="medium",
        color=COLOR_TEXT,
        linespacing=1.3,
        zorder=5,
    )


def _h_arrow(ax, x1: float, y1: float, x2: float, y2: float) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=15,
            linewidth=2.0,
            color=COLOR_ARROW,
            shrinkA=6,
            shrinkB=6,
            zorder=1,
        )
    )


def _ortho_arrow(ax, points: list[tuple[float, float]]) -> None:
    """Seta ortogonal pelos pontos; cabeça apenas no último segmento."""
    for i in range(len(points) - 2):
        ax.plot(
            [points[i][0], points[i + 1][0]],
            [points[i][1], points[i + 1][1]],
            color=COLOR_ARROW,
            linewidth=2.0,
            solid_capstyle="round",
            zorder=1,
        )
    ax.add_patch(
        FancyArrowPatch(
            points[-2],
            points[-1],
            arrowstyle="-|>",
            mutation_scale=15,
            linewidth=2.0,
            color=COLOR_ARROW,
            shrinkA=0,
            shrinkB=4,
            zorder=1,
        )
    )


def generate(output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 5.8), dpi=300)
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0.8, 6.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(
        6.6,
        5.85,
        "Pipeline — da entrada à avaliação",
        ha="center",
        va="center",
        fontsize=12.5,
        fontweight="bold",
        color=COLOR_PRIMARY,
        zorder=10,
    )

    _rounded_band(ax, (0.2, 4.15), 12.5, 1.65, "Pré-processamento")
    _rounded_band(ax, (0.2, 1.35), 10.5, 1.65, "Modelagem e saída")

    # Setas desenhadas antes das caixas (zorder menor) para não atravessá-las
    for i in range(3):
        x1, y1 = POSITIONS[i]
        x2, y2 = POSITIONS[i + 1]
        _h_arrow(ax, x1 + BOX_W / 2, y1, x2 - BOX_W / 2, y2)

    x4, y4 = POSITIONS[3]
    x5, y5 = POSITIONS[4]
    y_lane = 3.55  # corredor entre as duas faixas, fora das caixas
    _ortho_arrow(
        ax,
        [
            (x4, y4 - BOX_H / 2),
            (x4, y_lane),
            (x5, y_lane),
            (x5, y5 + BOX_H / 2),
        ],
    )

    for i in range(4, 6):
        x1, y1 = POSITIONS[i]
        x2, y2 = POSITIONS[i + 1]
        _h_arrow(ax, x1 + BOX_W / 2, y1, x2 - BOX_W / 2, y2)

    for i, (pos, label) in enumerate(zip(POSITIONS, STEPS)):
        _box(ax, pos[0], pos[1], label, i)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    plt.close(fig)
    print(f"Salvo: {output}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    out = root / "figures" / "corrigidas" / "fig-corr-06-pipeline.png"
    generate(out)
