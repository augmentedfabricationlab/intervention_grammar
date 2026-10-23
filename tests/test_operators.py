import compas
import pytest

from intervention_grammar import Add
from intervention_grammar import AddFeature
from intervention_grammar import Close
from intervention_grammar import Cut
from intervention_grammar import Detach
from intervention_grammar import Double
from intervention_grammar import Ease
from intervention_grammar import Extend
from intervention_grammar import Fasten
from intervention_grammar import Fill
from intervention_grammar import Inlay
from intervention_grammar import Insert
from intervention_grammar import InterventionError
from intervention_grammar import Join
from intervention_grammar import Lengthen
from intervention_grammar import Lift
from intervention_grammar import Lower
from intervention_grammar import Machine
from intervention_grammar import Mirror
from intervention_grammar import Move
from intervention_grammar import Open
from intervention_grammar import OpenUp
from intervention_grammar import Orient
from intervention_grammar import Probe
from intervention_grammar import Prop
from intervention_grammar import Record
from intervention_grammar import Release
from intervention_grammar import Remove
from intervention_grammar import Reroute
from intervention_grammar import Seat
from intervention_grammar import Secure
from intervention_grammar import Select
from intervention_grammar import Shorten
from intervention_grammar import Split
from intervention_grammar import SplitNode
from intervention_grammar import Support
from intervention_grammar import Swap
from intervention_grammar import Tilt
from intervention_grammar import Trim
from intervention_grammar import Turn
from intervention_grammar import Unjoin
from intervention_grammar import Unprop
from intervention_grammar import Unseat
from intervention_grammar import Withdraw
from intervention_grammar import demo
from intervention_grammar import inverse
from intervention_grammar import run
from intervention_grammar import state as st

# attributes an exact inverse may leave different: the log, and what new wood replaced
SKIP = ("log", "fabric")


def same(a, b, skip=SKIP):
    return st.snapshot(a, skip) == st.snapshot(b, skip)


def undo(program, skip=SKIP):
    """Run a program and its inverse; the model must come back."""
    model = demo.wall()
    after = run(model, program)[-1]
    back = run(after, inverse(model, program))[-1]
    assert same(model, back, skip), (program, inverse(model, program))
    return after


# ==============================================================================
# State
# ==============================================================================


def test_state_defaults_and_edits():
    m = demo.wall()
    assert st.attribute(m, "post_1", "fabric") == "original"
    assert st.attribute(m, "post_1", "props") == []
    st.set_attribute(m, "post_1", "condition", "damaged")
    assert st.attributes(m, "post_1")["condition"] == "damaged"
    assert sorted(st.neighbours(m, "post_2")) == ["plate", "rail_1", "rail_2", "sill"]
    assert st.connection_attribute(m, "sill", "post_2", "at") == {"post_2": 0.0, "sill": 1.5}
    st.remove_connection(m, "rail_1", "post_2")
    assert not st.has_connection(m, "post_2", "rail_1")
    with pytest.raises(InterventionError):
        st.element(m, "post_9")
    with pytest.raises(InterventionError):
        st.add_element(m, "sill")


def test_attribute_values_are_copies():
    m = demo.wall()
    props = st.attribute(m, "post_1", "props")
    props.append(1.0)
    assert st.attribute(m, "post_1", "props") == []


def test_model_with_state_survives_json():
    m = run(demo.wall(), [Release("rail_1", "post_1"), Probe("post_3", 0.1, "damaged")])[-1]
    back = compas.json_loads(compas.json_dumps(m))
    assert same(m, back, skip=())
    assert back.graph.attributes["log"][1]["operation"] == "Probe"


# ==============================================================================
# Running
# ==============================================================================


def test_run_keeps_states_and_log_and_leaves_the_model():
    m = demo.wall()
    before = st.snapshot(m)
    states = run(m, [Release("rail_1", "post_1"), Release("rail_1", "post_2"), Withdraw("rail_1")])
    assert len(states) == 4
    assert st.snapshot(m) == before
    log = states[-1].graph.attributes["log"]
    assert [e["operation"] for e in log] == ["Release", "Release", "Withdraw"]
    assert st.attribute(states[-1], "rail_1", "log") == [1, 2, 3]
    assert st.attribute(states[-1], "post_1", "log") == [1]


