"""
The state of a structure under intervention, kept on a compas_model Model.

Elements are the members of the structure, interactions are their connections.
The state lives on the model's graph: one set of attributes per element
node, one per connection edge. Element classes stay untouched, so the same
operations run on any compas_model element, for example the beams of a
compas_timber TimberModel.

Every operation changes the model only through the functions below. They are
the six basic edits (add or remove an element, add or remove a connection, set
an attribute on either) plus the lookups they need. Moving the grammar to
another kind of model means translating this module.

Element attributes
    fabric      "original" or "new"
    condition   "sound" or "damaged"
    placement   "in" (in place), "inserted" (in place, not yet seated),
                "out" (taken out, kept) or "missing" (known, not there)
    type        the role of the member, any name
    grounded    True if it stands on the ground
    length      in metres, if known
    trim        change of length at each end, {"start": d, "end": d}
    turn        {"reversed": bool, "quarter": 0..3}
    offset      sum of the moves, [x, y, z]
    lift        how far it is jacked up
    props       stations of temporary props
    cuts        regions cut out of it
    ends        joints machined into its ends, {"start": joint, "end": joint}
    fills       ends filled with new material after machining
    findings    results of probes
    notes       records
    exposed     True while it is opened up
    log         numbers of the steps that changed it

Connection attributes
    joint       description of the joint, a dict (family and parameters)
    state       "secured", "released" or "open" (made, not yet fastened)
    at          station of the connection on each member, {name: station}
    node        name of the point where it meets other connections
    support     (carried, carrier) or "both", if known
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from copy import deepcopy

__all__ = [
    "InterventionError",
    "ELEMENT_DEFAULTS",
    "CONNECTION_DEFAULTS",
    "element",
    "has_element",
    "names",
    "attribute",
    "set_attribute",
    "attributes",
    "add_element",
    "remove_element",
    "has_connection",
    "neighbours",
    "connection_attribute",
    "set_connection_attribute",
    "connection_attributes",
    "add_connection",
    "remove_connection",
    "snapshot",
]


class InterventionError(Exception):
    """An operation cannot be applied to the model as it is."""


ELEMENT_DEFAULTS = {
    "fabric": "original",
    "condition": "sound",
    "placement": "in",
    "type": None,
    "grounded": False,
    "length": None,
    "trim": {"start": 0.0, "end": 0.0},
    "turn": {"reversed": False, "quarter": 0},
    "offset": [0.0, 0.0, 0.0],
    "lift": 0.0,
    "props": [],
    "cuts": [],
    "ends": {},
    "fills": [],
    "findings": [],
    "notes": [],
    "exposed": False,
    "log": [],
}

CONNECTION_DEFAULTS = {
    "joint": None,
    "state": "secured",
    "at": {},
    "node": None,
    "support": None,
}

# attributes compas_model keeps on every interaction edge; not part of the state
_MODEL_EDGE_KEYS = ("modifiers", "contacts")


# ==============================================================================
# Elements
# ==============================================================================


def element(model, name):
    """The element with this name.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.

    Returns
    -------
    :class:`compas_model.elements.Element`

    Raises
    ------
    InterventionError
        If the model has no element of that name.

    """
    for e in model.elements():
        if e.name == name:
            return e
    raise InterventionError("there is no member {}".format(name))


def has_element(model, name):
    """True if the model has an element of that name.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.

    Returns
    -------
    bool

    """
    return any(e.name == name for e in model.elements())


def names(model):
    """The names of all elements, in the order of the model.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.

    Returns
    -------
    list[str]

    """
    return [e.name for e in model.elements()]


def _node(model, name):
    return element(model, name).graphnode


def attribute(model, name, key):
    """A state attribute of an element, with its default if it is not set.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.
    key : str
        One of the element attributes listed in the module docstring.

    Returns
    -------
    object
        A copy of the value.

    Raises
    ------
    InterventionError
        If the model has no element of that name.

    """
    value = model.graph.node_attribute(_node(model, name), key)
    if value is None:
        return deepcopy(ELEMENT_DEFAULTS.get(key))
    return deepcopy(value)


def set_attribute(model, name, key, value):
    """Set a state attribute of an element.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.
    key : str
        One of the element attributes listed in the module docstring.
    value : object
        The value. A copy is stored.

    Raises
    ------
    InterventionError
        If the model has no element of that name.

    """
    model.graph.node_attribute(_node(model, name), key, deepcopy(value))


def attributes(model, name):
    """All state attributes of an element, defaults filled in.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.

    Returns
    -------
    dict

    Raises
    ------
    InterventionError
        If the model has no element of that name.

    """
    return {key: attribute(model, name, key) for key in ELEMENT_DEFAULTS}


def add_element(model, item, **values):
    """Add an element and set its state attributes.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    item : str | :class:`compas_model.elements.Element`
        A name for a new plain element, or an element to add.
    **values
        State attributes of the element.

    Returns
    -------
    :class:`compas_model.elements.Element`

    """
    from compas_model.elements import Element

    e = Element(name=item) if isinstance(item, str) else item
    if has_element(model, e.name):
        raise InterventionError("there is already a member {}".format(e.name))
    model.add_element(e)
    for key, value in values.items():
        set_attribute(model, e.name, key, value)
    return e


def remove_element(model, name):
    """Remove an element and its connections.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.

    Raises
    ------
    InterventionError
        If the model has no element of that name.

    """
    model.remove_element(element(model, name))


# ==============================================================================
# Connections
# ==============================================================================


def _edge(model, a, b):
    u, v = _node(model, a), _node(model, b)
    if model.graph.has_edge((u, v)):
        return (u, v)
    if model.graph.has_edge((v, u)):
        return (v, u)
    return None


def has_connection(model, a, b):
    """True if the two elements are connected.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    a : str
        Name of one element.
    b : str
        Name of the other element.

    Returns
    -------
    bool

    """
    return _edge(model, a, b) is not None


def neighbours(model, name):
    """Names of the elements connected to this one.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    name : str
        Name of the element.

    Returns
    -------
    list[str]

    Raises
    ------
    InterventionError
        If the model has no element of that name.

    """
    graph = model.graph
    return [graph.node_element(n).name for n in graph.neighbors(_node(model, name))]


def _existing_edge(model, a, b):
    edge = _edge(model, a, b)
    if edge is None:
        raise InterventionError("{} and {} are not connected".format(a, b))
    return edge


def connection_attribute(model, a, b, key):
    """A state attribute of a connection, with its default if it is not set.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    a : str
        Name of one element.
    b : str
        Name of the other element.
    key : str
        One of the connection attributes listed in the module docstring.

    Returns
    -------
    object
        A copy of the value.

    Raises
    ------
    InterventionError
        If the two elements are not connected.

    """
    value = model.graph.edge_attribute(_existing_edge(model, a, b), key)
    if value is None:
        return deepcopy(CONNECTION_DEFAULTS.get(key))
    return deepcopy(value)


def set_connection_attribute(model, a, b, key, value):
    """Set a state attribute of a connection.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    a : str
        Name of one element.
    b : str
        Name of the other element.
    key : str
        One of the connection attributes listed in the module docstring.
    value : object
        The value. A copy is stored.

    Raises
    ------
    InterventionError
        If the two elements are not connected.

    """
    model.graph.edge_attribute(_existing_edge(model, a, b), key, deepcopy(value))


def connection_attributes(model, a, b):
    """All state attributes of a connection, defaults filled in.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    a : str
        Name of one element.
    b : str
        Name of the other element.

    Returns
    -------
    dict

    Raises
    ------
    InterventionError
        If the two elements are not connected.

    """
    return {key: connection_attribute(model, a, b, key) for key in CONNECTION_DEFAULTS}


def add_connection(model, a, b, **values):
    """Connect two elements and set the state attributes of the connection.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    a : str
        Name of one element.
    b : str
        Name of the other element.
    **values
        State attributes of the connection.

    Raises
    ------
    InterventionError
        If the two elements are already connected.

    """
    if has_connection(model, a, b):
        raise InterventionError("{} and {} are already connected".format(a, b))
    model.add_interaction(element(model, a), element(model, b))
    for key, value in values.items():
        set_connection_attribute(model, a, b, key, value)


def remove_connection(model, a, b):
    """Remove the connection between two elements.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    a : str
        Name of one element.
    b : str
        Name of the other element.

    Raises
    ------
    InterventionError
        If the two elements are not connected.

    """
    _existing_edge(model, a, b)
    model.remove_interaction(element(model, a), element(model, b))


# ==============================================================================
# Comparing states
# ==============================================================================


def snapshot(model, skip=("log",)):
    """The state as plain data, for comparing two states.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model.
    skip : tuple[str], optional
        Element attributes left out. Default: the log.

    Returns
    -------
    dict
        ``{name: (attributes, {neighbour: connection attributes})}``.

    """
    out = {}
    for name in names(model):
        values = {k: v for k, v in attributes(model, name).items() if k not in skip}
        links = {}
        for other in neighbours(model, name):
            links[other] = connection_attributes(model, name, other)
        out[name] = (values, links)
    return out
