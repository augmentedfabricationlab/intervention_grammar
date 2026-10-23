# Concepts

## State

A structure is a [compas_model](https://github.com/blockresearchgroup/compas_model)
`Model`: members are elements, connections are interactions. The state of the
intervention lives on the model's graph, one set of attributes per element node
and one per connection edge. Element classes stay untouched, so the same
operations run on any compas_model element.

| Element attribute | Values |
|---|---|
| `fabric` | `"original"` or `"new"` |
| `condition` | `"sound"` or `"damaged"` |
| `placement` | `"in"`, `"inserted"` (in place, not yet seated), `"out"` (taken out, kept) or `"missing"` (known, not there) |
| `type` | the role of the member, any name |
| `grounded` | `True` if it stands on the ground |
| `length` | in metres, if known |
| `trim` | change of length at each end, `{"start": d, "end": d}` |
| `turn` | end for end, and quarter turns about the axis |
| `offset` | sum of the moves, `[x, y, z]` |
| `lift` | how far it is jacked up |
| `props` | stations of temporary props |
| `cuts` | regions cut out of it |
| `ends` | joints machined into its ends |
| `fills` | ends filled with new material after machining |
| `findings` | results of probes |
| `notes` | records |
| `exposed` | `True` while it is opened up |
| `log` | numbers of the steps that changed it |

| Connection attribute | Values |
|---|---|
| `joint` | family and parameters, a plain dict |
| `state` | `"secured"`, `"released"` or `"open"` (made, not yet fastened) |
| `at` | station on each member, `{name: metres}` |
| `node` | the point where it meets other connections |
| `support` | `(carried, carrier)` or `"both"`, if known |

All operators change the model through a few basic edits in
[`intervention_grammar.state`][intervention_grammar.state]: add or remove an
element, add or remove a connection, set an attribute on either. Another kind
of model needs only that module translated.

## Operation

Every operator is a COMPAS `Data` class with three methods:

* `check(model)` raises an
  [`InterventionError`][intervention_grammar.state.InterventionError] if the
  operation cannot be applied to the model as it is,
* `apply(model)` changes the model,
* `inverse(model)` returns the operation that undoes it, given the model
  before it was applied.

An operation saves and loads with `compas.json_dump` and `compas.json_load`,
so a program can be written, stored and exchanged as JSON.

## Approach

An [`Approach`][intervention_grammar.operation.Approach] is an operation made
of other operations. It is expanded step by step when it runs, for the model
as it is at that moment. See [Approaches](approaches.md).

## Program

A program is a plain list of operations and approaches.
[`run(model, program)`][intervention_grammar.operation.run] applies it to a
copy of the model and returns every state: the model before the first step and
after each step. Each state carries the log of all steps so far in
`model.graph.attributes["log"]`.
[`inverse(model, program)`][intervention_grammar.operation.inverse] gives the
program that undoes it.

## Levels

The grammar says what changes in a structure. How the steps are ordered and
assigned to people and machines, and how a robot carries them out, are
separate levels, kept in other packages. A program and its states can be
handed to them.

## What is checked

`check` asks whether an operation fits the state: the member exists, a
connection is secured before it can be released, a member held by secured
connections cannot be withdrawn or moved, a connection can only be secured
once both members are in place, a member is out before it is turned, a trim
does not cut through a connection, a split lies inside the member.

Not checked: whether a member can physically move along its path, support and
statics, tool access. These need geometry and are outside the scope of this
package. Without geometry, volumes are unknown, so
[`original_share`][intervention_grammar.measures.original_share] weighs
members by length.
