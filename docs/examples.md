# Examples

The examples use [`demo.wall`][intervention_grammar.demo.wall], a timber wall
of two bays without geometry: a sill and a plate over both bays, three posts,
two rails and two braces, all joints secured.

## A prosthesis

The foot of `post_3` is found damaged. A prosthesis cuts the post through above
the damage, removes the old foot and joins a new piece to the post and to the
sill.

```python
from intervention_grammar import demo, run, inverse, original_share
from intervention_grammar import Probe, Prosthesis

wall = demo.wall()
program = [
    Probe("post_3", at=0.1, finding="damaged"),
    Prosthesis("post_3", span=[0, 0.4], joint={"family": "lap", "length": 0.3}),
]

states = run(wall, program)
for entry in states[-1].graph.attributes["log"]:
    print(entry["step"], entry["text"])
```

The approach expands into the operators it is made of:

```text
 1  Probe(member='post_3', at=0.1, finding='damaged')
 2  Release(a='post_3', b='sill')
 3  Split(member='post_3', at=0.4, joint={'family': 'lap', 'length': 0.3}, pieces=['post_3.old', 'post_3'])
 4  Remove(member='post_3.old')
 5  Add(member='post_3.new', placed=False, attributes={'type': 'post', 'length': 0.4, 'grounded': False})
 6  Insert(member='post_3.new', path='straight')
 7  Seat(member='post_3.new')
 8  Join(a='post_3.new', b='post_3', joint={'family': 'lap', 'length': 0.3}, state='open', at={'post_3.new': 0.4, 'post_3': 0}, support=['post_3', 'post_3.new'])
 9  Join(a='post_3.new', b='sill', joint={'family': 'tenon'}, state='open', at={'sill': 2.9, 'post_3.new': 0}, support=['post_3.new', 'sill'])
10  Secure(a='post_3.new', b='post_3')
11  Secure(a='post_3.new', b='sill')
```

`states` holds twelve models: the wall before the first step and after each
of the eleven steps. `original_share(states[-1])` gives 97.7 %, the share of
the wall that is still original material, weighed by length.

## Undoing it

```python
for op in inverse(wall, program):
    print(op)
```

```text
Release(a='post_3.new', b='sill')
Release(a='post_3.new', b='post_3')
Unjoin(a='post_3.new', b='sill')
Unjoin(a='post_3.new', b='post_3')
Unseat(member='post_3.new')
Withdraw(member='post_3.new', path='straight')
Remove(member='post_3.new')
Add(member='post_3.old', element=<Element post_3.old>, placed=True, connections={...}, attributes={...})
Merge(a='post_3.old', b='post_3', into='post_3')
Secure(a='post_3', b='sill')
```

The inverse brings the structure back to its shape. The old foot returns as
the element it was, with its condition and findings. The probe has no
inverse.

## When an operation does not fit

`run` checks every step before it applies it, and stops at the first one that
does not fit the state:

```python
from intervention_grammar import InterventionError, Withdraw

try:
    run(wall, [Withdraw("post_3")])
except InterventionError as error:
    print(error)
```

```text
step 1, Withdraw(member='post_3', path='straight'): post_3 is still held by secured joints with sill, plate, rail_2
```

## Saving a program

Operations are COMPAS `Data`, so a program and every state save and load as
JSON:

```python
import compas

compas.json_dump(program, "program.json")
program = compas.json_load("program.json")
```

## Drawing the states

[graph_drawing](https://augmentedfabricationlab.github.io/graph_drawing/)
draws a model with its state as a graph: members as boxes coloured by type,
arrows from the carried member to the carrying one, rings for damaged and new
members. Placing every member where it is in the wall keeps the drawing
readable, as on the [home page](index.md):

```python
from graph_drawing import models

# the middle of every member in the wall, in metres
where = {
    "sill": (1.5, 0.0), "plate": (1.5, 2.2),
    "post_1": (0.1, 1.1), "post_2": (1.5, 1.1), "post_3": (2.9, 1.3), "post_3.new": (2.9, 0.2),
    "rail_1": (0.8, 1.1), "rail_2": (2.2, 1.1),
    "brace_1": (0.4, 1.9), "brace_2": (2.2, 1.65),
}
positions = {name: (2.2 * x, 2.2 * y) for name, (x, y) in where.items()}

drawing = models.drawing(states[-1], positions=positions)
with open("after.svg", "w") as f:
    f.write(drawing.to_svg())
drawing.to_pdf("after.pdf")
```

## In Grasshopper

`rhino/run_program.py` is the body of a Python 3 Script component. Its input
`program` takes operation objects or text, one operation per item:

```text
Probe("post_3", at=0.1, finding="damaged")
Prosthesis("post_3", span=[0, 0.4], joint={"family": "lap", "length": 0.3})
```

The outputs are every state, one chosen state, the log and the error.