def test_failing_step_names_step_and_reason():
    with pytest.raises(InterventionError) as e:
        run(demo.wall(), [Release("rail_1", "post_1"), Withdraw("rail_1")])
    assert "step 2" in str(e.value)
    assert "held by secured joints with post_2" in str(e.value)


def test_program_survives_json():
    program = [Split("post_3", 0.4, {"family": "half_lap", "length": 0.3}), Tilt("post_3.a", "post_3.b", 6.0), Record("note")]
    back = compas.json_loads(compas.json_dumps(program))
    assert [repr(op) for op in back] == [repr(op) for op in program]
    assert same(run(demo.wall(), program)[-1], run(demo.wall(), back)[-1])


# ==============================================================================
# Structure
# ==============================================================================


def test_split_distributes_connections_by_station():
    m = run(demo.wall(), [Split("post_3", 0.4, {"family": "half_lap"})])[-1]
    assert sorted(st.neighbours(m, "post_3.a")) == ["post_3.b", "sill"]
    assert sorted(st.neighbours(m, "post_3.b")) == ["plate", "post_3.a", "rail_2"]
    assert st.attribute(m, "post_3.b", "length") == pytest.approx(1.8)
    assert st.connection_attribute(m, "post_3.b", "rail_2", "at")["post_3.b"] == pytest.approx(0.7)
    assert st.connection_attribute(m, "post_3.a", "sill", "support") == ["post_3.a", "sill"]


def test_split_merge_are_inverse():
    undo([Split("post_3", 0.4, {"family": "half_lap"})])
    undo([Split("sill", 1.0, None, pieces=["sill.left", "sill"])])


def test_split_needs_stations_or_start():
    m = demo.wall()
    st.set_connection_attribute(m, "post_3", "rail_2", "at", {})
    with pytest.raises(InterventionError):
        run(m, [Split("post_3", 0.4)])
    after = run(m, [Split("post_3", 0.4, start=["sill"])])[-1]
    assert sorted(st.neighbours(after, "post_3.b")) == ["plate", "post_3.a", "rail_2"]


def test_split_outside_the_member_is_refused():
    with pytest.raises(InterventionError):
        run(demo.wall(), [Split("post_3", 2.5)])


def test_join_unjoin():
    m = undo([Join("post_1", "post_3", {"family": "tie"})])
    assert st.connection_attribute(m, "post_1", "post_3", "state") == "open"
    undo([Unjoin("rail_1", "post_1")])
    with pytest.raises(InterventionError):
        run(demo.wall(), [Join("rail_1", "post_1")])


def test_trim_extend_shift_stations_and_respect_joints():
    m = undo([Trim("plate", "end", 0.05)])
    assert st.attribute(m, "plate", "length") == pytest.approx(2.95)
    with pytest.raises(InterventionError):
        run(demo.wall(), [Trim("post_1", "end", 0.1)])  # the joint with the plate sits at the head
    m = undo([Extend("post_1", "start", 0.2)])
    assert st.connection_attribute(m, "post_1", "plate", "at")["post_1"] == pytest.approx(2.4)
    with pytest.raises(InterventionError):
        run(demo.wall(), [Trim("post_1", "start", 0.2)])  # the joint with the sill sits at the foot


def test_turn_needs_the_member_out_and_reverses_stations():
    with pytest.raises(InterventionError):
        run(demo.wall(), [Turn("rail_1")])
    out = [Release("rail_1", "post_1"), Release("rail_1", "post_2"), Withdraw("rail_1")]
    m = undo(out + [Turn("rail_1", "end")])
    assert st.connection_attribute(m, "rail_1", "post_1", "at")["rail_1"] == pytest.approx(1.4)
    assert st.attribute(m, "rail_1", "turn")["reversed"] is True
    undo(out + [Turn("rail_1", "axis", 1)])


