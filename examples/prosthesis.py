"""A post foot prosthesis on the demo wall: run it, read the log, undo it.

    python examples/prosthesis.py
"""

import compas

from intervention_grammar import demo
from intervention_grammar import run
from intervention_grammar import inverse
from intervention_grammar import original_share
from intervention_grammar import Probe
from intervention_grammar import Prosthesis

wall = demo.wall()
program = [
    Probe("post_3", at=0.1, finding="damaged"),
    Prosthesis("post_3", span=[0, 0.4], joint={"family": "lap", "length": 0.3}),
]

states = run(wall, program)
repaired = states[-1]

print("Steps")
for entry in repaired.graph.attributes["log"]:
    print("  {:2d}  {}".format(entry["step"], entry["text"]))

print("\nOriginal share: {:.1%}".format(original_share(repaired)))

print("\nInverse")
for op in inverse(wall, program):
    print("     ", op)

# a program and every state can be saved as COMPAS JSON
print("\nProgram as JSON: {} characters".format(len(compas.json_dumps(program))))
