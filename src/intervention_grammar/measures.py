"""
Measures of an intervention.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .operation import changed
from .state import attribute
from .state import names

__all__ = ["original_share", "touched"]


def original_share(model):
    """Share of the members that are original fabric.

    Weighted by length where every member has one, otherwise counted. Cut
    regions are not subtracted: without geometry their volume is not known.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        A state of the structure.

    Returns
    -------
    float
        Between 0 and 1. Missing members are left out.

    """
    members = [n for n in names(model) if attribute(model, n, "placement") != "missing"]
    if not members:
        return 0.0
    lengths = [attribute(model, n, "length") for n in members]
    weights = lengths if all(x is not None for x in lengths) else [1.0] * len(members)
    original = sum(w for n, w in zip(members, weights) if attribute(model, n, "fabric") == "original")
    return original / sum(weights)


def touched(states):
    """Names of the members a program changed at some step, in the order they were first changed.

    Parameters
    ----------
    states : list[:class:`compas_model.models.Model`]
        As returned by :func:`intervention_grammar.run`.

    Returns
    -------
    list[str]

    """
    out = []
    for before, after in zip(states, states[1:]):
        for name in changed(before, after):
            if name not in out:
                out.append(name)
    return out
