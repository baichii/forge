class Error(Exception):
    """Error superclass."""


# Registration errors
class UnregisteredModule(Error):
    """Raised when the user requests a module from the registry that does not actually exist."""


class NamespaceNotFound(UnregisteredModule):
    """Raised when the user requests a module from the registry where the namespace doesn't exist."""


class NameNotFound(UnregisteredModule):
    """Raised when the user requests a module from the registry where the name doesn't exist."""


class VersionNotFound(UnregisteredModule):
    """Raised when the user requests a module from the registry where the version doesn't exist."""


class Deprecated(Error):
    """Raised when the user requests a module from the registry with an older version number than the latest module with the same name."""


class RegistrationError(Error):
    """Raised when the user attempts to register an invalid module. For example, an unversioned module when a versioned module exists."""
