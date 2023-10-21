class ServiceException(Exception):
    """Base class for all service exceptions"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class NotFoundError(ServiceException):
    def __init__(self, message: str):
        super().__init__(status_code=404, message=message)


class BadRequestError(ServiceException):
    def __init__(self, message: str):
        super().__init__(status_code=400, message=message)
