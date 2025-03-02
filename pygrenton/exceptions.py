"""Exceptions raised by pygranton library."""

class FeatureNotGettableError(Exception):

    def __init__(self, name: str) -> None:
        """Init the exception."""
        super().__init__(f'Feature "{name}" is not gettable.')

class FeatureNotSettableError(Exception):

    def __init__(self, name: str) -> None:
        """Init the exception."""
        super().__init__(f'Feature "{name}" is not settable.')

class ConfigurationDownloadError(Exception):

    def __init__(self) -> None:
        """Init the exception."""
        super().__init__("Unable to download configuration.")

class ConfigurationParserError(Exception):

    def __init__(self) -> None:
        """Init the exception."""
        super().__init__("Unable to parse configuration.")

class InvalidUpdateMessageError(Exception):

    def __init__(self) -> None:
        """Init the exception."""
        super().__init__("Received an invalid update message.")

class InvalidLuaResponseError(Exception):

    def __init__(self, response: str) -> None:
        """Init the exception."""
        super().__init__(f"Invalid Lua response: {response}")
