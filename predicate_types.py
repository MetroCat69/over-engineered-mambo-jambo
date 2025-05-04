from typing import Literal, Union, TypedDict, List,Any


UnaryOperator = Literal["isNone", "isNotNone"]
BinaryOperator = Literal["eqTo", "notEqualTo", "isLessThan", "isGreaterThan"]
GroupOperator = Literal["and", "or"]

Operator = Union[UnaryOperator, BinaryOperator, GroupOperator]

class UnaryOperation(TypedDict):
    operator: UnaryOperator

class BinaryOperation(TypedDict):
    operator: BinaryOperator
    operand: Any

class GroupOperation(TypedDict):
    operator: GroupOperator
    operations: List["Operation"]  

Operation = Union[UnaryOperation, BinaryOperation, GroupOperation]
