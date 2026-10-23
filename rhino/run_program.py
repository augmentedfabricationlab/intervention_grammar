"""
Grasshopper component (Rhino 8, Python 3): run a program and pick a state.

Paste into a Python 3 Script component. intervention_grammar has to be importable in
Rhino: add the repo's src folder to Rhino's Python path, or install it with
Rhino's Python (see README.rst).

Inputs
    model     a compas_model Model; empty: the demo wall
    program   operations, either objects from another component or text, one
              operation per item, written as Python calls, for example
              Prosthesis("post_3", span=[0, 0.4])
    step      the state to output; empty: the last one

Outputs
    states    every state, the model before the first step and after each step
    state     the chosen state
    log       one line per step
    error     why the program stopped, if it did
"""

import intervention_grammar as ig

model = globals().get("model") or ig.demo.wall()
items = [p for p in (globals().get("program") or []) if p is not None]
names = {name: getattr(ig, name) for name in ig.__all__}
operations = [eval(p, {"__builtins__": {}}, names) if isinstance(p, str) else p for p in items]

states, state, log, error = [model], model, [], None
try:
    states = ig.run(model, operations)
except ig.InterventionError as e:
    error = str(e)

if len(states) > 1:
    log = ["{:2d}  {}".format(e["step"], e["text"]) for e in states[-1].graph.attributes["log"]]
s = globals().get("step")
state = states[-1] if s is None else states[max(0, min(int(s), len(states) - 1))]
