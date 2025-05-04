from types import SimpleNamespace
from dataclasses import dataclass
from predicate import Predicate


def test_example_simple_namespace():
    """Tests the first example from the task description with SimpleNamespace."""
    j_str = """{"feature": ".x.y", "operation": {"operator": "eqTo", "operand": 5}}"""
    predicate = Predicate.from_json(j_str)

    ns1 = SimpleNamespace(x=SimpleNamespace(y=5))
    ns2 = SimpleNamespace(x=SimpleNamespace(y=3))
    ns3 = SimpleNamespace(z=SimpleNamespace(y=5))

    assert predicate.evaluate(ns1)
    assert not predicate.evaluate(ns2)
    assert not predicate.evaluate(ns3)


def test_example_dataclass():
    """Tests the second example from the task description rompt with dataclasses."""

    @dataclass
    class User:
        name: str
        level: int

    @dataclass
    class Game:
        user: User

    g = Game(user=User(name="bob", level=6))

    pred_str1 = """{"feature": ".user.name", "operation": {"operator": "eqTo", "operand": "bob"}}"""
    pred1 = Predicate.from_json(pred_str1)

    # Feature path is misspelled (.users.level instead of .user.level) - should fail extraction
    pred_str2 = """{"feature": ".users.level", "operation": {"operator": "isLessThan", "operand": 3.6}}"""
    pred2 = Predicate.from_json(pred_str2)

    assert pred1.evaluate(g)
    assert not pred2.evaluate(g)  # Expect False because .users.level does not exist


def test_feature_empty_string_evaluates_root():
    """Tests that an empty feature string evaluates the root object itself."""
    root_obj = 1
    predicate_none = Predicate.from_json(
        '{"feature": "", "operation": {"operator": "isNone"}}'
    )
    predicate_not_none = Predicate.from_json(
        '{"feature": "", "operation": {"operator": "isNotNone"}}'
    )
    predicate_eq = Predicate.from_json(
        '{"feature": "", "operation": {"operator": "eqTo", "operand": 1}}'
    )

    assert not predicate_none.evaluate(root_obj)
    assert predicate_not_none.evaluate(root_obj)
    assert predicate_eq.evaluate(root_obj)

    assert predicate_none.evaluate(None)
    assert not predicate_not_none.evaluate(None)
    assert not predicate_eq.evaluate(None)
