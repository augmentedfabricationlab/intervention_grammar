# Approaches

An approach is an operation made of other operations. When a program runs,
each approach is expanded into its operators for the model as it is at that
moment, and each operator is checked and applied in turn. The log lists the
operators.

| Approach | Parameters | What it does | Steps |
|---|---|---|---|
| [`Patch`][intervention_grammar.approaches.Patch] | `member, region, piece, joint` | Cut damaged material out of part of a member and fit a new piece. | Cut ; Inlay ; Secure |
| [`Prosthesis`][intervention_grammar.approaches.Prosthesis] | `member, span, joint, zone, path` | Replace a member over its full section along a span, at an end or in the middle. | Release ; Split, in the middle twice ; Remove the old piece ; Add ; Insert ; Seat ; Join ; Secure |
| [`Replacement`][intervention_grammar.approaches.Replacement] | `member, new, path` | Replace a whole member. | Release ; Withdraw ; Remove ; Add ; Insert ; Seat ; Join ; Secure |
| [`Reinforcement`][intervention_grammar.approaches.Reinforcement] | `member, piece, face, span, joint` | Add a piece alongside a member and fasten the two together; the piece shares the member's load path. | Double ; Secure |
| [`Addition`][intervention_grammar.approaches.Addition] | `member, between, type, joint, length` | Introduce a new member that takes part of the load; the damage stays. | Cut ; Add ; Secure |
| [`Reconnection`][intervention_grammar.approaches.Reconnection] | `member, other` | Remake a failed connection with a separate connector. | Release ; Cut ; Detach ; Secure |
| [`Realignment`][intervention_grammar.approaches.Realignment] | `members, by` | Move members back into line and secure them again. | Release ; Move ; Secure |
| [`Subtraction`][intervention_grammar.approaches.Subtraction] | `member, region` | Take damaged or harmful material away without replacing it. | Cut, or Release ; Remove |
| [`Repositioning`][intervention_grammar.approaches.Repositioning] | `member, mode, quarter, path` | Take a member out, turn it, and put it back, so that its damaged parts lie where they matter less. | Release ; Withdraw ; Turn ; Inlay the old cuts ; Cut new ones ; Insert ; Seat ; Secure |
| [`Collapse`][intervention_grammar.approaches.Collapse] | `remove, ring, rest, by, joint` | Remove a bay and close the structure up (an edge ring collapse). | Remove the members of a bay ; Split and Remove the bay segments ; Move the rest ; Join ; Secure |
| [`Bypass`][intervention_grammar.approaches.Bypass] | `member, through, to, end, by, at` | Remove a member and let a neighbour that ended on it continue to the next member. | Extend ; Reroute ; Remove ; Secure |
| [`Lowering`][intervention_grammar.approaches.Lowering] | `standing, base, above, by` | Shorten the members standing on a base, replace the base and lower everything above onto it. | Prop ; Remove the base ; Trim the standing members ; new base in ; Move down ; Join ; Secure ; Unprop |
| [`Retain`][intervention_grammar.approaches.Retain] | `member, note` | Leave the structure as it is and record why. | Record |

Where an approach needs the connections in a zone of a member, it reads their
stations, or takes them from its `zone` parameter.

[`Retain`][intervention_grammar.approaches.Retain] changes nothing and records
why. The other approaches can be compared with it.

## Writing an approach

A new approach is a subclass of
[`Approach`][intervention_grammar.operation.Approach] with its parameters,
`__data__` for saving it, and `operations(model)`, which returns the
operations in the order they are carried out:

```python
from intervention_grammar import Approach, Release, Withdraw, Turn, Insert, Seat, Secure
from intervention_grammar.state import neighbours


class TurnAround(Approach):
    """Take a member out, turn it end for end, and put it back."""

    def __init__(self, member):
        super(TurnAround, self).__init__()
        self.member = member

    @property
    def __data__(self):
        return {"member": self.member}

    def operations(self, model):
        others = neighbours(model, self.member)
        return (
            [Release(self.member, o) for o in others]
            + [Withdraw(self.member), Turn(self.member, mode="end"), Insert(self.member), Seat(self.member)]
            + [Secure(self.member, o) for o in others]
        )
```

`check` and `inverse` come with the base class: an approach can be applied if
all its operators can, and its inverse is the inverse of its operators in
reverse order.
