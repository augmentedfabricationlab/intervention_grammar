# Operators

Every operator is a class with `check`, `apply` and `inverse`. The operators
fall into four layers. Structure operators change what the finished structure
is. Joint operators change the shape of a connection. Process operators move
the structure through temporary states on the way. Knowledge operators change
what is known about it.

Members and connections are named by the names of their elements: a
connection is given by its two members `a` and `b`. Positions along a member
are stations, in metres from its start.

## Structure

What the finished structure is: its members, their connections, their lengths
and their positions.

| Operator | Parameters | What it does | Inverse |
|---|---|---|---|
| [`Cut`][intervention_grammar.structure_operators.Cut] | `member, region` | Cut material out of a member. | [`Inlay`][intervention_grammar.structure_operators.Inlay] |
| [`Inlay`][intervention_grammar.structure_operators.Inlay] | `member, piece, region, joint` | Fit a new piece into a member. | [`Remove`][intervention_grammar.structure_operators.Remove] of the piece |
| [`Split`][intervention_grammar.structure_operators.Split] | `member, at, joint, pieces, start` | Cut a member through at a station; the two pieces meet in a joint. | [`Merge`][intervention_grammar.structure_operators.Merge] |
| [`Join`][intervention_grammar.structure_operators.Join] | `a, b, joint, state, at, support` | Join two members with a joint. | [`Unjoin`][intervention_grammar.structure_operators.Unjoin] |
| [`Unjoin`][intervention_grammar.structure_operators.Unjoin] | `a, b` | Take away the connection between two members. | [`Join`][intervention_grammar.structure_operators.Join] |
| [`Merge`][intervention_grammar.structure_operators.Merge] | `a, b, into` | Make two connected pieces one member again. | [`Split`][intervention_grammar.structure_operators.Split] |
| [`Trim`][intervention_grammar.structure_operators.Trim] | `member, end, by` | Shorten a member at one end. | [`Extend`][intervention_grammar.structure_operators.Extend] |
| [`Extend`][intervention_grammar.structure_operators.Extend] | `member, end, by` | Lengthen a member at one end. | [`Trim`][intervention_grammar.structure_operators.Trim] |
| [`Turn`][intervention_grammar.structure_operators.Turn] | `member, mode, quarter` | Turn a member that is out: end for end, or about its own axis. | [`Turn`][intervention_grammar.structure_operators.Turn] in the opposite direction |
| [`Add`][intervention_grammar.structure_operators.Add] | `member, like, element, placed, connections, attributes` | Add a member to the structure. | [`Remove`][intervention_grammar.structure_operators.Remove] |
| [`Remove`][intervention_grammar.structure_operators.Remove] | `member` | Take a member out of the structure for good; its connections go with it. | [`Add`][intervention_grammar.structure_operators.Add] |
| [`Double`][intervention_grammar.structure_operators.Double] | `member, piece, face, span, joint` | Add a piece alongside a member, sharing its load path. | [`Remove`][intervention_grammar.structure_operators.Remove] of the piece |
| [`Support`][intervention_grammar.structure_operators.Support] | `member, at, support, kind` | Give a member a permanent support from the ground. | [`Remove`][intervention_grammar.structure_operators.Remove] of the support |
| [`Reroute`][intervention_grammar.structure_operators.Reroute] | `member, old, new, at, state` | Connect a member to another one instead. | [`Reroute`][intervention_grammar.structure_operators.Reroute] to the old member |
| [`SplitNode`][intervention_grammar.structure_operators.SplitNode] | `node, connections, new` | Let some connections of a crowded node meet in a node of their own. | [`MergeNodes`][intervention_grammar.structure_operators.MergeNodes] |
| [`MergeNodes`][intervention_grammar.structure_operators.MergeNodes] | `node, other` | Let the connections of two nodes meet in one. | [`SplitNode`][intervention_grammar.structure_operators.SplitNode] |
| [`Move`][intervention_grammar.structure_operators.Move] | `members, by` | Move members permanently. | [`Move`][intervention_grammar.structure_operators.Move] by the opposite vector |
| [`Swap`][intervention_grammar.structure_operators.Swap] | `a, b` | Two members that are out exchange their places in the structure. | [`Swap`][intervention_grammar.structure_operators.Swap] |

[`Remove`][intervention_grammar.structure_operators.Remove] is undone
geometrically: the member comes back in its shape, in new material. The same
holds for [`Cut`][intervention_grammar.structure_operators.Cut], which an
inlay undoes, and for [`Fill`][intervention_grammar.process_operators.Fill].
The share of original material that remains is measured with
[`original_share`][intervention_grammar.measures.original_share].

## Joint

The shape of a connection. Joints are plain dicts, a family name and its
parameters, for example `{"family": "lap", "length": 0.3}`. The grammar
stores and changes them and leaves the meaning of a family to the tools that
make or check the joint, so joints can come from any source.

