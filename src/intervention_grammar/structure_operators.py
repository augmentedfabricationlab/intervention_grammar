"""
Structure operators change what the finished structure is: its members, their
connections, their lengths and their positions.

Collapse and Bypass, which combine several structure operators, are in
:mod:`intervention_grammar.approaches`.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas.geometry import Translation

from .operation import Operation
from .state import ELEMENT_DEFAULTS
from .state import InterventionError
from .state import add_connection
from .state import add_element
from .state import attribute
from .state import attributes
from .state import connection_attribute
from .state import connection_attributes
from .state import element
from .state import has_connection
from .state import has_element
from .state import neighbours
from .state import remove_connection
from .state import remove_element
from .state import set_attribute
from .state import set_connection_attribute

__all__ = [
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
]

ENDS = ("start", "end")


def _require(model, *members):
    for m in members:
        element(model, m)


def _free(model, name):
    if has_element(model, name):
        raise InterventionError("there is already a member {}".format(name))


def _station(model, member, other):
    """Station of the connection to other along member, or None."""
    return connection_attribute(model, member, other, "at").get(member)


def _rename(link, old, new, shift=0.0):
    """Connection attributes with member old renamed to new, its station shifted."""
    link = dict(link)
    at = dict(link["at"])
    if old in at:
        at[new] = round(at.pop(old) + shift, 9)
    link["at"] = at
    if link.get("support") and link["support"] != "both":
        link["support"] = [new if m == old else m for m in link["support"]]
    return link


def _divide(values, at):
    """Share the station-bound attributes of a member between the pieces of a split at station at.

    Findings, props and cuts with a station or span go to the piece they lie
    on (stations on the end piece measured from the cut). Findings without a
    station stay with both pieces, cuts and props without one with the start
    piece. A damaged member whose damage was found at known stations leaves
    the damage only with the pieces that hold it.
    """
    a, b = dict(values), dict(values)
    for key in ("findings", "props", "cuts"):
        a[key], b[key] = [], []
    for f in values["findings"]:
        s = f.get("at")
        if s is None:
            a["findings"].append(f)
            b["findings"].append(f)
        elif s < at:
            a["findings"].append(f)
        else:
            b["findings"].append(dict(f, at=round(s - at, 9)))
    for s in values["props"]:
        if s is None or s < at:
            a["props"].append(s)
        else:
            b["props"].append(round(s - at, 9))
    for c in values["cuts"]:
        span = c.get("span") if isinstance(c, dict) else None
        if not span or span[0] < at:
            a["cuts"].append(c)
        else:
            b["cuts"].append(dict(c, span=[round(x - at, 9) for x in span]))
    damage = [f for f in values["findings"] if f.get("finding") == "damaged"]
    if values["condition"] == "damaged" and damage and all(f.get("at") is not None for f in damage):
        for piece in (a, b):
            piece["condition"] = "damaged" if any(f.get("finding") == "damaged" for f in piece["findings"]) else "sound"
    return a, b


def _unite(va, vb, shift):
    """The station-bound attributes of two pieces as one member, stations of b shifted."""
    findings = list(va["findings"])
    for f in vb["findings"]:
        if f.get("at") is not None:
            findings.append(dict(f, at=round(f["at"] + shift, 9)))
        elif f not in findings:
            findings.append(f)
    props = list(va["props"]) + [p if p is None else round(p + shift, 9) for p in vb["props"]]
    cuts = list(va["cuts"])
    for c in vb["cuts"]:
        span = c.get("span") if isinstance(c, dict) else None
        cuts.append(dict(c, span=[round(x + shift, 9) for x in span]) if span else c)
    condition = "damaged" if "damaged" in (va["condition"], vb["condition"]) else va["condition"]
    return {"findings": findings, "props": props, "cuts": cuts, "condition": condition}


def _lean(values, defaults):
    """Only the values that differ from the defaults."""
    return {k: v for k, v in values.items() if v != defaults.get(k)}


def _copy_element(model, member, name):
    e = element(model, member).copy()
    e.name = name
    return e


# ==============================================================================
# Material
# ==============================================================================


class Cut(Operation):
    """Cut material out of a member.

    Inverse: :class:`Inlay`.

    Parameters
    ----------
    member : str
        The member to cut.
    region : dict
        What is cut, for example ``{"span": [0.0, 0.2], "face": "top", "depth": 0.03}``
        or ``{"for": "member_2"}``. Kept as it is until geometry reads it.

    """

    layer = "structure"

    def __init__(self, member, region=None):
        super(Cut, self).__init__()
        self.member = member
        self.region = region or {}

    @property
    def __data__(self):
        return {"member": self.member, "region": self.region}

    def check(self, model):
        _require(model, self.member)

    def apply(self, model):
        set_attribute(model, self.member, "cuts", attribute(model, self.member, "cuts") + [self.region])

    def inverse(self, model):
        n = len(attribute(model, self.member, "cuts")) + 1
        return Inlay(self.member, "{}.inlay{}".format(self.member, n), self.region)


class Inlay(Operation):
    """Fit a new piece into a member.

    Inverse: :class:`Remove` of the piece.

    The piece is a new element connected to the member; the connection is
    open until it is secured.

    Parameters
    ----------
    member : str
        The member that receives the piece.
    piece : str
        Name of the new piece.
    region : dict, optional
        Where the piece sits.
    joint : dict, optional
        How it is held in the member.

    """

    layer = "structure"

    def __init__(self, member, piece, region=None, joint=None):
        super(Inlay, self).__init__()
        self.member = member
        self.piece = piece
        self.region = region or {}
        self.joint = joint

    @property
    def __data__(self):
        return {"member": self.member, "piece": self.piece, "region": self.region, "joint": self.joint}

    def check(self, model):
        _require(model, self.member)
        _free(model, self.piece)

    def apply(self, model):
        add_element(model, self.piece, fabric="new", notes=[{"region": self.region}])
        add_connection(model, self.piece, self.member, joint=self.joint, state="open")

    def inverse(self, model):
        return Remove(self.piece)


# ==============================================================================
# Splitting and joining
# ==============================================================================


class Split(Operation):
    """Cut a member through at a station; the two pieces meet in a joint.

    Inverse: :class:`Merge`.

    The connections of the member go to the piece on their side of the cut,
    found from the station of each connection on the member (the connection
    attribute "at"). Where stations are not known, ``start`` lists the
    neighbours of the start piece; when it is given, it decides for all of them.

    Parameters
    ----------
    member : str
        The member to cut through.
    at : float
        Station of the cut, in metres from the start of the member.
    joint : dict, optional
        The joint the two pieces meet in, for example ``{"family": "lap", "length": 0.3}``.
    pieces : list[str], optional
        Names of the start and end piece. Default ``member.a`` and ``member.b``.
        One of them may be the member's own name.
    start : list[str], optional
        Neighbours that go to the start piece. All others go to the end piece.

    """

    layer = "structure"

    def __init__(self, member, at, joint=None, pieces=None, start=None):
        super(Split, self).__init__()
        self.member = member
        self.at = at
        self.joint = joint
        self.pieces = list(pieces) if pieces else [member + ".a", member + ".b"]
        self.start = list(start) if start else None

    @property
    def __data__(self):
        return {"member": self.member, "at": self.at, "joint": self.joint, "pieces": self.pieces, "start": self.start}

    def _sides(self, model):
        sides = {}
        for other in neighbours(model, self.member):
            s = _station(model, self.member, other)
            if self.start is not None:
                sides[other] = 0 if other in self.start else 1
            elif s is None:
                raise InterventionError("the station of the connection {} - {} is not known; give start=[...]".format(self.member, other))
            else:
                sides[other] = 0 if s < self.at else 1
        return sides

    def check(self, model):
        _require(model, self.member)
        for p in self.pieces:
            if p != self.member:
                _free(model, p)
        length = attribute(model, self.member, "length")
        if length is not None and not 0 < self.at < length:
            raise InterventionError("{} is {:.3f} m long, it cannot be split at {:.3f}".format(self.member, length, self.at))
        self._sides(model)

    def apply(self, model):
        sides = self._sides(model)
        values = attributes(model, self.member)
        links = {o: connection_attributes(model, self.member, o) for o in sides}
        a, b = self.pieces
        length = values["length"]
        ea, eb = _copy_element(model, self.member, a), _copy_element(model, self.member, b)
        remove_element(model, self.member)
        va, vb = _divide(values, self.at)
        if length is not None:
            va["length"], vb["length"] = self.at, round(length - self.at, 9)
        va["ends"] = {k: v for k, v in values["ends"].items() if k == "start"}
        vb["ends"] = {k: v for k, v in values["ends"].items() if k == "end"}
        va["trim"] = {"start": values["trim"]["start"], "end": 0.0}
        vb["trim"] = {"start": 0.0, "end": values["trim"]["end"]}
        va["log"], vb["log"] = list(values["log"]), list(values["log"])
        add_element(model, ea, **va)
        add_element(model, eb, **vb)
        for other, side in sides.items():
            piece = b if side else a
            add_connection(model, piece, other, **_rename(links[other], self.member, piece, -self.at if side else 0.0))
        add_connection(model, a, b, joint=self.joint, state="open", at={a: self.at, b: 0.0})

    def inverse(self, model):
        return Merge(self.pieces[0], self.pieces[1], into=self.member)


class Merge(Operation):
    """Make two connected pieces one member again.

    Inverse: :class:`Split`.

    The member takes the attributes of the first piece and the connections of
    both; stations on the second piece are shifted by the length of the first.

    Parameters
    ----------
    a : str
        The start piece.
    b : str
        The end piece.
    into : str, optional
        Name of the merged member. Default: the name of ``a``.

    """

    layer = "structure"

    def __init__(self, a, b, into=None):
        super(Merge, self).__init__()
        self.a = a
        self.b = b
        self.into = into or a

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "into": self.into}

    def check(self, model):
        _require(model, self.a, self.b)
        if not has_connection(model, self.a, self.b):
            raise InterventionError("{} and {} are not connected, they cannot be merged".format(self.a, self.b))
        if self.into not in (self.a, self.b):
            _free(model, self.into)

    def apply(self, model):
        va, vb = attributes(model, self.a), attributes(model, self.b)
        la = va["length"]
        links = []
        for piece, shift in ((self.a, 0.0), (self.b, la or 0.0)):
            for other in neighbours(model, piece):
                if other not in (self.a, self.b):
                    links.append((other, _rename(connection_attributes(model, piece, other), piece, self.into, shift)))
        e = _copy_element(model, self.a, self.into)
        remove_element(model, self.a)
        remove_element(model, self.b)
        values = dict(va)
        values.update(_unite(va, vb, la or 0.0))
        if la is not None and vb["length"] is not None:
            values["length"] = round(la + vb["length"], 9)
        values["ends"] = dict(va["ends"])
        values["ends"].update({k: v for k, v in vb["ends"].items() if k == "end"})
        values["trim"] = {"start": va["trim"]["start"], "end": vb["trim"]["end"]}
        if "new" in (va["fabric"], vb["fabric"]) and va["fabric"] != vb["fabric"]:
            values["notes"] = va["notes"] + [{"merged": [self.a, self.b], "fabric": [va["fabric"], vb["fabric"]]}]
        add_element(model, e, **values)
        for other, link in links:
            add_connection(model, self.into, other, **link)

    def inverse(self, model):
        la = attribute(model, self.a, "length")
        splice = connection_attribute(model, self.a, self.b, "joint")
        start = [o for o in neighbours(model, self.a) if o != self.b]
        return Split(self.into, la if la is not None else 0.0, joint=splice, pieces=[self.a, self.b], start=start)


class Join(Operation):
    """Join two members with a joint.

    Inverse: :class:`Unjoin`.

    Parameters
    ----------
    a : str
        The first member.
    b : str
        The second member.
    joint : dict, optional
        The joint, a family name and its parameters.
    state : str, optional
        "open" (default) until it is secured.
    at : dict, optional
        Station of the joint on each member.
    support : list[str], optional
        (carried, carrier), if known.

    """

    layer = "structure"

    def __init__(self, a, b, joint=None, state="open", at=None, support=None):
        super(Join, self).__init__()
        self.a = a
        self.b = b
        self.joint = joint
        self.state = state
        self.at = at or {}
        self.support = support

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "joint": self.joint, "state": self.state, "at": self.at, "support": self.support}

    def check(self, model):
        _require(model, self.a, self.b)
        if has_connection(model, self.a, self.b):
            raise InterventionError("{} and {} are already joined".format(self.a, self.b))

    def apply(self, model):
        add_connection(model, self.a, self.b, joint=self.joint, state=self.state, at=self.at, support=self.support)

    def inverse(self, model):
        return Unjoin(self.a, self.b)


class Unjoin(Operation):
    """Take away the connection between two members.

    Inverse: :class:`Join`.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.

    """

    layer = "structure"

    def __init__(self, a, b):
        super(Unjoin, self).__init__()
        self.a = a
        self.b = b

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b}

    def check(self, model):
        _require(model, self.a, self.b)
        if not has_connection(model, self.a, self.b):
            raise InterventionError("{} and {} are not joined".format(self.a, self.b))

    def apply(self, model):
        remove_connection(model, self.a, self.b)

    def inverse(self, model):
        link = connection_attributes(model, self.a, self.b)
        return Join(self.a, self.b, joint=link["joint"], state=link["state"], at=link["at"], support=link["support"])


# ==============================================================================
# Length and orientation
# ==============================================================================


class Trim(Operation):
    """Shorten a member at one end.

    Inverse: :class:`Extend`.

    Parameters
    ----------
    member : str
        The member to shorten.
    end : str
        "start" or "end".
    by : float
        In metres.

    """

    layer = "structure"
    sign = -1.0

    def __init__(self, member, end, by):
        super(Trim, self).__init__()
        self.member = member
        self.end = end
        self.by = by

    @property
    def __data__(self):
        return {"member": self.member, "end": self.end, "by": self.by}

    def check(self, model):
        _require(model, self.member)
        if self.end not in ENDS:
            raise InterventionError("end must be 'start' or 'end', not {!r}".format(self.end))
        if self.by <= 0:
            raise InterventionError("by must be positive")
        length = attribute(model, self.member, "length")
        if self.sign < 0 and length is not None:
            if self.by >= length:
                raise InterventionError("{} is only {:.3f} m long".format(self.member, length))
            for other in neighbours(model, self.member):
                s = _station(model, self.member, other)
                if s is None:
                    continue
                inside = s < self.by if self.end == "start" else s > length - self.by
                if inside:
                    raise InterventionError("trimming {} by {:.3f} m cuts through its joint with {}".format(self.member, self.by, other))

    def apply(self, model):
        d = self.sign * self.by
        trim = attribute(model, self.member, "trim")
        trim[self.end] = round(trim[self.end] + d, 9)
        set_attribute(model, self.member, "trim", trim)
        length = attribute(model, self.member, "length")
        if length is not None:
            set_attribute(model, self.member, "length", round(length + d, 9))
        if self.end == "start":
            for other in neighbours(model, self.member):
                at = connection_attribute(model, self.member, other, "at")
                if self.member in at:
                    at[self.member] = round(at[self.member] + d, 9)
                    set_connection_attribute(model, self.member, other, "at", at)

    def inverse(self, model):
        return Extend(self.member, self.end, self.by)


class Extend(Trim):
    """Lengthen a member at one end.

    Inverse: :class:`Trim`.

    Parameters
    ----------
    member : str
        The member to lengthen.
    end : str
        "start" or "end".
    by : float
        In metres.

    """

    sign = 1.0

    def inverse(self, model):
        return Trim(self.member, self.end, self.by)


class Turn(Operation):
    """Turn a member that is out: end for end, or about its own axis.

    Inverse: :class:`Turn` in the opposite direction.

    Turning end for end reverses the member, so the stations of its
    connections are measured from the other end. A quarter turn about the axis
    changes which face points where.

    Parameters
    ----------
    member : str
        The member to turn. It has to be out.
    mode : str
        "end" (end for end) or "axis" (about the long axis).
    quarter : int, optional
        Number of quarter turns about the axis, for mode "axis".

    """

    layer = "structure"

    def __init__(self, member, mode="end", quarter=0):
        super(Turn, self).__init__()
        self.member = member
        self.mode = mode
        self.quarter = quarter

    @property
    def __data__(self):
        return {"member": self.member, "mode": self.mode, "quarter": self.quarter}

    def check(self, model):
        _require(model, self.member)
        if self.mode not in ("end", "axis"):
            raise InterventionError("mode must be 'end' or 'axis', not {!r}".format(self.mode))
        if attribute(model, self.member, "placement") != "out":
            raise InterventionError("{} has to be taken out before it can be turned".format(self.member))

    def apply(self, model):
        turn = attribute(model, self.member, "turn")
        if self.mode == "end":
            turn["reversed"] = not turn["reversed"]
            length = attribute(model, self.member, "length")
            if length is not None:
                for other in neighbours(model, self.member):
                    at = connection_attribute(model, self.member, other, "at")
                    if self.member in at:
                        at[self.member] = round(length - at[self.member], 9)
                        set_connection_attribute(model, self.member, other, "at", at)
            trim = attribute(model, self.member, "trim")
            set_attribute(model, self.member, "trim", {"start": trim["end"], "end": trim["start"]})
            ends = attribute(model, self.member, "ends")
            set_attribute(model, self.member, "ends", {("end" if k == "start" else "start"): v for k, v in ends.items()})
        else:
            turn["quarter"] = (turn["quarter"] + self.quarter) % 4
        set_attribute(model, self.member, "turn", turn)

    def inverse(self, model):
        return Turn(self.member, self.mode, (-self.quarter) % 4)


# ==============================================================================
# Members in and out of the structure
# ==============================================================================


class Add(Operation):
    """Add a member to the structure.

    Inverse: :class:`Remove`.

    Parameters
    ----------
    member : str
        Name of the new member.
    like : str, optional
        An existing member to copy (its element, type and length).
    element : :class:`compas_model.elements.Element`, optional
        The element to add, for example a beam. Default: a plain element, or a copy of ``like``.
    placed : bool, optional
        True (default): in place. False: made, but still to be inserted.
    connections : dict, optional
        ``{neighbour: {"joint": ..., "state": ..., "at": ...}}``.
    attributes : dict, optional
        State attributes that differ from those of a new member.

    """

    layer = "structure"

    def __init__(self, member, like=None, element=None, placed=True, connections=None, attributes=None):
        super(Add, self).__init__()
        self.member = member
        self.like = like
        self.element = element
        self.placed = placed
        self.connections = connections or {}
        self.attributes = attributes or {}

    @property
    def __data__(self):
        return {
            "member": self.member,
            "like": self.like,
            "element": self.element,
            "placed": self.placed,
            "connections": self.connections,
            "attributes": self.attributes,
        }

    def check(self, model):
        _free(model, self.member)
        if self.like is not None and self.like != self.member:
            _require(model, self.like)
        for other in self.connections:
            _require(model, other)

    def apply(self, model):
        values = {"fabric": "new", "placement": "in" if self.placed else "out"}
        if self.element is not None:
            item = self.element.copy()
            item.name = self.member
        elif self.like is not None and has_element(model, self.like):
            item = _copy_element(model, self.like, self.member)
            values["type"] = attribute(model, self.like, "type")
            values["length"] = attribute(model, self.like, "length")
        else:
            item = self.member
        values.update(self.attributes)
        add_element(model, item, **values)
        for other, link in self.connections.items():
            link = dict(link)
            link.setdefault("state", "open")
            add_connection(model, self.member, other, **link)

    def inverse(self, model):
        return Remove(self.member)


class Remove(Operation):
    """Take a member out of the structure for good; its connections go with it.

    Inverse: :class:`Add`.

    The inverse brings back the shape and the connections in new material:
    the removed original fabric does not come back.

    Parameters
    ----------
    member : str
        The member to remove.

    """

    layer = "structure"

    def __init__(self, member):
        super(Remove, self).__init__()
        self.member = member

    @property
    def __data__(self):
        return {"member": self.member}

    def check(self, model):
        _require(model, self.member)

    def apply(self, model):
        remove_element(model, self.member)

    def inverse(self, model):
        values = _lean(attributes(model, self.member), ELEMENT_DEFAULTS)
        values.pop("log", None)
        values.pop("fabric", None)
        placed = values.pop("placement", "in") != "out"
        links = {o: _lean(connection_attributes(model, self.member, o), {"state": "open"}) for o in neighbours(model, self.member)}
        for link in links.values():
            for key in ("node", "support"):
                if link.get(key) is None:
                    link.pop(key, None)
        item = element(model, self.member).copy()
        return Add(self.member, element=item, placed=placed, connections=links, attributes=values)


class Double(Operation):
    """Add a piece alongside a member, sharing its load path.

    Inverse: :class:`Remove` of the piece.

    Parameters
    ----------
    member : str
        The member to double.
    piece : str, optional
        Name of the piece. Default ``member.double``.
    face : str, optional
        The face of the member the piece lies against, any name.
    span : list[float], optional
        Stations on the member the piece covers.
    joint : dict, optional
        How the piece is fastened to the member.

    """

    layer = "structure"

    def __init__(self, member, piece=None, face=None, span=None, joint=None):
        super(Double, self).__init__()
        self.member = member
        self.piece = piece or member + ".double"
        self.face = face
        self.span = span
        self.joint = joint

    @property
    def __data__(self):
        return {"member": self.member, "piece": self.piece, "face": self.face, "span": self.span, "joint": self.joint}

    def check(self, model):
        _require(model, self.member)
        _free(model, self.piece)

    def apply(self, model):
        length = None
        if self.span:
            length = self.span[1] - self.span[0]
        add_element(model, self.piece, fabric="new", length=length,
                    notes=[{"doubles": self.member, "face": self.face, "span": self.span}])
        at = {self.member: self.span[0]} if self.span else {}
        add_connection(model, self.piece, self.member, joint=self.joint, state="open", at=at)

    def inverse(self, model):
        return Remove(self.piece)


class Support(Operation):
    """Give a member a permanent support from the ground.

    Inverse: :class:`Remove` of the support.

    Parameters
    ----------
    member : str
        The member to support.
    at : float, optional
        Station on the member.
    support : str, optional
        Name of the new support. Default ``member.support``.
    kind : str, optional
        What kind of support, any name.

    """

    layer = "structure"

    def __init__(self, member, at=None, support=None, kind=None):
        super(Support, self).__init__()
        self.member = member
        self.at = at
        self.support = support or member + ".support"
        self.kind = kind

    @property
    def __data__(self):
        return {"member": self.member, "at": self.at, "support": self.support, "kind": self.kind}

    def check(self, model):
        _require(model, self.member)
        _free(model, self.support)

    def apply(self, model):
        add_element(model, self.support, fabric="new", type=self.kind, grounded=True)
        at = {self.member: self.at} if self.at is not None else {}
        add_connection(model, self.member, self.support, joint={"family": self.kind}, state="open", at=at,
                       support=[self.member, self.support])

    def inverse(self, model):
        return Remove(self.support)


class Reroute(Operation):
    """Connect a member to another one instead.

    Inverse: :class:`Reroute` to the old member.



    Parameters
    ----------
    member : str
        The member whose connection moves.
    old : str
        The member it is connected to now.
    new : str
        The member it is connected to afterwards.
    at : dict, optional
        Stations of the new connection, for example ``{new: 2.6}``. Stations
        not given stay as they were.
    state : str, optional
        State of the new connection, "open" (default) until it is secured.

    """

    layer = "structure"

    def __init__(self, member, old, new, at=None, state="open"):
        super(Reroute, self).__init__()
        self.member = member
        self.old = old
        self.new = new
        self.at = at or {}
        self.state = state

    @property
    def __data__(self):
        return {"member": self.member, "old": self.old, "new": self.new, "at": self.at, "state": self.state}

    def check(self, model):
        _require(model, self.member, self.old, self.new)
        if not has_connection(model, self.member, self.old):
            raise InterventionError("{} is not connected to {}".format(self.member, self.old))
        if has_connection(model, self.member, self.new):
            raise InterventionError("{} is already connected to {}".format(self.member, self.new))

    def apply(self, model):
        link = _rename(connection_attributes(model, self.member, self.old), self.old, self.new)
        link["at"].pop(self.new, None)
        link["at"].update(self.at)
        link["state"] = self.state
        remove_connection(model, self.member, self.old)
        add_connection(model, self.member, self.new, **link)

    def inverse(self, model):
        link = connection_attributes(model, self.member, self.old)
        return Reroute(self.member, self.new, self.old, at=link["at"], state=link["state"])


class SplitNode(Operation):
    """Let some connections of a crowded node meet in a node of their own.

    Inverse: :class:`MergeNodes`.

    A node is a point where several connections meet; the connection attribute
    "node" names it.

    Parameters
    ----------
    node : str
        The node.
    connections : list[list[str]]
        The connections that move, as pairs of member names.
    new : str
        Name of the new node.

    """

    layer = "structure"

    def __init__(self, node, connections, new):
        super(SplitNode, self).__init__()
        self.node = node
        self.connections = [list(c) for c in connections]
        self.new = new

    @property
    def __data__(self):
        return {"node": self.node, "connections": self.connections, "new": self.new}

    def check(self, model):
        for a, b in self.connections:
            _require(model, a, b)
            if connection_attribute(model, a, b, "node") != self.node:
                raise InterventionError("the connection {} - {} is not part of the joint {}".format(a, b, self.node))

    def apply(self, model):
        for a, b in self.connections:
            set_connection_attribute(model, a, b, "node", self.new)

    def inverse(self, model):
        return MergeNodes(self.node, self.new)


class MergeNodes(Operation):
    """Let the connections of two nodes meet in one.

    Inverse: :class:`SplitNode`.

    Parameters
    ----------
    node : str
        The node that stays.
    other : str
        The node whose connections join it.

    """

    layer = "structure"

    def __init__(self, node, other):
        super(MergeNodes, self).__init__()
        self.node = node
        self.other = other

    @property
    def __data__(self):
        return {"node": self.node, "other": self.other}

    def _members(self, model):
        out = []
        for a in [e.name for e in model.elements()]:
            for b in neighbours(model, a):
                if a < b and connection_attribute(model, a, b, "node") == self.other:
                    out.append([a, b])
        return out

    def check(self, model):
        if not self._members(model):
            raise InterventionError("no connection belongs to the joint {}".format(self.other))

    def apply(self, model):
        for a, b in self._members(model):
            set_connection_attribute(model, a, b, "node", self.node)

    def inverse(self, model):
        return SplitNode(self.node, self._members(model), self.other)


# ==============================================================================
# Position
# ==============================================================================


class Move(Operation):
    """Move members permanently.

    Inverse: :class:`Move` by the opposite vector.

    Connections between moving members and members that stay must not be
    secured.

    Parameters
    ----------
    members : list[str]
        The members that move together.
    by : list[float]
        Translation vector in metres.

    """

    layer = "structure"

    def __init__(self, members, by):
        super(Move, self).__init__()
        self.members = list(members)
        self.by = list(by)

    @property
    def __data__(self):
        return {"members": self.members, "by": self.by}

    def check(self, model):
        _require(model, *self.members)
        moving = set(self.members)
        held = []
        for m in self.members:
            for other in neighbours(model, m):
                if other not in moving and connection_attribute(model, m, other, "state") == "secured":
                    held.append("{} - {}".format(m, other))
        if held:
            raise InterventionError("secured connections hold the moving members: " + ", ".join(held))

    def apply(self, model):
        T = Translation.from_vector(self.by)
        for m in self.members:
            offset = attribute(model, m, "offset")
            set_attribute(model, m, "offset", [offset[i] + self.by[i] for i in range(3)])
            e = element(model, m)
            e.transformation = T * e.transformation if e.transformation is not None else T

    def inverse(self, model):
        return Move(self.members, [-x for x in self.by])


class Swap(Operation):
    """Two members that are out exchange their places in the structure.

    Inverse: :class:`Swap`.

    Each takes over the connections of the other.

    Parameters
    ----------
    a : str
        One member that is out.
    b : str
        The other member that is out.

    """

    layer = "structure"

    def __init__(self, a, b):
        super(Swap, self).__init__()
        self.a = a
        self.b = b

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b}

    def check(self, model):
        _require(model, self.a, self.b)
        for m in (self.a, self.b):
            if attribute(model, m, "placement") != "out":
                raise InterventionError("{} has to be taken out before it can change places".format(m))

    def apply(self, model):
        links = {}
        for m in (self.a, self.b):
            links[m] = {}
            for other in neighbours(model, m):
                if other in (self.a, self.b):
                    continue
                links[m][other] = _rename(connection_attributes(model, m, other), m, self.b if m == self.a else self.a)
                remove_connection(model, m, other)
        for m, other_m in ((self.a, self.b), (self.b, self.a)):
            for other, link in links[m].items():
                add_connection(model, other_m, other, **link)

    def inverse(self, model):
        return Swap(self.a, self.b)
