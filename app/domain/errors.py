class DomainError(Exception):
    pass


class EmailAlreadyBlacklistedError(DomainError):
    pass
