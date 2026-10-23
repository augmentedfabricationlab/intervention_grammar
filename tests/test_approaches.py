import compas
import pytest

from intervention_grammar import Addition
from intervention_grammar import Bypass
from intervention_grammar import Collapse
from intervention_grammar import InterventionError
from intervention_grammar import Lowering
from intervention_grammar import MidProsthesis
from intervention_grammar import Patch
from intervention_grammar import Probe
from intervention_grammar import Prosthesis
from intervention_grammar import Realignment
from intervention_grammar import Reconnection
from intervention_grammar import Reinforcement
from intervention_grammar import Release
from intervention_grammar import Replacement
from intervention_grammar import Repositioning
from intervention_grammar import Retain
from intervention_grammar import Sequence
from intervention_grammar import Subtraction
from intervention_grammar import Withdraw
from intervention_grammar import demo
from intervention_grammar import inverse
from intervention_grammar import original_share
from intervention_grammar import run
from intervention_grammar import state as st
from intervention_grammar import touched

WALL = ["post_1", "post_2", "post_3", "rail_1", "rail_2", "plate", "brace_1", "brace_2"]

# every approach, on the demo wall
CASES = {
    "patch": Patch("sill", {"span": [1.8, 2.0], "face": "top", "depth": 0.03}),
    "prosthesis": Prosthesis("post_3", 0.4),
    "prosthesis at the end": Prosthesis("plate", 0.5, end="end"),
    "mid prosthesis": MidProsthesis("sill", [0.6, 1.2]),
    "replacement": Replacement("rail_2"),
    "reinforcement": Reinforcement("rail_1", span=[0.2, 1.2]),
    "addition": Addition("brace_3", {"post_3": 1.6, "plate": 2.3}, length=0.85),
    "reconnection": Reconnection("rail_1", "post_2"),
    "realignment": Realignment(["post_3"], [0.0, -0.01, 0.0]),
    "subtraction": Subtraction("brace_1"),
    "repositioning": Repositioning("rail_2"),
    "collapse": Collapse(["post_3", "rail_2", "brace_2"], {"sill": [1.6, 2.8], "plate": [1.6, 2.8]}, [], [-1.2, 0.0, 0.0]),
    "bypass": Bypass("rail_2", "brace_2", "sill", end="end", by=1.1, at=2.6),
    "lowering": Lowering(["post_1", "post_2", "post_3"], "sill", WALL, 0.2),
    "retain": Retain("post_3"),
}

# approaches whose inverse fills cuts with new pieces: the shape comes back, with extra pieces of new wood
WITH_CUTS = ("patch", "addition", "reconnection", "repositioning")


@pytest.mark.parametrize("name", sorted(CASES))
def test_approach_runs_and_undoes(name):
    model = demo.wall()
    program = [CASES[name]]
    states = run(model, program)
    log = states[-1].graph.attributes["log"]
    assert len(log) == len(states) - 1
    assert all(e["approach"] for e in log)
    back = run(states[-1], inverse(model, program))[-1]
    skip = ("log", "fabric", "cuts", "fills", "notes")
    before, after = st.snapshot(model, skip), st.snapshot(back, skip)
    if name in WITH_CUTS:
        for n in before:
            assert before[n][0] == after[n][0], n
        assert set(before) <= set(after)
    else:
        assert before == after


@pytest.mark.parametrize("name", sorted(CASES))
def test_approach_survives_json(name):
    program = [CASES[name]]
    back = compas.json_loads(compas.json_dumps(program))
    a, b = run(demo.wall(), program)[-1], run(demo.wall(), back)[-1]
    assert st.snapshot(a) == st.snapshot(b)


def test_prosthesis_steps():
    states = run(demo.wall(), [Probe("post_3", 0.1, "damaged"), Prosthesis("post_3", 0.4)])
    m = states[-1]
    steps = [e["operation"] for e in m.graph.attributes["log"]]
    assert steps == ["Probe", "Release", "Split", "Remove", "Add", "Insert", "Seat", "Join", "Join", "Secure", "Secure"]
    assert not st.has_element(m, "post_3.old")
    assert st.attribute(m, "post_3", "fabric") == "original"
    assert st.attribute(m, "post_3", "length") == pytest.approx(1.8)
    assert st.attribute(m, "post_3.new", "fabric") == "new"
    assert sorted(st.neighbours(m, "post_3.new")) == ["post_3", "sill"]
    assert st.connection_attribute(m, "post_3.new", "sill", "state") == "secured"
    assert st.connection_attribute(m, "post_3.new", "sill", "at") == {"post_3.new": 0.0, "sill": 2.9}
    assert st.connection_attribute(m, "post_3.new", "sill", "support") == ["post_3.new", "sill"]
    assert st.connection_attribute(m, "post_3.new", "post_3", "support") == ["post_3", "post_3.new"]
    assert original_share(m) == pytest.approx(1.0 - 0.4 / sum(st.attribute(m, n, "length") for n in st.names(m)))


