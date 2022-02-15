import app.exceptions


class FilesLoader:
    def __init__(self):
        self._files = None
        self._file_names = None
        self._file_contents = None

    def get_file_names(self):
        return self._file_names

    def set_file_names(self, file_names):
        if self._file_names is not None and self._file_contents is not None:
            self._file_contents = None
            self._files = None
        self._file_names = file_names

    def get_file_contents(self):
        return self._file_contents

    def set_file_contents(self, file_contents):
        if self._file_names is not None and self._file_contents is not None:
            self._file_names = None
            self._files = None
        self._file_contents = file_contents

    def load(self):
        if self._file_names is not None and self._file_contents is not None:
            if self._files is None:
                self._files = dict(zip(self._file_names, self._file_contents))
            return self._files
        else:
            message = (
                "Trying to load data while file names "
                "and file contents are not set"
            )
            raise app.exceptions.LoadFilesError(message)
