class AppViewLocalizer:
    def __init__(self, locale_name, localizations):
        self._locale_name = locale_name
        self._localizations = localizations

    def get_literal(self, name):
        if name not in self._localizations["app_literals"]:
            raise RuntimeError(f"Cannot find {name} in application's locale")
        item = self._localizations["app_literals"][name]
        if self._locale_name not in item:
            raise RuntimeError(
                f"Cannot find {self._locale} locale for "
                "{name} in application's locale"
            )
        return item[self._locale_name]["value"]
