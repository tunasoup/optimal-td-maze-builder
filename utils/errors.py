class Error(Exception):
    """Base class for exceptions"""
    pass


class ValidationError(Error):
    def __init__(self, message):
        self.message = message
