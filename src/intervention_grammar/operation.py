"""
Operations, approaches, and running them on a model.

An operation has four parts: its parameters, ``check`` (can it be applied to
this model), ``apply`` (change the model) and ``inverse`` (the operation that
undoes it, given the model before it was applied). An approach is an
operation made of other operations. A program is a plain list of operations
and approaches.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas.data import Data

from .state import InterventionError
from .state import attribute
from .state import names
from .state import set_attribute
from .state import snapshot

__all__ = [
    "Operation",
    "Approach",
    "Sequence",
    "run",
    "steps",
    "inverse",
    "changed",
]


class Operation(Data):
    """Base class of all operations.

    Subclasses keep their parameters as attributes of the same name, list them
    in ``__data__``, and implement ``check``, ``apply`` and ``inverse``.

    Attributes
    ----------
    layer : str
        "structure", "joint", "process", "knowledge" or "approach".

    """

    layer = None

    @property
    def __data__(self):
        raise NotImplementedError

    @classmethod
    def __from_data__(cls, data):
        return cls(**data)

    def __repr__(self):
        args = ", ".join("{}={}".format(k, _short(v)) for k, v in self.__data__.items() if v not in (None, {}, []))
        return "{}({})".format(type(self).__name__, args)

    def check(self, model):
        """Raise a :class:`InterventionError` if the operation cannot be applied to the model."""
        pass

    def apply(self, model):
        """Change the model."""
        raise NotImplementedError

    def inverse(self, model):
        """The operation that undoes this one.

        Parameters
        ----------
        model : :class:`compas_model.models.Model`
            The model before this operation was applied.

        Returns
        -------
        :class:`Operation` | None
            None for operations that cannot be undone, such as learning something.

        """
        raise NotImplementedError


def _short(value):
    """A parameter as it is written in a step, elements by their name."""
    if isinstance(value, Data) and not isinstance(value, Operation):
        return "<{} {}>".format(type(value).__name__, value.name)
    if isinstance(value, dict):
        return "{" + ", ".join("{!r}: {}".format(k, _short(v)) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_short(v) for v in value) + "]"
    if isinstance(value, float):
        return "{:g}".format(round(value, 6))
    return repr(value)


class Approach(Operation):
    """An operation made of other operations.

    Subclasses implement ``operations(model)``, which returns the operations in
    the order they are carried out, for the model as it is when the approach
    starts. Operations in the list may be approaches themselves.
    """

    layer = "approach"

    def operations(self, model):
        raise NotImplementedError

    def check(self, model):
        self.apply(model.copy())

    def apply(self, model):
        for op in self.operations(model):
            op.check(model)
            op.apply(model)

    def inverse(self, model):
        return Sequence(inverse(model, [self]))


class Sequence(Approach):
    """A fixed list of operations, applied one after the other.

    Parameters
    ----------
    operations : list[:class:`Operation`]
        The operations, in the order they are applied.

    """

    def __init__(self, operations):
        super(Sequence, self).__init__()
        self._operations = list(operations)

    @property
    def __data__(self):
        return {"operations": self._operations}

    def __repr__(self):
        return "Sequence({})".format(", ".join(repr(op) for op in self._operations))

    def operations(self, model):
        return list(self._operations)


# ==============================================================================
# Running
# ==============================================================================


def steps(model, operations):
    """Apply operations to a copy of the model, one primitive step at a time.

    Approaches are expanded when they are reached, so each step is one
    operation that is not an approach.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model. It is copied and stays unchanged.
    operations : list[:class:`Operation`]
        The program: operations and approaches, in order.

    Yields
    ------
    tuple
        ``(operation, approach, before, after)``: the operation, the innermost
        approach it belongs to (or None), and copies of the model before and
        after it.

    Raises
    ------
    InterventionError
        With the step number and the operation, if one cannot be applied.

    """
    current = model.copy()
    pending = [(op, None) for op in operations]
    number = 0
    while pending:
        op, parent = pending.pop(0)
        if isinstance(op, Approach):
            try:
                pending[0:0] = [(sub, op) for sub in op.operations(current)]
            except InterventionError as error:
                raise InterventionError("step {}, {!r}: {}".format(number + 1, op, error))
            continue
        number += 1
        after = current.copy()
        try:
            op.check(after)
            op.apply(after)
        except InterventionError as error:
            raise InterventionError("step {}, {!r}: {}".format(number, op, error))
        yield op, parent, current, after
        current = after


def run(model, operations):
    """Apply a program to a copy of the model and keep every state.

    The model itself is left unchanged. Each state carries the log of the
    steps so far: ``model.graph.attributes["log"]`` lists every step, and the
    attribute "log" of each element the numbers of the steps that changed it.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model. It is copied and stays unchanged.
    operations : list[:class:`Operation`]
        The program: operations and approaches, in order.

    Returns
    -------
    list[:class:`compas_model.models.Model`]
        The model before the first step and after every step.

    """
    states = [model.copy()]
    log = list(model.graph.attributes.get("log") or [])
    for op, parent, before, after in steps(model, operations):
        number = len(log) + 1
        entry = {
            "step": number,
            "operation": type(op).__name__,
            "layer": op.layer,
            "text": repr(op),
            "data": op.__data__,
            "approach": repr(parent) if parent is not None else None,
        }
        log.append(entry)
        after.graph.attributes["log"] = list(log)
        for name in changed(before, after):
            if name in names(after):
                set_attribute(after, name, "log", attribute(after, name, "log") + [number])
        states.append(after)
    return states


def inverse(model, operations):
    """The operations that undo a program, in the order they are carried out.

    Knowledge operations have no inverse and are left out.

    Parameters
    ----------
    model : :class:`compas_model.models.Model`
        The model the program starts from.
    operations : list[:class:`Operation`]
        The program: operations and approaches, in order.

    Returns
    -------
    list[:class:`Operation`]
        The inverse of every step, last step first.

    """
    undo = []
    for op, parent, before, after in steps(model, operations):
        back = op.inverse(before)
        if back is not None:
            undo.insert(0, back)
    return undo


def changed(before, after):
    """Names of the elements whose state differs between two models.

    Parameters
    ----------
    before : :class:`compas_model.models.Model`
        The earlier state.
    after : :class:`compas_model.models.Model`
        The later state.

    Returns
    -------
    list[str]
        Elements that are new or changed in ``after``, then elements that are gone.

    """
    a, b = snapshot(before), snapshot(after)
    out = [n for n in b if n not in a or a[n] != b[n]]
    out += [n for n in a if n not in b]
    return out
