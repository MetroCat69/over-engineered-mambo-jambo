import json
import logging
from typing import Any,List,cast,Tuple
from predicate_types import UnaryOperator,BinaryOperator,GroupOperation,BinaryOperation,UnaryOperation,Operation,GroupOperator
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

UNARY_OPERATOR_VALUES: Tuple[UnaryOperator, ...] = ("isNone", "isNotNone")
BINARY_OPERATOR_VALUES: Tuple[BinaryOperator, ...] = ("eqTo", "notEqualTo", "isLessThan", "isGreaterThan")
GROUP_OPERATOR_VALUES: Tuple[GroupOperator, ...] = ("and", "or")


class Predicate:
    def __init__(self, feature: str, operation: Operation):
        self.feature = feature
        self.operation = operation

    @classmethod
    def from_json(cls, json_string: str) -> "Predicate":
        try:
            data = json.loads(json_string)
            return cls(data["feature"], data["operation"])
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid predicate JSON: {e}")
            raise ValueError("Invalid predicate JSON") from e

    def evaluate(self, root: object) -> bool:
        try:
            value = self._extract_feature_value(root, self.feature)
        except AttributeError as e:
            logger.error(f"Failed to extract feature '{self.feature}': {e}")
            return False
        return self._evaluate_operation(value, self.operation)

    def _extract_feature_value(self, root: object, feature: str) -> Any:
        if not feature:
            return root
        attrs = feature.strip(".").split(".")
        current = root
        for attr in attrs:
            if not attr or not attr[0].isalpha():
                raise AttributeError(f"Invalid attribute in path: {attr}")
            try:
                current = getattr(current, attr)
            except AttributeError:
                raise 
        return current

    
    def _evaluate_operation(self, value: Any, operation: Operation) -> bool:
        try:
            operator = operation["operator"]
            # using casting as type narrowing does not work with mypy in this case so we are casting
            if operation["operator"] in UNARY_OPERATOR_VALUES:
                operation = cast(UnaryOperation,operation)
                return self._eval_unary(operation["operator"], value)
            elif operation["operator"] in BINARY_OPERATOR_VALUES:
                operation = cast(BinaryOperation,operation)
                return self._eval_binary(operation["operator"], value,operation["operand"] )
            elif operator in GROUP_OPERATOR_VALUES:
                operation = cast(GroupOperation,operation)
                return self._eval_group(operation["operator"], value, operation["operations"])
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        except Exception as e:
            logger.error(f"Operation evaluation failed: {e}")
            return False

    @staticmethod
    def _eval_unary(operator: UnaryOperator, value: Any) -> bool:
        if operator == "isNone":
            return value is None
        elif operator == "isNotNone":
            return value is not None
        return False

    @staticmethod
    def _eval_binary(operator: BinaryOperator, value: Any, operand: Any) -> bool:
        if operator == "eqTo":
            return value == operand
        elif operator == "notEqualTo":
            return value != operand
        elif operator == "isLessThan":
            return value < operand
        elif operator == "isGreaterThan":
            return value > operand
        return False
    
    def _eval_group(self, operator: GroupOperator, value: Any, operations: List[Operation]) -> bool:
        results = [self._evaluate_operation(value, op) for op in operations]
        if operator == "and":
            return all(results)
        elif operator == "or":
            return any(results)
        return False
    