def test_add_remove():
    m = undo([Add("strut_1", connections={"sill": {"joint": {"family": "notch"}}}, attributes={"type": "strut"})])
    assert st.attribute(m, "strut_1", "fabric") == "new"
    m = undo([Remove("brace_1")])
    assert not st.has_element(m, "brace_1")
    back = run(m, inverse(demo.wall(), [Remove("brace_1")]))[-1]
    assert st.attribute(back, "brace_1", "fabric") == "new"  # the shape comes back, the original wood does not


def test_add_like_copies_type_and_length():
    m = run(demo.wall(), [Add("post_4", like="post_3", placed=False)])[-1]
    assert st.attribute(m, "post_4", "type") == "post"
    assert st.attribute(m, "post_4", "length") == pytest.approx(2.2)
    assert st.attribute(m, "post_4", "placement") == "out"


def test_cut_inlay_restore_the_shape_in_new_wood():
    m = demo.wall()
    after = run(m, [Cut("sill", {"span": [1.8, 2.0], "face": "top"})])[-1]
    assert st.attribute(after, "sill", "cuts") == [{"span": [1.8, 2.0], "face": "top"}]
    (back,) = inverse(m, [Cut("sill", {"span": [1.8, 2.0], "face": "top"})])
    assert isinstance(back, Inlay)
    undo([Inlay("sill", "sill.patch", {"span": [1.8, 2.0]})])


def test_double_and_support():
    m = undo([Double("rail_1", span=[0.2, 1.2], joint={"family": "plank", "fasteners": [{"kind": "peg", "count": 4}]})])
    assert st.connection_attribute(m, "rail_1.double", "rail_1", "joint")["family"] == "plank"
    m = undo([Support("plate", at=2.2)])
    assert st.attribute(m, "plate.support", "grounded") is True


def test_reroute():
    m = undo([Reroute("brace_2", "rail_2", "sill", {"sill": 2.6})])
    assert st.has_connection(m, "brace_2", "sill")
    assert not st.has_connection(m, "brace_2", "rail_2")
    assert st.connection_attribute(m, "brace_2", "sill", "at") == {"brace_2": 1.15, "sill": 2.6}


def test_split_node_and_merge_nodes():
    m = demo.wall()
    for other in ("sill", "plate", "rail_1", "rail_2"):
        st.set_connection_attribute(m, "post_2", other, "node", "j2")
    after = run(m, [SplitNode("j2", [["post_2", "rail_1"], ["post_2", "rail_2"]], "j2_rails")])[-1]
    assert st.connection_attribute(after, "post_2", "rail_1", "node") == "j2_rails"
    back = run(after, inverse(m, [SplitNode("j2", [["post_2", "rail_1"], ["post_2", "rail_2"]], "j2_rails")]))[-1]
    assert same(m, back)


def test_move_is_held_by_secured_joints():
    with pytest.raises(InterventionError):
        run(demo.wall(), [Move(["post_3"], [0.0, 0.01, 0.0])])
    released = [Release("post_3", o) for o in ("sill", "plate", "rail_2")]
    m = undo(released + [Move(["post_3"], [0.0, 0.01, 0.0])])
    assert st.attribute(m, "post_3", "offset") == pytest.approx([0.0, 0.01, 0.0])
    assert st.element(m, "post_3").transformation.translation_vector[1] == pytest.approx(0.01)


def test_swap():
    out = []
    for m in ("rail_1", "rail_2"):
        out += [Release(m, o) for o in demo_neighbours(m)] + [Withdraw(m)]
    m = undo(out + [Swap("rail_1", "rail_2")])
    assert st.has_connection(m, "rail_1", "post_3")
    assert st.has_connection(m, "rail_2", "post_1")


def demo_neighbours(member):
    return st.neighbours(demo.wall(), member)


# ==============================================================================
# Joints
# ==============================================================================


