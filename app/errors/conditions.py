class ConditionEvaluationError(Exception):
    pass


class StateVariableNotFoundError(ConditionEvaluationError):
    pass
