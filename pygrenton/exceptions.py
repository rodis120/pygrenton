
class FeatureNotGettableError(Exception):
    
    def __init__(self, name) -> None:
        message = f"Feature \"{name}\" is not gettable."
        super().__init__(message)

class FeatureNotSettableError(Exception):
    
    def __init__(self, name) -> None:
        message = f"Feature \"{name}\" is not settable."
        super().__init__(message)
        
class ConfigurationDownloadError(Exception):
    
    def __init__(self) -> None:
        super().__init__("Unable to download configuration.")
        
class ConfigurationParserError(Exception):
    
    def __init__(self) -> None:
        super().__init__("Unable to parse configuration.")