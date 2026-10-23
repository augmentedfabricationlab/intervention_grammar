"""
********************************************************************************
intervention_grammar
********************************************************************************

A grammar of interventions in existing structures: primitive operators in four layers, and approaches
composed of them, acting on a structure of members and their connections.

The operators describe what is done to a structure, whoever carries it out.


Main concepts
=============

**State.** A structure is a compas_model ``Model``: members are elements,
connections are interactions. The state of the intervention (fabric, condition, placement,
joint, released or secured, stations) lives on the model's graph, see
:mod:`intervention_grammar.state`. The operators change the model only through the
basic edits defined there.

**Operation.** Every operator is a COMPAS ``Data`` class with ``check``,
``apply`` and ``inverse``:

* structure: Cut, Inlay, Split, Join, Unjoin, Merge, Trim, Extend, Turn, Add,
  Remove, Double, Support, Reroute, SplitNode, MergeNodes, Move, Swap
* joint: Select, Orient, Tilt, Lengthen, Shorten, Mirror, AddFeature, Fasten,
  Detach, Open, Ease
* process: Release, Secure, Withdraw, Insert, Seat, Unseat, Lift, Lower, Prop,
  Unprop, Machine, Fill
* knowledge: Record, Probe, OpenUp, Close

**Approach.** An operation made of other operations: Patch, Prosthesis,
MidProsthesis, Replacement, Reinforcement, Addition, Reconnection,
Realignment, Subtraction, Repositioning, Collapse, Bypass, Lowering, Retain.

**Program.** A plain list of operations and approaches. :func:`run` applies
it to a copy of a model and returns every state, with the log of all steps;
:func:`inverse` gives the program that undoes it.

Example
-------
>>> from intervention_grammar import demo, run, Prosthesis, Probe
>>> wall = demo.wall()
>>> states = run(wall, [Probe("post_3", at=0.1, finding="damaged"), Prosthesis("post_3", length=0.4, joint={"family": "lap"})])
>>> len(states)
12
>>> states[-1].graph.attributes["log"][2]["text"]
"Split(member='post_3', at=0.4, joint={'family': 'lap'}, pieces=['post_3.old', 'post_3'])"

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from . import demo
from . import state
from .__version__ import __author__
from .__version__ import __author_email__
from .__version__ import __copyright__
from .__version__ import __description__
from .__version__ import __license__
from .__version__ import __title__
from .__version__ import __url__
from .__version__ import __version__
from .approaches import Addition
from .approaches import Bypass
from .approaches import Collapse
from .approaches import Lowering
from .approaches import MidProsthesis
from .approaches import Patch
from .approaches import Prosthesis
from .approaches import Realignment
from .approaches import Reconnection
from .approaches import Reinforcement
from .approaches import Replacement
from .approaches import Repositioning
from .approaches import Retain
from .approaches import Subtraction
from .joint_operators import AddFeature
from .joint_operators import Detach
from .joint_operators import Ease
from .joint_operators import Fasten
from .joint_operators import Lengthen
from .joint_operators import Mirror
from .joint_operators import Open
from .joint_operators import Orient
from .joint_operators import Select
from .joint_operators import Shorten
from .joint_operators import Tilt
from .knowledge_operators import Close
from .knowledge_operators import OpenUp
from .knowledge_operators import Probe
from .knowledge_operators import Record
from .measures import original_share
from .measures import touched
from .operation import Approach
from .operation import Operation
from .operation import Sequence
from .operation import changed
from .operation import inverse
from .operation import run
from .operation import steps
from .process_operators import Fill
from .process_operators import Insert
from .process_operators import Lift
from .process_operators import Lower
from .process_operators import Machine
from .process_operators import Prop
from .process_operators import Release
from .process_operators import Seat
from .process_operators import Secure
from .process_operators import Unprop
from .process_operators import Unseat
from .process_operators import Withdraw
from .state import InterventionError
from .structure_operators import Add
from .structure_operators import Cut
from .structure_operators import Double
from .structure_operators import Extend
from .structure_operators import Inlay
from .structure_operators import Join
from .structure_operators import Merge
from .structure_operators import MergeNodes
from .structure_operators import Move
from .structure_operators import Remove
from .structure_operators import Reroute
from .structure_operators import Split
from .structure_operators import SplitNode
from .structure_operators import Support
from .structure_operators import Swap
from .structure_operators import Trim
from .structure_operators import Turn
from .structure_operators import Unjoin

__all__ = [
    "InterventionError",
    "Operation",
    "Approach",
    "Sequence",
    "run",
    "steps",
    "inverse",
    "changed",
    "Cut",
    "Inlay",
    "Split",
    "Join",
    "Unjoin",
    "Merge",
    "Trim",
    "Extend",
    "Turn",
    "Add",
    "Remove",
    "Double",
    "Support",
    "Reroute",
    "SplitNode",
    "MergeNodes",
    "Move",
    "Swap",
    "Select",
    "Orient",
    "Tilt",
    "Lengthen",
    "Shorten",
    "Mirror",
    "AddFeature",
    "Fasten",
    "Detach",
    "Open",
    "Ease",
    "Release",
    "Secure",
    "Withdraw",
    "Insert",
    "Seat",
    "Unseat",
    "Lift",
    "Lower",
    "Prop",
    "Unprop",
    "Machine",
    "Fill",
    "Record",
    "Probe",
    "OpenUp",
    "Close",
    "Patch",
    "Prosthesis",
    "MidProsthesis",
    "Replacement",
    "Reinforcement",
    "Addition",
    "Reconnection",
    "Realignment",
    "Subtraction",
    "Repositioning",
    "Collapse",
    "Bypass",
    "Lowering",
    "Retain",
    "original_share",
    "touched",
    "state",
    "demo",
    "__author__",
    "__author_email__",
    "__copyright__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
]
