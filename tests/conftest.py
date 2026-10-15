import matplotlib

matplotlib.use("Agg")

import matplotlib as mpl  # noqa: E402
import pytest  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

import visualific as vf  # noqa: E402


@pytest.fixture(autouse=True)
def _restore_rcparams():
    """Undo any vf.use() or rcParams change made by a test."""
    with mpl.rc_context():
        yield


@pytest.fixture
def house():
    """Apply the house style for one test."""
    with vf.style():
        yield


def make_figure(width="elsevier-single", height=60.0) -> Figure:
    """A figure at its final size, made without pyplot."""
    return Figure(figsize=vf.figsize(width, height))


def clean_figure(width="elsevier-single") -> Figure:
    """A small figure that follows every house rule."""
    fig = make_figure(width)
    ax = fig.add_subplot()
    x = [0, 1, 2, 3, 4]
    for i, kw in enumerate(vf.qual.styles(3)):
        ax.plot(x, [v * (i + 1) for v in x], label=f"Model {i + 1}", **kw)
    ax.plot(x, [v * 1.5 for v in x], color=vf.OBSERVED_GREY, label="Observed")
    ax.set_xlabel("Time (d)")
    ax.set_ylabel(r"Discharge (m$^3$ s$^{-1}$)")
    ax.legend()
    return fig
