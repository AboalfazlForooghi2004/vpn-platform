class DomainError(Exception):
    """Base class for domain rule violations."""


class InvalidTransition(DomainError):
    """Raised when a state machine transition is not allowed."""


class LedgerInvariantError(DomainError):
    """Raised when a ledger transaction is not balanced or valid."""


class InvalidAwgConfiguration(DomainError):
    """Raised when an AWG profile or peer config is invalid."""
