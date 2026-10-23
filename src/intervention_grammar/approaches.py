"""
Approaches are interventions written as compositions of operators.

Each approach looks at the model as it is when it starts and returns the
operations in the order they are carried out, structure and process operators
mixed. Running a program expands the approaches, so the log shows every
single step and the approach it belongs to.

Where an approach needs to know which connections lie in a zone of a member,
it reads the stations of the connections (the connection attribute "at"), or
takes them from its ``zone`` parameter.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .joint_operators import Detach
from .knowledge_operators import Record
from .operation import Approach
from .process_operators import Insert
from .process_operators import Prop
from .process_operators import Release
from .process_operators import Seat
from .process_operators import Secure
from .process_operators import Unprop
from .process_operators import Withdraw
from .state import InterventionError
from .state import attribute
from .state import attributes
from .state import connection_attribute
from .state import element
from .state import neighbours
from .structure_operators import Add
from .structure_operators import Cut
from .structure_operators import Double
from .structure_operators import Extend
from .structure_operators import Inlay
from .structure_operators import Join
from .structure_operators import Move
from .structure_operators import Remove
from .structure_operators import Reroute
from .structure_operators import Split
from .structure_operators import Trim
from .structure_operators import Turn

__all__ = [
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
]


# ==============================================================================
# Helpers
# ==============================================================================


def _releases(model, member, others=None):
    """Release every secured connection of the member (with others only, if given)."""
    out = []
    for o in neighbours(model, member):
        if others is not None and o not in others:
            continue
        if connection_attribute(model, member, o, "state") == "secured":
            out.append(Release(member, o))
    return out


def _zone(model, member, s0, s1, zone=None):
    """Neighbours whose connection lies between stations s0 and s1 of the member."""
    if zone is not None:
        return list(zone)
    out = []
    for o in neighbours(model, member):
        s = connection_attribute(model, member, o, "at").get(member)
        if s is None:
            raise InterventionError("the station of the connection {} - {} is not known; give zone=[...]".format(member, o))
        if s0 - 1e-9 <= s <= s1 + 1e-9:
            out.append(o)
    return out


def _support(model, member, other, new):
    """The support direction of a connection, with member renamed to new."""
    support = connection_attribute(model, member, other, "support")
    if not support or support == "both":
        return support
    return [new if m == member else m for m in support]


def _length(model, member):
    length = attribute(model, member, "length")
    if length is None:
        raise InterventionError("the length of {} is not known".format(member))
    return length


def _new(name, model):
    """A new member like the old one, still to be inserted."""
    values = attributes(model, name)
    return {"type": values["type"], "length": values["length"], "grounded": values["grounded"]}


# ==============================================================================
# Replacing damaged material
# ==============================================================================


class Patch(Approach):
    """Cut damaged material out of part of a member and fit a new piece.

    Patch = Cut(region) ; Inlay(piece) ; Secure(piece).

    Parameters
    ----------
    member : str
        The member with the damage.
    region : dict
        The part that is cut out, for example ``{"span": [1.8, 2.0], "face": "top", "depth": 0.03}``.
    piece : str, optional
        Name of the new piece. Default ``member.patch``.
    joint : dict, optional
        How the piece is held in the member.

    """

    def __init__(self, member, region, piece=None, joint=None):
        super(Patch, self).__init__()
        self.member = member
        self.region = region
        self.piece = piece or member + ".patch"
        self.joint = joint

    @property
    def __data__(self):
        return {"member": self.member, "region": self.region, "piece": self.piece, "joint": self.joint}

    def operations(self, model):
        return [
            Cut(self.member, self.region),
            Inlay(self.member, self.piece, self.region, self.joint),
            Secure(self.piece, self.member),
        ]


class Prosthesis(Approach):
    """Replace a member over its full section along a length at one end.

    Prosthesis = Release(connections in the zone) ; Split(m, s, J) ; Remove(old end) ;
    Add(piece) ; Insert(piece) ; Seat ; Join(J) ; Join(connections of the zone) ;
    Secure. The rest of the member keeps its name; the old end becomes
    ``member.old`` and the new piece ``member.new``.

    Parameters
    ----------
    member : str
        The member whose end is replaced.
    length : float
        How far the new piece reaches, measured from the end.
    end : str, optional
        "start" (default) or "end".
    joint : dict, optional
        The joint between the remaining member and the new piece.
    zone : list[str], optional
        Neighbours connected within the replaced length, where stations are not known.
    path : str, optional
        How the new piece is brought in.

    """

    def __init__(self, member, length, end="start", joint=None, zone=None, path="straight"):
        super(Prosthesis, self).__init__()
        self.member = member
        self.length = length
        self.end = end
        self.joint = joint
        self.zone = list(zone) if zone else None
        self.path = path

    @property
    def __data__(self):
        return {"member": self.member, "length": self.length, "end": self.end, "joint": self.joint,
                "zone": self.zone, "path": self.path}

    def operations(self, model):
        m = self.member
        element(model, m)
        old, new = m + ".old", m + ".new"
        if self.end == "start":
            at = self.length
            zone = _zone(model, m, 0.0, at, self.zone)
            pieces = [old, m]
        else:
            total = _length(model, m)
            at = total - self.length
            zone = _zone(model, m, at, total, self.zone)
            pieces = [m, old]
        start = zone if self.end == "start" else [o for o in neighbours(model, m) if o not in zone]
        links = {o: connection_attribute(model, m, o, "joint") for o in zone}
        stations = {o: connection_attribute(model, m, o, "at") for o in zone}
        values = _new(m, model)
        values["length"] = self.length
        splice = {new: self.length, m: 0.0} if self.end == "start" else {m: at, new: 0.0}
        ops = _releases(model, m, zone)
        ops += [
            Split(m, at, self.joint, pieces=pieces, start=start if self.zone else None),
            Remove(old),
            Add(new, placed=False, attributes=values),
            Insert(new, self.path),
            Seat(new),
            Join(new, m, self.joint, at=splice),
        ]
        for o in zone:
            s = stations[o]
            at_new = {o: s[o]} if o in s else {}
            if m in s:
                at_new[new] = s[m] if self.end == "start" else round(s[m] - at, 9)
            ops.append(Join(new, o, links[o], at=at_new, support=_support(model, m, o, new)))
        ops += [Secure(new, m)] + [Secure(new, o) for o in zone]
        return ops


class MidProsthesis(Approach):
    """Replace a member over its full section along a length in its middle.

    MidProsthesis = Release ; Split(m, s1) ; Split(m, s0) ; Remove(segment) ;
    Add ; Insert ; Seat ; Join(J0) ; Join(J1) ; Join(connections of the segment) ;
    Secure. The two remaining pieces are ``member.a`` and ``member.b``.

    Parameters
    ----------
    member : str
        The member whose middle segment is replaced.
    span : list[float]
        Stations s0 and s1 of the replaced segment.
    joints : list[dict], optional
        The joints at s0 and at s1.
    zone : list[str], optional
        Neighbours connected within the segment, where stations are not known.
    path : str, optional
        How the new segment is brought in, see :class:`Insert`. Default "straight".

    """

    def __init__(self, member, span, joints=None, zone=None, path="straight"):
        super(MidProsthesis, self).__init__()
        self.member = member
        self.span = list(span)
        self.joints = list(joints) if joints else [None, None]
        self.zone = list(zone) if zone else None
        self.path = path

    @property
    def __data__(self):
        return {"member": self.member, "span": self.span, "joints": self.joints, "zone": self.zone, "path": self.path}

    def operations(self, model):
        m = self.member
        s0, s1 = self.span
        a, b, old, new = m + ".a", m + ".b", m + ".old", m + ".new"
        zone = _zone(model, m, s0, s1, self.zone)
        links = {o: connection_attribute(model, m, o, "joint") for o in zone}
        stations = {o: connection_attribute(model, m, o, "at") for o in zone}
        values = _new(m, model)
        values["length"] = round(s1 - s0, 9)
        right = [o for o in neighbours(model, m) if (connection_attribute(model, m, o, "at").get(m) or 0.0) > s1]
        ops = _releases(model, m, zone)
        ops += [
            Split(m, s1, self.joints[1], pieces=[m + ".rest", b],
                  start=None if self.zone is None else [o for o in neighbours(model, m) if o not in right]),
            Split(m + ".rest", s0, self.joints[0], pieces=[a, old],
                  start=None if self.zone is None else [o for o in neighbours(model, m) if o not in zone and o not in right]),
            Remove(old),
            Add(new, placed=False, attributes=values),
            Insert(new, self.path),
            Seat(new),
            Join(a, new, self.joints[0], at={a: s0, new: 0.0}),
            Join(new, b, self.joints[1], at={new: round(s1 - s0, 9), b: 0.0}),
        ]
        for o in zone:
            s = stations[o]
            at_new = {o: s[o]} if o in s else {}
            if m in s:
                at_new[new] = round(s[m] - s0, 9)
            ops.append(Join(new, o, links[o], at=at_new, support=_support(model, m, o, new)))
        ops += [Secure(a, new), Secure(new, b)] + [Secure(new, o) for o in zone]
        return ops


class Replacement(Approach):
    """Replace a whole member.

    Replacement = Release(all connections of m) ; Withdraw(m) ; Remove(m) ; Add(m') ;
    Insert(m', path) ; Seat ; Join(the old connections) ; Secure. The new member
    keeps the name unless ``new`` is given.

    Parameters
    ----------
    member : str
        The member to replace.
    new : str, optional
        Name of the new member. Default: the name of the old one.
    path : str, optional
        How the new member is brought in, see :class:`Insert`. Default "straight".

    """

    def __init__(self, member, new=None, path="straight"):
        super(Replacement, self).__init__()
        self.member = member
        self.new = new or member
        self.path = path

    @property
    def __data__(self):
        return {"member": self.member, "new": self.new, "path": self.path}

    def operations(self, model):
        m, n = self.member, self.new
        element(model, m)
        others = neighbours(model, m)
        links = {o: connection_attribute(model, m, o, "joint") for o in others}
        stations = {o: connection_attribute(model, m, o, "at") for o in others}
        values = _new(m, model)
        ops = _releases(model, m)
        ops += [Withdraw(m, self.path), Remove(m), Add(n, placed=False, attributes=values), Insert(n, self.path), Seat(n)]
        for o in others:
            s = dict(stations[o])
            if m in s:
                s[n] = s.pop(m)
            ops.append(Join(n, o, links[o], at=s, support=_support(model, m, o, n)))
        ops += [Secure(n, o) for o in others]
        return ops


# ==============================================================================
# Adding material, keeping the damage
# ==============================================================================


class Reinforcement(Approach):
    """Add a piece alongside a member and fasten the two together; the piece shares the member's load path.

    Reinforcement = Double(m, span) ; Secure.

    Parameters
    ----------
    member : str
        The member to reinforce.
    piece : str, optional
        Name of the added piece. Default ``member.double``.
    face : str, optional
        The face of the member it lies on.
    span : list[float], optional
        Stations on the member the piece covers.
    joint : dict, optional
        How the two are fastened.

    """

    def __init__(self, member, piece=None, face=None, span=None, joint=None):
        super(Reinforcement, self).__init__()
        self.member = member
        self.piece = piece or member + ".double"
        self.face = face
        self.span = span
        self.joint = joint

    @property
    def __data__(self):
        return {"member": self.member, "piece": self.piece, "face": self.face, "span": self.span, "joint": self.joint}

    def operations(self, model):
        return [Double(self.member, self.piece, self.face, self.span, self.joint), Secure(self.piece, self.member)]


class Addition(Approach):
    """Introduce a new member that takes part of the load; the damage stays.

    Addition = Cut(for the new connections) ; Add(m_new, connections) ; Secure.

    Parameters
    ----------
    member : str
        Name of the new member.
    between : dict
        ``{existing member: station}`` for each member it is connected to.
    type : str, optional
        The role of the new member, any name.
    joint : dict, optional
        The joint of the new connections.
    length : float, optional
        Length of the new member; its first two connections sit at its two ends.

    """

    def __init__(self, member, between, type=None, joint=None, length=None):
        super(Addition, self).__init__()
        self.member = member
        self.between = dict(between)
        self.type = type
        self.joint = joint
        self.length = length

    @property
    def __data__(self):
        return {"member": self.member, "between": self.between, "type": self.type, "joint": self.joint, "length": self.length}

    def operations(self, model):
        ops = [Cut(o, {"for": self.member, "at": s}) for o, s in self.between.items()]
        ends = [0.0, self.length]
        connections = {}
        for i, (o, s) in enumerate(self.between.items()):
            at = {o: s}
            if self.length is not None and i < 2:
                at[self.member] = ends[i]
            connections[o] = {"joint": self.joint, "at": at}
        values = {"type": self.type}
        if self.length is not None:
            values["length"] = self.length
        ops.append(Add(self.member, connections=connections, attributes=values))
        ops += [Secure(self.member, o) for o in self.between]
        return ops


# ==============================================================================
# Connections and geometry
# ==============================================================================


class Reconnection(Approach):
    """Remake a failed connection with a separate connector.

    Reconnection = Release(j) ; Cut(failed connecting part) ; Detach(j) ; Secure.

    Parameters
    ----------
    member : str
        The member whose connecting part failed.
    other : str
        The member it is connected to.

    """

    def __init__(self, member, other):
        super(Reconnection, self).__init__()
        self.member = member
        self.other = other

    @property
    def __data__(self):
        return {"member": self.member, "other": self.other}

    def operations(self, model):
        return _releases(model, self.member, [self.other]) + [
            Cut(self.member, {"connection": self.other}),
            Detach(self.member, self.other),
            Secure(self.member, self.other),
        ]


class Realignment(Approach):
    """Move members back into line and secure them again.

    Realignment = Release ; Move(members, by) ; Secure.

    Parameters
    ----------
    members : list[str]
        The members to move back into line.
    by : list[float]
        Translation vector in metres.

    """

    def __init__(self, members, by):
        super(Realignment, self).__init__()
        self.members = list(members)
        self.by = list(by)

    @property
    def __data__(self):
        return {"members": self.members, "by": self.by}

    def operations(self, model):
        moving = set(self.members)
        held = []
        for m in self.members:
            for o in neighbours(model, m):
                if o not in moving and connection_attribute(model, m, o, "state") == "secured":
                    held.append((m, o))
        return [Release(m, o) for m, o in held] + [Move(self.members, self.by)] + [Secure(m, o) for m, o in held]


class Subtraction(Approach):
    """Take damaged or harmful material away without replacing it.

    With a region, the material is cut out of the member; without one, the
    whole member is removed.

    Parameters
    ----------
    member : str
        The member to take material from, or to remove.
    region : dict, optional
        The region to cut out, in the form :class:`Cut` takes.

    """

    def __init__(self, member, region=None):
        super(Subtraction, self).__init__()
        self.member = member
        self.region = region

    @property
    def __data__(self):
        return {"member": self.member, "region": self.region}

    def operations(self, model):
        if self.region:
            return [Cut(self.member, self.region)]
        return _releases(model, self.member) + [Remove(self.member)]


class Repositioning(Approach):
    """Take a member out, turn it, and put it back, so that its damaged parts lie where they matter less.

    Repositioning = Release ; Withdraw ; Turn(m) ; Inlay(old connection cuts) ;
    Cut(new ones) ; Insert ; Seat ; Secure.

    Parameters
    ----------
    member : str
        The member to turn.
    mode : str, optional
        "end" or "axis".
    quarter : int, optional
        Quarter turns about the axis, for mode "axis".
    path : str, optional
        How the member is taken out and brought back, see :class:`Insert`. Default "straight".

    """

    def __init__(self, member, mode="end", quarter=0, path="straight"):
        super(Repositioning, self).__init__()
        self.member = member
        self.mode = mode
        self.quarter = quarter
        self.path = path

    @property
    def __data__(self):
        return {"member": self.member, "mode": self.mode, "quarter": self.quarter, "path": self.path}

    def operations(self, model):
        m = self.member
        others = neighbours(model, m)
        return _releases(model, m) + [
            Withdraw(m, self.path),
            Turn(m, self.mode, self.quarter),
            Inlay(m, m + ".fill", {"connections": "old"}),
            Cut(m, {"connections": "new"}),
            Insert(m, self.path),
            Seat(m),
        ] + [Secure(m, o) for o in others] + [Secure(m + ".fill", m)]


# ==============================================================================
# Reconfiguration
# ==============================================================================


class Collapse(Approach):
    """Remove a bay and close the structure up (an edge ring collapse).

    Collapse = Remove(members of the bay) ; Split and Remove(the bay segments of
    the members running through it) ; Move(rest) ; Join ; Secure.

    Parameters
    ----------
    remove : list[str]
        Members that go as a whole.
    ring : dict
        ``{member: [s0, s1]}``: members that run through the bay; the segment
        between the stations is cut out.
    rest : list[str]
        Members beyond the bay that move to close it.
    by : list[float]
        The move that closes the bay.
    joint : dict, optional
        The joint that rejoins the pieces of the members in ``ring``.

    """

    def __init__(self, remove, ring, rest, by, joint=None):
        super(Collapse, self).__init__()
        self.remove = list(remove)
        self.ring = {k: list(v) for k, v in ring.items()}
        self.rest = list(rest)
        self.by = list(by)
        self.joint = joint

    @property
    def __data__(self):
        return {"remove": self.remove, "ring": self.ring, "rest": self.rest, "by": self.by, "joint": self.joint}

    def operations(self, model):
        ops = []
        for m in self.remove:
            ops.append(Remove(m))
        moving = list(self.rest)
        for m, (s0, s1) in self.ring.items():
            left, bay, right = m + ".a", m + ".bay", m + ".b"
            ops += [Split(m, s1, None, pieces=[m + ".rest", right]), Split(m + ".rest", s0, None, pieces=[left, bay]), Remove(bay)]
            moving.append(right)
        for m in self.rest:
            ops += _releases(model, m, [o for o in neighbours(model, m) if o not in self.rest and o not in self.ring])
        ops.append(Move(moving, self.by))
        for m in self.ring:
            ops += [Join(m + ".a", m + ".b", self.joint), Secure(m + ".a", m + ".b")]
        return ops


class Bypass(Approach):
    """Remove a member and let a neighbour that ended on it continue to the next member.

    Bypass = Extend(through) ; Reroute(through, member, to) ; Remove(member) ; Secure.

    Parameters
    ----------
    member : str
        The member that goes.
    through : str
        The neighbour that continues.
    to : str
        The member it is connected to afterwards.
    end : str, optional
        Which end of ``through`` is extended.
    by : float, optional
        How far it is extended.
    at : float, optional
        Station of the new connection on ``to``.

    """

    def __init__(self, member, through, to, end="start", by=0.0, at=None):
        super(Bypass, self).__init__()
        self.member = member
        self.through = through
        self.to = to
        self.end = end
        self.by = by
        self.at = at

    @property
    def __data__(self):
        return {"member": self.member, "through": self.through, "to": self.to, "end": self.end, "by": self.by, "at": self.at}

    def operations(self, model):
        t = self.through
        ops = _releases(model, t, [self.member])
        if self.by:
            ops.append(Extend(t, self.end, self.by))
        at = {}
        if self.at is not None:
            at[self.to] = self.at
        if self.end == "start":
            at[t] = 0.0
        elif attribute(model, t, "length") is not None:
            at[t] = round(attribute(model, t, "length") + self.by, 9)
        ops += [Reroute(t, self.member, self.to, at), Remove(self.member), Secure(t, self.to)]
        return ops


class Lowering(Approach):
    """Shorten the members standing on a base, replace the base and lower everything above onto it.

    The topology stays the same.

    Lowering = Prop ; Remove(base) ; Trim(standing members) ; Add, Insert and
    Seat(new base) ; Move(above, down) ; Join ; Secure ; Unprop.

    Parameters
    ----------
    standing : list[str]
        The members standing on the base; they are shortened at their start.
    base : str
        The member they stand on; it is replaced.
    above : list[str]
        Every member that moves down, the standing members included.
    by : float
        How far, in metres.

    """

    def __init__(self, standing, base, above, by):
        super(Lowering, self).__init__()
        self.standing = list(standing)
        self.base = base
        self.above = list(above)
        self.by = by

    @property
    def __data__(self):
        return {"standing": self.standing, "base": self.base, "above": self.above, "by": self.by}

    def operations(self, model):
        s = self.base
        links = {p: connection_attribute(model, p, s, "joint") for p in self.standing}
        stations = {p: connection_attribute(model, p, s, "at") for p in self.standing}
        values = _new(s, model)
        ops = [Prop(p) for p in self.standing]
        ops += [Remove(s)]
        ops += [Trim(p, "start", self.by) for p in self.standing]
        ops += [Add(s, placed=False, attributes=values), Insert(s), Seat(s)]
        ops.append(Move(self.above, [0.0, 0.0, -self.by]))
        for p in self.standing:
            at = dict(stations[p])
            at[p] = 0.0
            ops.append(Join(p, s, links[p], at=at, support=connection_attribute(model, p, s, "support")))
        ops += [Secure(p, s) for p in self.standing]
        ops += [Unprop(p) for p in self.standing]
        return ops


class Retain(Approach):
    """Leave the structure as it is and record why: the baseline every other approach is compared with.

    Parameters
    ----------
    member : str, optional
        The member the record is about. Default: the structure as a whole.
    note : str, optional
        Why the structure is left as it is.

    """

    def __init__(self, member=None, note="retained, to be monitored"):
        super(Retain, self).__init__()
        self.member = member
        self.note = note

    @property
    def __data__(self):
        return {"member": self.member, "note": self.note}

    def operations(self, model):
        return [Record(self.note, self.member)]