| Operator | Parameters | What it does | Inverse |
|---|---|---|---|
| [`Select`][intervention_grammar.joint_operators.Select] | `a, b, joint` | Set the joint of a connection. | [`Select`][intervention_grammar.joint_operators.Select] with the previous joint |
| [`Orient`][intervention_grammar.joint_operators.Orient] | `a, b, turns` | Turn the joint about the member axis by quarter turns. | [`Orient`][intervention_grammar.joint_operators.Orient] by the opposite number of turns |
| [`Tilt`][intervention_grammar.joint_operators.Tilt] | `a, b, angle, plane` | Tilt a cutting plane of the joint by an angle. | [`Tilt`][intervention_grammar.joint_operators.Tilt] by the opposite angle |
| [`Lengthen`][intervention_grammar.joint_operators.Lengthen] | `a, b, by` | Make the joint longer. | [`Shorten`][intervention_grammar.joint_operators.Shorten] |
| [`Shorten`][intervention_grammar.joint_operators.Shorten] | `a, b, by` | Make the joint shorter. | [`Lengthen`][intervention_grammar.joint_operators.Lengthen] |
| [`Mirror`][intervention_grammar.joint_operators.Mirror] | `a, b` | Mirror the joint. | [`Mirror`][intervention_grammar.joint_operators.Mirror] |
| [`AddFeature`][intervention_grammar.joint_operators.AddFeature] | `a, b, feature` | Add a feature to the joint. | [`Select`][intervention_grammar.joint_operators.Select] with the joint as it was |
| [`Fasten`][intervention_grammar.joint_operators.Fasten] | `a, b, fastener, count` | Add fasteners to the joint. | [`Select`][intervention_grammar.joint_operators.Select] with the joint as it was |
| [`Detach`][intervention_grammar.joint_operators.Detach] | `a, b` | Make the connecting part of a joint a separate piece. | [`Select`][intervention_grammar.joint_operators.Select] with the joint as it was |
| [`Open`][intervention_grammar.joint_operators.Open] | `a, b, towards` | Open a joint on one side, so that a member can be inserted from that side. | [`Select`][intervention_grammar.joint_operators.Select] with the joint as it was |
| [`Ease`][intervention_grammar.joint_operators.Ease] | `a, b, play` | Give the joint a clearance for assembly. | [`Select`][intervention_grammar.joint_operators.Select] with the joint as it was |

## Process

The temporary states of an intervention: fastenings undone and made again,
members taken out and put back, the structure lifted and propped.

| Operator | Parameters | What it does | Inverse |
|---|---|---|---|
| [`Release`][intervention_grammar.process_operators.Release] | `a, b` | Release a connection: undo its fastening, the members stay in contact. | [`Secure`][intervention_grammar.process_operators.Secure] |
| [`Secure`][intervention_grammar.process_operators.Secure] | `a, b` | Fasten a connection. | [`Release`][intervention_grammar.process_operators.Release] |
| [`Withdraw`][intervention_grammar.process_operators.Withdraw] | `member, path` | Take a member out without destroying it, for reuse or turning. | [`Insert`][intervention_grammar.process_operators.Insert] |
| [`Insert`][intervention_grammar.process_operators.Insert] | `member, path` | Bring a member that is out into place along a path. | [`Withdraw`][intervention_grammar.process_operators.Withdraw] |
| [`Seat`][intervention_grammar.process_operators.Seat] | `member` | Press an inserted member fully home. | [`Unseat`][intervention_grammar.process_operators.Unseat] |
| [`Unseat`][intervention_grammar.process_operators.Unseat] | `member` | Loosen a seated member so it can be withdrawn. | [`Seat`][intervention_grammar.process_operators.Seat] |
| [`Lift`][intervention_grammar.process_operators.Lift] | `members, by` | Jack members up. | [`Lower`][intervention_grammar.process_operators.Lower] |
| [`Lower`][intervention_grammar.process_operators.Lower] | `members, by` | Lower jacked members back. | [`Lift`][intervention_grammar.process_operators.Lift] |
| [`Prop`][intervention_grammar.process_operators.Prop] | `member, at` | Put a temporary prop under a member. | [`Unprop`][intervention_grammar.process_operators.Unprop] |
| [`Unprop`][intervention_grammar.process_operators.Unprop] | `member, at` | Take a temporary prop away. | [`Prop`][intervention_grammar.process_operators.Prop] |
| [`Machine`][intervention_grammar.process_operators.Machine] | `member, end, joint` | Cut a joint into the end of a member. | [`Fill`][intervention_grammar.process_operators.Fill] |
| [`Fill`][intervention_grammar.process_operators.Fill] | `member, end` | Fill a machined end with new material: the shape comes back, the original material does not. | [`Machine`][intervention_grammar.process_operators.Machine] |

## Knowledge

What is known about the structure. Record and Probe add knowledge and have no
inverse.

| Operator | Parameters | What it does | Inverse |
|---|---|---|---|
| [`Record`][intervention_grammar.knowledge_operators.Record] | `text, member` | Record something about a member, or about the structure. | none |
| [`Probe`][intervention_grammar.knowledge_operators.Probe] | `member, at, finding` | Inspect a member at a station. | none |
| [`OpenUp`][intervention_grammar.knowledge_operators.OpenUp] | `member, what` | Remove a covering to expose a member and its connections. | [`Close`][intervention_grammar.knowledge_operators.Close] |
| [`Close`][intervention_grammar.knowledge_operators.Close] | `member, what` | Cover an opened member again. | [`OpenUp`][intervention_grammar.knowledge_operators.OpenUp] |
