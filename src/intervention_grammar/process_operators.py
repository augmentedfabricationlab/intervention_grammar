"""
Process operators move a structure through the temporary states of an intervention.

Every process operator has an inverse, so taking a member out and putting it
back is one operator followed by its inverse. The checks concern the state of
the model: a member held by secured joints cannot be withdrawn, and a joint can
only be secured once both members are in place. Whether a member can
physically move along a path is outside the scope of this package.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .operation import Operation
from .operation import Sequence
from .state import InterventionError
from .state import attribute
from .state import connection_attribute
from .state import element
from .state import has_connection
from .state import neighbours
from .state import set_attribute
from .state import set_connection_attribute

__all__ = [
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
]


def _held_by(model, member, moving=()):
    """Members that still hold this one with a secured joint."""
    return [o for o in neighbours(model, member)
            if o not in moving and connection_attribute(model, member, o, "state") == "secured"]


# ==============================================================================
# Joints
# ==============================================================================


class Release(Operation):
    """Release a connection: undo its fastening, the members stay in contact.

    Inverse: :class:`Secure`.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.

    """

    layer = "process"

    def __init__(self, a, b):
        super(Release, self).__init__()
        self.a = a
        self.b = b

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b}

    def check(self, model):
        element(model, self.a)
        element(model, self.b)
        if not has_connection(model, self.a, self.b):
            raise InterventionError("{} and {} are not connected".format(self.a, self.b))
        if connection_attribute(model, self.a, self.b, "state") != "secured":
            raise InterventionError("the joint {} - {} is not secured".format(self.a, self.b))

    def apply(self, model):
        set_connection_attribute(model, self.a, self.b, "state", "released")

    def inverse(self, model):
        return Secure(self.a, self.b)


class Secure(Operation):
    """Fasten a connection.

    Inverse: :class:`Release`.

    Both members have to be in place.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.

    """

    layer = "process"

    def __init__(self, a, b):
        super(Secure, self).__init__()
        self.a = a
        self.b = b

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b}

    def check(self, model):
        element(model, self.a)
        element(model, self.b)
        if not has_connection(model, self.a, self.b):
            raise InterventionError("{} and {} are not connected".format(self.a, self.b))
        if connection_attribute(model, self.a, self.b, "state") == "secured":
            raise InterventionError("the joint {} - {} is already secured".format(self.a, self.b))
        for m in (self.a, self.b):
            if attribute(model, m, "placement") != "in":
                raise InterventionError("{} is not in place, the joint cannot be secured".format(m))

    def apply(self, model):
        set_connection_attribute(model, self.a, self.b, "state", "secured")

    def inverse(self, model):
        return Release(self.a, self.b)


# ==============================================================================
# Members out and in
# ==============================================================================


class Withdraw(Operation):
    """Take a member out without destroying it, for reuse or turning.

    Inverse: :class:`Insert`.

    Parameters
    ----------
    member : str
        The member to take out.
    path : str | dict, optional
        "straight" (default), "tilt", "swing", or a description of the path.

    """

    layer = "process"

    def __init__(self, member, path="straight"):
        super(Withdraw, self).__init__()
        self.member = member
        self.path = path

    @property
    def __data__(self):
        return {"member": self.member, "path": self.path}

    def check(self, model):
        element(model, self.member)
        if attribute(model, self.member, "placement") not in ("in", "inserted"):
            raise InterventionError("{} is not in place".format(self.member))
        held = _held_by(model, self.member)
        if held:
            raise InterventionError("{} is still held by secured joints with {}".format(self.member, ", ".join(held)))

    def apply(self, model):
        set_attribute(model, self.member, "placement", "out")

    def inverse(self, model):
        back = Insert(self.member, self.path)
        if attribute(model, self.member, "placement") == "in":
            return Sequence([back, Seat(self.member)])
        return back


class Insert(Operation):
    """Bring a member that is out into place along a path.

    Inverse: :class:`Withdraw`.

    The member is then inserted; :class:`Seat` presses it fully home.

    Parameters
    ----------
    member : str
        The member to bring in.
    path : str | dict, optional
        "straight" (default), "tilt", "swing", or a description of the path.

    """

    layer = "process"

    def __init__(self, member, path="straight"):
        super(Insert, self).__init__()
        self.member = member
        self.path = path

    @property
    def __data__(self):
        return {"member": self.member, "path": self.path}

    def check(self, model):
        element(model, self.member)
        if attribute(model, self.member, "placement") != "out":
            raise InterventionError("{} is not out, it cannot be inserted".format(self.member))

    def apply(self, model):
        set_attribute(model, self.member, "placement", "inserted")

    def inverse(self, model):
        return Withdraw(self.member, self.path)


class Seat(Operation):
    """Press an inserted member fully home.

    Inverse: :class:`Unseat`.

    Parameters
    ----------
    member : str
        The inserted member.

    """

    layer = "process"

    def __init__(self, member):
        super(Seat, self).__init__()
        self.member = member

    @property
    def __data__(self):
        return {"member": self.member}

    def check(self, model):
        element(model, self.member)
        if attribute(model, self.member, "placement") != "inserted":
            raise InterventionError("{} has not been inserted".format(self.member))

    def apply(self, model):
        set_attribute(model, self.member, "placement", "in")

    def inverse(self, model):
        return Unseat(self.member)


class Unseat(Seat):
    """Loosen a seated member so it can be withdrawn.

    Inverse: :class:`Seat`.

    Parameters
    ----------
    member : str
        The seated member.

    """

    def check(self, model):
        element(model, self.member)
        if attribute(model, self.member, "placement") != "in":
            raise InterventionError("{} is not in place".format(self.member))
        held = _held_by(model, self.member)
        if held:
            raise InterventionError("{} is still held by secured joints with {}".format(self.member, ", ".join(held)))

    def apply(self, model):
        set_attribute(model, self.member, "placement", "inserted")

    def inverse(self, model):
        return Seat(self.member)


# ==============================================================================
# Jacking and propping
# ==============================================================================


class Lift(Operation):
    """Jack members up.

    Inverse: :class:`Lower`.

    Joints between the lifted members and members that stay must be released.

    Parameters
    ----------
    members : list[str]
        The members that are jacked up together.
    by : float
        In metres.

    """

    layer = "process"
    sign = 1.0

    def __init__(self, members, by):
        super(Lift, self).__init__()
        self.members = list(members)
        self.by = by

    @property
    def __data__(self):
        return {"members": self.members, "by": self.by}

    def check(self, model):
        for m in self.members:
            element(model, m)
        held = []
        for m in self.members:
            held += ["{} - {}".format(m, o) for o in _held_by(model, m, self.members)]
        if held:
            raise InterventionError("secured joints hold the members: " + ", ".join(held))
        if self.sign < 0:
            low = [m for m in self.members if attribute(model, m, "lift") < self.by - 1e-9]
            if low:
                raise InterventionError("not lifted that far: " + ", ".join(low))

    def apply(self, model):
        for m in self.members:
            set_attribute(model, m, "lift", attribute(model, m, "lift") + self.sign * self.by)

    def inverse(self, model):
        return Lower(self.members, self.by)


class Lower(Lift):
    """Lower jacked members back.

    Inverse: :class:`Lift`.

    Parameters
    ----------
    members : list[str]
        The members that are lowered together.
    by : float
        In metres.

    """

    sign = -1.0

    def inverse(self, model):
        return Lift(self.members, self.by)


class Prop(Operation):
    """Put a temporary prop under a member.

    Inverse: :class:`Unprop`.

    Parameters
    ----------
    member : str
        The member to prop.
    at : float, optional
        Station on the member.

    """

    layer = "process"

    def __init__(self, member, at=None):
        super(Prop, self).__init__()
        self.member = member
        self.at = at

    @property
    def __data__(self):
        return {"member": self.member, "at": self.at}

    def check(self, model):
        element(model, self.member)

    def apply(self, model):
        set_attribute(model, self.member, "props", attribute(model, self.member, "props") + [self.at])

    def inverse(self, model):
        return Unprop(self.member, self.at)


class Unprop(Prop):
    """Take a temporary prop away.

    Inverse: :class:`Prop`.

    Parameters
    ----------
    member : str
        The propped member.
    at : float, optional
        Station of the prop on the member.

    """

    def check(self, model):
        element(model, self.member)
        if self.at not in attribute(model, self.member, "props"):
            raise InterventionError("{} has no prop{}".format(self.member, "" if self.at is None else " at {}".format(self.at)))

    def apply(self, model):
        props = attribute(model, self.member, "props")
        props.remove(self.at)
        set_attribute(model, self.member, "props", props)

    def inverse(self, model):
        return Prop(self.member, self.at)


# ==============================================================================
# Machining
# ==============================================================================


class Machine(Operation):
    """Cut a joint into the end of a member.

    Inverse: :class:`Fill`.

    Parameters
    ----------
    member : str
        The member to machine.
    end : str
        "start" or "end".
    joint : dict
        The joint to cut, a family name and its parameters.

    """

    layer = "process"

    def __init__(self, member, end, joint):
        super(Machine, self).__init__()
        self.member = member
        self.end = end
        self.joint = joint

    @property
    def __data__(self):
        return {"member": self.member, "end": self.end, "joint": self.joint}

    def check(self, model):
        element(model, self.member)
        if self.end not in ("start", "end"):
            raise InterventionError("end must be 'start' or 'end', not {!r}".format(self.end))
        if self.end in attribute(model, self.member, "ends"):
            raise InterventionError("the {} of {} is already machined".format(self.end, self.member))

    def apply(self, model):
        ends = attribute(model, self.member, "ends")
        ends[self.end] = self.joint
        set_attribute(model, self.member, "ends", ends)

    def inverse(self, model):
        return Fill(self.member, self.end)


class Fill(Operation):
    """Fill a machined end with new material: the shape comes back, the original material does not.

    Inverse: :class:`Machine`.

    Parameters
    ----------
    member : str
        The member with the machined end.
    end : str
        "start" or "end".

    """

    layer = "process"

    def __init__(self, member, end):
        super(Fill, self).__init__()
        self.member = member
        self.end = end

    @property
    def __data__(self):
        return {"member": self.member, "end": self.end}

    def check(self, model):
        element(model, self.member)
        if self.end not in attribute(model, self.member, "ends"):
            raise InterventionError("the {} of {} is not machined".format(self.end, self.member))

    def apply(self, model):
        ends = attribute(model, self.member, "ends")
        joint = ends.pop(self.end)
        set_attribute(model, self.member, "ends", ends)
        set_attribute(model, self.member, "fills", attribute(model, self.member, "fills") + [{"end": self.end, "joint": joint}])

    def inverse(self, model):
        return Machine(self.member, self.end, attribute(model, self.member, "ends")[self.end])
