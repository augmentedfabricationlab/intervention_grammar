"""
Knowledge operators change what is known about a structure.

Record and Probe leave the structure as it is and have no inverse. OpenUp
removes a covering, so it has an inverse, Close.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .operation import Operation
from .state import InterventionError
from .state import attribute
from .state import element
from .state import set_attribute

__all__ = [
    "Record",
    "Probe",
    "OpenUp",
    "Close",
]


class Record(Operation):
    """Record something about a member, or about the structure.

    It has no inverse.

    Parameters
    ----------
    text : str
        What is recorded.
    member : str, optional
        Without a member, the record goes on the structure.

    """

    layer = "knowledge"

    def __init__(self, text, member=None):
        super(Record, self).__init__()
        self.text = text
        self.member = member

    @property
    def __data__(self):
        return {"text": self.text, "member": self.member}

    def check(self, model):
        if self.member is not None:
            element(model, self.member)

    def apply(self, model):
        if self.member is None:
            model.graph.attributes["notes"] = list(model.graph.attributes.get("notes") or []) + [self.text]
        else:
            set_attribute(model, self.member, "notes", attribute(model, self.member, "notes") + [self.text])

    def inverse(self, model):
        return None


class Probe(Operation):
    """Inspect a member at a station.

    It has no inverse.

    A finding of "sound" or "damaged" sets the member's condition.

    Parameters
    ----------
    member : str
        The member to inspect.
    at : float, optional
        Station of the inspection, if it is local.
    finding : str, optional
        "sound", "damaged", or any description.

    """

    layer = "knowledge"

    def __init__(self, member, at=None, finding=None):
        super(Probe, self).__init__()
        self.member = member
        self.at = at
        self.finding = finding

    @property
    def __data__(self):
        return {"member": self.member, "at": self.at, "finding": self.finding}

    def check(self, model):
        element(model, self.member)

    def apply(self, model):
        found = attribute(model, self.member, "findings") + [{"at": self.at, "finding": self.finding}]
        set_attribute(model, self.member, "findings", found)
        if self.finding in ("sound", "damaged"):
            set_attribute(model, self.member, "condition", self.finding)

    def inverse(self, model):
        return None


class OpenUp(Operation):
    """Remove a covering to expose a member and its connections.

    Inverse: :class:`Close`.

    Parameters
    ----------
    member : str
        The member to expose.
    what : str, optional
        What comes off.

    """

    layer = "knowledge"

    def __init__(self, member, what="covering"):
        super(OpenUp, self).__init__()
        self.member = member
        self.what = what

    @property
    def __data__(self):
        return {"member": self.member, "what": self.what}

    def check(self, model):
        element(model, self.member)
        if attribute(model, self.member, "exposed"):
            raise InterventionError("{} is already open".format(self.member))

    def apply(self, model):
        set_attribute(model, self.member, "exposed", True)

    def inverse(self, model):
        return Close(self.member, self.what)


class Close(OpenUp):
    """Cover an opened member again.

    Inverse: :class:`OpenUp`.

    Parameters
    ----------
    member : str
        The member to cover.
    what : str, optional
        What goes back on.

    """

    def check(self, model):
        element(model, self.member)
        if not attribute(model, self.member, "exposed"):
            raise InterventionError("{} is not open".format(self.member))

    def apply(self, model):
        set_attribute(model, self.member, "exposed", False)

    def inverse(self, model):
        return OpenUp(self.member, self.what)
