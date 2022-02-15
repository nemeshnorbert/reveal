class RevealAppError(Exception):
    pass


class ConvertOperationsError(RevealAppError):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)


class ReadOperationsError(RevealAppError):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)


class LoadFilesError(RevealAppError):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)
