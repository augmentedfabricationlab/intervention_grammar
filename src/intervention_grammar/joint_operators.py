"""
Joint operators change the shape of a connection.

A joint is a family and its parameters, kept as a plain dict on the
connection, for example ``{"family": "lap", "length": 0.3, "tilt": 6.0}``.
The grammar stores families and leaves their meaning to other tools.
Topological operators (AddFeature, Fasten, Detach, Open) change which faces, pieces and contacts a joint has; parametric
operators (Orient, Tilt, Lengthen, Shorten, Mirror) change its dimensions and
angles.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .operation import Operation
from .state import InterventionError
from .state import connection_attribute
from .state import element
from .state import has_connection
from .state import set_connection_attribute

__all__ = [
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
]


class JointOperation(Operation):
    """Base class of operations on the joint between two members.

    Subclasses implement ``change(joint)``, which returns the changed joint.
    Unless a subclass has a natural inverse, the inverse selects the joint as
    it was.
    """

    layer = "joint"

    def __init__(self, a, b):
        super(JointOperation, self).__init__()
        self.a = a
        self.b = b

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b}

    def current(self, model):
        """The joint as it is, as a dict."""
        return connection_attribute(model, self.a, self.b, "joint") or {}

    def check(self, model):
        element(model, self.a)
        element(model, self.b)
        if not has_connection(model, self.a, self.b):
            raise InterventionError("{} and {} are not connected".format(self.a, self.b))

    def apply(self, model):
        set_connection_attribute(model, self.a, self.b, "joint", self.change(self.current(model)))

    def change(self, joint):
        raise NotImplementedError

    def inverse(self, model):
        return Select(self.a, self.b, connection_attribute(model, self.a, self.b, "joint"))


class Select(JointOperation):
    """Set the joint of a connection.

    Inverse: :class:`Select` with the previous joint.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    joint : dict
        Family and parameters, for example ``{"family": "lap", "length": 0.3}``.

    """

    def __init__(self, a, b, joint=None):
        super(Select, self).__init__(a, b)
        self.joint = joint

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "joint": self.joint}

    def change(self, joint):
        return dict(self.joint) if self.joint else None


class Orient(JointOperation):
    """Turn the joint about the member axis by quarter turns.

    Inverse: :class:`Orient` by the opposite number of turns.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    turns : int
        Number of quarter turns, negative for the opposite direction. Default 1.

    """

    def __init__(self, a, b, turns=1):
        super(Orient, self).__init__(a, b)
        self.turns = turns

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "turns": self.turns}

    def change(self, joint):
        joint["orientation"] = (joint.get("orientation", 0) + self.turns) % 4
        return joint

    def inverse(self, model):
        return Orient(self.a, self.b, -self.turns)


class Tilt(JointOperation):
    """Tilt a cutting plane of the joint by an angle.

    Inverse: :class:`Tilt` by the opposite angle.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    angle : float
        In degrees.
    plane : str, optional
        Name of the plane, if the joint has several. Without a name the angle
        is kept as "tilt", with one as "tilt_<plane>".

    """

    def __init__(self, a, b, angle, plane=None):
        super(Tilt, self).__init__(a, b)
        self.angle = angle
        self.plane = plane

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "angle": self.angle, "plane": self.plane}

    def change(self, joint):
        key = "tilt" if self.plane is None else "tilt_" + self.plane
        joint[key] = joint.get(key, 0.0) + self.angle
        return joint

    def inverse(self, model):
        return Tilt(self.a, self.b, -self.angle, self.plane)


class Lengthen(JointOperation):
    """Make the joint longer.

    Inverse: :class:`Shorten`.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    by : float
        In metres.

    """

    sign = 1.0

    def __init__(self, a, b, by):
        super(Lengthen, self).__init__(a, b)
        self.by = by

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "by": self.by}

    def check(self, model):
        super(Lengthen, self).check(model)
        length = self.current(model).get("length")
        if length is None:
            raise InterventionError("the joint {} - {} has no length".format(self.a, self.b))
        if length + self.sign * self.by <= 0:
            raise InterventionError("the joint {} - {} is only {:.3f} m long".format(self.a, self.b, length))

    def change(self, joint):
        joint["length"] = joint["length"] + self.sign * self.by
        return joint

    def inverse(self, model):
        return Shorten(self.a, self.b, self.by)


class Shorten(Lengthen):
    """Make the joint shorter.

    Inverse: :class:`Lengthen`.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    by : float
        In metres.

    """

    sign = -1.0

    def inverse(self, model):
        return Lengthen(self.a, self.b, self.by)


class Mirror(JointOperation):
    """Mirror the joint.

    Inverse: :class:`Mirror`.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.

    """

    def change(self, joint):
        joint["mirrored"] = not joint.get("mirrored", False)
        return joint

    def inverse(self, model):
        return Mirror(self.a, self.b)


class AddFeature(JointOperation):
    """Add a feature to the joint.

    Inverse: :class:`Select` with the joint as it was.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    feature : str | dict
        A name, or a dict with a name and parameters.

    """

    def __init__(self, a, b, feature):
        super(AddFeature, self).__init__(a, b)
        self.feature = feature

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "feature": self.feature}

    def change(self, joint):
        joint["features"] = list(joint.get("features") or []) + [self.feature]
        return joint


class Fasten(JointOperation):
    """Add fasteners to the joint.

    Inverse: :class:`Select` with the joint as it was.

    The fasteners become part of the joint's design; :class:`Secure` fastens the connection.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    fastener : str | dict
        The kind of fastener, any name or description.
    count : int, optional
        Number of fasteners. Default 1.

    """

    def __init__(self, a, b, fastener, count=1):
        super(Fasten, self).__init__(a, b)
        self.fastener = fastener
        self.count = count

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "fastener": self.fastener, "count": self.count}

    def change(self, joint):
        joint["fasteners"] = list(joint.get("fasteners") or []) + [{"kind": self.fastener, "count": self.count}]
        return joint


class Detach(JointOperation):
    """Make the connecting part of a joint a separate piece.

    Inverse: :class:`Select` with the joint as it was.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.

    """

    def change(self, joint):
        joint["loose"] = True
        return joint


class Open(JointOperation):
    """Open a joint on one side, so that a member can be inserted from that side.

    Inverse: :class:`Select` with the joint as it was.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    towards : str | list[float]
        The side or direction the joint opens to.

    """

    def __init__(self, a, b, towards):
        super(Open, self).__init__(a, b)
        self.towards = towards

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "towards": self.towards}

    def change(self, joint):
        joint["open"] = self.towards
        return joint


class Ease(JointOperation):
    """Give the joint a clearance for assembly.

    Inverse: :class:`Select` with the joint as it was.

    The clearance applies while a member is inserted and is ignored once it
    is seated.

    Parameters
    ----------
    a : str
        One member of the connection.
    b : str
        The other member of the connection.
    play : float
        The clearance, in metres.

    """

    def __init__(self, a, b, play):
        super(Ease, self).__init__(a, b)
        self.play = play

    @property
    def __data__(self):
        return {"a": self.a, "b": self.b, "play": self.play}

    def change(self, joint):
        joint["ease"] = self.play
        return joint
