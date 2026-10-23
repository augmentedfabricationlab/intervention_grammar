"""
A small wall to try the grammar on.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .state import add_connection
from .state import add_element

__all__ = ["wall"]

TENON = {"family": "tenon"}


def wall():
    r"""A timber wall of two bays without geometry.

    Sill and plate run over both bays, three posts stand between them, one rail
    in each bay, a knee brace from the first post to the plate, and a brace
    from the plate down onto the second rail. Every
    member has a type and a length, every connection a tenon, a support
    direction and the station on both members, and all joints are secured.

    ::

        plate   ======================
                |  /        |   \    |
                | /brace_1  |    \   |    brace_2
                |-----------|--------|    rail_1, rail_2
                |           |        |
        sill    ======================
             post_1      post_2    post_3

    Returns
    -------
    :class:`compas_model.models.Model`

    """
    from compas_model.models import Model

    model = Model(name="wall")
    members = [
        ("sill", "sill", 3.0),
        ("post_1", "post", 2.2),
        ("post_2", "post", 2.2),
        ("post_3", "post", 2.2),
        ("rail_1", "rail", 1.4),
        ("rail_2", "rail", 1.4),
        ("plate", "top", 3.0),
        ("brace_1", "brace", 0.85),
        ("brace_2", "brace", 1.15),
    ]
    for name, kind, length in members:
        add_element(model, name, type=kind, length=length, grounded=(name == "sill"))

    def join(a, b, sa, sb, carried, carrier):
        add_connection(model, a, b, joint=dict(TENON), state="secured", at={a: sa, b: sb}, support=[carried, carrier])

    for post, s in (("post_1", 0.1), ("post_2", 1.5), ("post_3", 2.9)):
        join(post, "sill", 0.0, s, post, "sill")
        join(post, "plate", 2.2, s, "plate", post)
    join("rail_1", "post_1", 0.0, 1.1, "rail_1", "post_1")
    join("rail_1", "post_2", 1.4, 1.1, "rail_1", "post_2")
    join("rail_2", "post_2", 0.0, 1.1, "rail_2", "post_2")
    join("rail_2", "post_3", 1.4, 1.1, "rail_2", "post_3")
    join("brace_1", "post_1", 0.0, 1.6, "brace_1", "post_1")
    join("brace_1", "plate", 0.85, 0.7, "plate", "brace_1")
    join("brace_2", "plate", 0.0, 2.3, "plate", "brace_2")
    join("brace_2", "rail_2", 1.15, 0.6, "brace_2", "rail_2")
    return model
