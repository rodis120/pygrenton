
class FeatureNotGettableError(Exception):
    
    def __init__(self, name) -> None:
        message = f"Feature \"{name}\" is not gettable."
        super().__init__(message)


class FeatureNotSettableError(Exception):
    
    def __init__(self, name) -> None:
        message = f"Feature \"{name}\" is not settable."
        super().__init__(message)