def test_joint_operators_change_the_joint_and_undo():
    a, b = "rail_1", "post_2"
    m = undo([
        Select(a, b, {"family": "hooked_scarf", "length": 0.6}),
        Orient(a, b, 1),
        Tilt(a, b, 6.0),
        Tilt(a, b, 26.6, plane="undersquint"),
        Lengthen(a, b, 0.1),
        Shorten(a, b, 0.05),
        Mirror(a, b),
        AddFeature(a, b, "hook"),
        Fasten(a, b, "peg", 2),
        Detach(a, b),
        Open(a, b, "up"),
        Ease(a, b, 0.006),
    ])
    joint = st.connection_attribute(m, a, b, "joint")
    assert joint["family"] == "hooked_scarf"
    assert joint["length"] == pytest.approx(0.65)
    assert joint["tilt"] == pytest.approx(6.0)
    assert joint["tilt_undersquint"] == pytest.approx(26.6)
    assert joint["orientation"] == 1
    assert joint["mirrored"] is True
    assert joint["features"] == ["hook"]
    assert joint["fasteners"] == [{"kind": "peg", "count": 2}]
    assert joint["loose"] is True and joint["open"] == "up" and joint["ease"] == pytest.approx(0.006)


def test_lengthen_needs_a_length():
    with pytest.raises(InterventionError):
        run(demo.wall(), [Lengthen("rail_1", "post_2", 0.1)])


# ==============================================================================
# Process
# ==============================================================================


def test_release_secure_withdraw_insert_seat():
    m = undo([Release("rail_1", "post_1"), Release("rail_1", "post_2"), Withdraw("rail_1")])
    assert st.attribute(m, "rail_1", "placement") == "out"
    with pytest.raises(InterventionError):
        run(m, [Secure("rail_1", "post_1")])  # not in place
    m = run(m, [Insert("rail_1"), Seat("rail_1"), Secure("rail_1", "post_1")])[-1]
    assert st.connection_attribute(m, "rail_1", "post_1", "state") == "secured"
    undo([Release("rail_1", "post_1"), Release("rail_1", "post_2"), Unseat("rail_1")])


def test_lift_lower_prop_unprop():
    released = [Release(p, "sill") for p in ("post_1", "post_2", "post_3")]
    wall = ["post_1", "post_2", "post_3", "rail_1", "rail_2", "plate", "brace_1", "brace_2"]
    m = undo(released + [Prop("plate", 1.5), Lift(wall, 0.05)])
    assert st.attribute(m, "plate", "lift") == pytest.approx(0.05)
    assert st.attribute(m, "plate", "props") == [1.5]
    with pytest.raises(InterventionError):
        run(demo.wall(), [Lift(["post_1"], 0.05)])
    with pytest.raises(InterventionError):
        run(demo.wall(), released + [Lower(wall, 0.05)])
    with pytest.raises(InterventionError):
        run(demo.wall(), [Unprop("plate", 1.5)])


def test_machine_fill():
    m = undo([Machine("post_1", "end", {"family": "half_lap"})], skip=SKIP + ("fills",))
    assert st.attribute(m, "post_1", "ends") == {"end": {"family": "half_lap"}}
    m = run(m, [Fill("post_1", "end")])[-1]
    assert st.attribute(m, "post_1", "fills") == [{"end": "end", "joint": {"family": "half_lap"}}]
    with pytest.raises(InterventionError):
        run(m, [Fill("post_1", "end")])


# ==============================================================================
# Knowledge
# ==============================================================================


def test_knowledge():
    model = demo.wall()
    program = [Record("survey before any action"), Record("tenon split", "rail_1"), Probe("post_3", 0.1, "damaged"), OpenUp("rail_1")]
    m = run(model, program)[-1]
    assert m.graph.attributes["notes"] == ["survey before any action"]
    assert st.attribute(m, "rail_1", "notes") == ["tenon split"]
    assert st.attribute(m, "post_3", "condition") == "damaged"
    assert st.attribute(m, "rail_1", "exposed") is True
    assert [type(op).__name__ for op in inverse(model, program)] == ["Close"]
    with pytest.raises(InterventionError):
        run(m, [OpenUp("rail_1")])
    assert st.attribute(run(m, [Close("rail_1")])[-1], "rail_1", "exposed") is False
