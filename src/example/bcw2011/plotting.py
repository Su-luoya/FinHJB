"""Plot styling helpers for BCW2011 paper-style figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def _paper_rcparams():
    return {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.family": "DejaVu Serif",
        "axes.titlesize": 11,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9.5,
    }


def paper_figure(
    figsize=(11, 8),
    *,
    top=0.83,
    bottom=0.09,
    left=0.08,
    right=0.98,
    hspace=0.32,
    wspace=0.24,
):
    """Create a 2x2 paper-style figure."""
    plt.rcParams.update(_paper_rcparams())
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.subplots_adjust(
        top=top,
        bottom=bottom,
        left=left,
        right=right,
        hspace=hspace,
        wspace=wspace,
    )
    return fig, axes


def finalize_axes(ax, *, xlabel="w", ylabel=None, title=None):
    """Apply consistent axis styling."""
    ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if title is not None:
        ax.set_title(title, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.18, linewidth=0.6)


def add_boundary_markers(ax, result, keys, *, alpha=0.28):
    """Draw case-specific vertical markers on an axis."""
    summary = result["summary"]
    color = result["style"]["color"]
    linestyle = result["style"].get("marker_linestyle", ":")
    for key in keys:
        value = summary.get(key)
        if value is None:
            continue
        ax.axvline(value, color=color, linestyle=linestyle, linewidth=1.0, alpha=alpha)


def add_shared_legend(fig, axes, *, ncol=2, y=0.985):
    """Place one figure-level legend above a multi-panel layout."""
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, y),
        ncol=ncol,
        frameon=False,
        columnspacing=1.6,
        handlelength=2.8,
    )


def save_figure(fig, output_path: str | Path):
    """Save the figure and close it."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    return output_path
