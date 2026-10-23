# Intervention Grammar

<p class="lead">
A grammar of interventions in existing structures.
</p>

A structure is a set of members and their connections. Operators change it:
they cut, split, join, remove and add members, change the shape of a joint,
release and secure connections, lift and prop, and record what is found.
Approaches compose operators into interventions: repairs, reinforcements,
additions and alterations. A program of operations runs on a model, step by
step, and every step can be undone.

<div class="figures" markdown>
<figure markdown>
  ![The demo wall with a damaged post](_images/wall_probed.svg)
  <figcaption>The demo wall after an inspection. The foot of post_3 is damaged (red ring).</figcaption>
</figure>
<figure markdown>
  ![The same wall after a prosthesis](_images/wall_prosthesis.svg)
  <figcaption>After a prosthesis. The foot is cut off, a new piece (black ring) is joined to the post and rests on the sill.</figcaption>
</figure>
</div>

Each box is a member, coloured by its role. An arrow points from a member to
the member it rests on, down to the ground.

The operators describe what is done to a structure, independent of who does
it: a person, a robot or a program carry out the same Split or Lift. They are
independent of the material as well. Operators that work along a member
(Split, Trim, Extend, Turn, Machine) measure positions in stations along its
axis, so the grammar suits frames and trusses of linear members first.

The structure is a [compas_model](https://github.com/blockresearchgroup/compas_model)
`Model`, and the state of the intervention lives on its graph. The same
operations therefore run on any compas_model element, for example the beams
of a [compas_timber](https://gramaziokohler.github.io/compas_timber/) model.
Every operation is a COMPAS `Data` class and saves and loads as JSON.

```python
from intervention_grammar import demo, run, inverse
from intervention_grammar import Probe, Prosthesis

wall = demo.wall()
program = [
    Probe("post_3", at=0.1, finding="damaged"),
    Prosthesis("post_3", length=0.4, joint={"family": "lap", "length": 0.3}),
]
states = run(wall, program)    # every state, step by step
undo = inverse(wall, program)  # the program that undoes it
```

Start with the [concepts](concepts.md), look up the [operators](operators.md)
and [approaches](approaches.md), or follow the [examples](examples.md).
The drawings on this page are made with
[graph_drawing](https://augmentedfabricationlab.github.io/graph_drawing/).

Intervention Grammar is developed by Tizian Rein at the
[Professorship of Digital Fabrication](https://www.arc.ed.tum.de/df),
Technical University of Munich.
