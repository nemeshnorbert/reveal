import app.controller.app_controller
import app.model.app_model
import app.view.app_view


class RevealAppHandler:
    def __init__(self, config):
        self._config = config
        self._controller = None

    def __call__(self, document):
        if self._controller is None:
            self._setup()
        return self._controller(document)

    def _setup(self):
        self._controller = app.controller.app_controller.RevealAppController(
            model=app.model.app_model.RevealAppModel(self._config["model"]),
            view=app.view.app_view.RevealAppView(self._config["view"]),
            config=self._config["controller"],
        )
        self._controller.setup()