def test_prosthesis_leaves_the_damage_with_the_old_end():
    m = run(demo.wall(), [Probe("post_3", 0.1, "damaged"), Probe("post_3", 1.5, "sound"), Prosthesis("post_3", 0.4)])[-1]
    assert st.attribute(m, "post_3", "condition") == "sound"
    assert st.attribute(m, "post_3", "findings") == [{"at": pytest.approx(1.1), "finding": "sound"}]
    m = run(demo.wall(), [Probe("post_3", None, "damaged"), Prosthesis("post_3", 0.4)])[-1]
    assert st.attribute(m, "post_3", "condition") == "damaged"  # where the damage sits is not known


def test_prosthesis_at_the_end_keeps_the_start():
    m = run(demo.wall(), [Prosthesis("plate", 0.5, end="end")])[-1]
    assert sorted(st.neighbours(m, "plate.new")) == ["plate", "post_3"]
    assert st.connection_attribute(m, "plate.new", "post_3", "at")["plate.new"] == pytest.approx(0.4)
    assert st.attribute(m, "plate", "length") == pytest.approx(2.5)
    assert st.connection_attribute(m, "plate.new", "plate", "support") == ["plate", "plate.new"]


def test_mid_prosthesis_pieces():
    m = run(demo.wall(), [MidProsthesis("sill", [0.6, 1.2])])[-1]
    assert sorted(st.neighbours(m, "sill.a")) == ["post_1", "sill.new"]
    assert sorted(st.neighbours(m, "sill.b")) == ["post_2", "post_3", "sill.new"]
    assert st.attribute(m, "sill.new", "length") == pytest.approx(0.6)


def test_replacement_keeps_the_name_and_the_joints():
    model = demo.wall()
    m = run(model, [Replacement("rail_2")])[-1]
    assert st.attribute(m, "rail_2", "fabric") == "new"
    assert sorted(st.neighbours(m, "rail_2")) == sorted(st.neighbours(model, "rail_2"))
    assert all(st.connection_attribute(m, "rail_2", o, "state") == "secured" for o in st.neighbours(m, "rail_2"))


def test_collapse_closes_the_bay():
    m = run(demo.wall(), [CASES["collapse"]])[-1]
    assert not st.has_element(m, "post_3")
    assert st.has_connection(m, "sill.a", "sill.b")
    assert st.attribute(m, "sill.b", "offset") == pytest.approx([-1.2, 0.0, 0.0])
    assert st.attribute(m, "sill.a", "offset") == pytest.approx([0.0, 0.0, 0.0])


def test_bypass_runs_the_brace_through():
    m = run(demo.wall(), [CASES["bypass"]])[-1]
    assert not st.has_element(m, "rail_2")
    assert st.connection_attribute(m, "brace_2", "sill", "at") == {"brace_2": 2.25, "sill": 2.6}


def test_lowering_keeps_the_topology():
    model = demo.wall()
    m = run(model, [CASES["lowering"]])[-1]
    assert sorted(st.names(m)) == sorted(st.names(model))
    for n in st.names(m):
        assert sorted(st.neighbours(m, n)) == sorted(st.neighbours(model, n))
    assert st.attribute(m, "plate", "offset")[2] == pytest.approx(-0.2)
    assert st.attribute(m, "post_1", "length") == pytest.approx(2.0)
    assert st.attribute(m, "sill", "fabric") == "new"


def test_touched_and_retain():
    states = run(demo.wall(), [Retain("post_3", "monitor the foot")])
    assert touched(states) == ["post_3"]
    assert st.attribute(states[-1], "post_3", "notes") == ["monitor the foot"]


def test_approach_failure_names_the_step():
    with pytest.raises(InterventionError) as e:
        run(demo.wall(), [Prosthesis("post_3", 2.5)])
    assert "cannot be split" in str(e.value)


def test_nested_sequence_expands():
    program = [Sequence([Release("rail_1", "post_1"), Sequence([Release("rail_1", "post_2"), Withdraw("rail_1")])])]
    states = run(demo.wall(), program)
    assert len(states) == 4
