import base64
import io

import app.controller.loader
import app.exceptions


class RevealAppController:
    def __init__(self, model, view, config):
        self._config = config
        self._model = model
        self._view = view
        self._loader = None

    def setup(self):
        self._loader = app.controller.loader.FilesLoader()
        self._view.setup(controller=self)
        self._model.setup()

    def __call__(self, document):
        document.add_root(self._view.representation)

    def on_upload_files(self, attr, old, new):
        del attr
        del old
        self._loader.set_file_contents(
            [io.BytesIO(base64.b64decode(content)) for content in new]
        )

    def on_set_file_names(self, attr, old, new):
        del attr
        del old
        self._view.show_loading_status_message()
        self._loader.set_file_names(new)
        self._init_operations(self._loader.load())

    def on_load_example_click(self):
        self._view.show_loading_status_message()
        path = self._config["example_path"]
        self._loader.set_file_names([path])
        with open(path, "rb") as file_:
            self._loader.set_file_contents([io.BytesIO(file_.read())])
        self._init_operations(self._loader.load())

    def on_tab_change(self, attr, old, new):
        del attr
        del old
        self._show_active_tab(new)

    def on_transactions_tab_plot_settings_change(self, attr, old, new):
        del attr
        del old
        del new
        self._show_transactions_tab()

    def on_control_change(self, attr, old, new):
        del attr
        del old
        del new
        self._show_active_tab(self._view.get_active_tab_id())

    def _show_active_tab(self, tab_id):
        dispatchers = [
            self._show_overview_tab,
            self._show_transactions_tab,
            self._show_operations_tab,
            self._show_help_tab,
        ]
        callback = dispatchers[tab_id]
        callback()

    def _show_overview_tab(self):
        overview = self._model.report_overview(
            constraints=self._collect_report_constraints(),
            settings=self._collect_report_settings(),
        )
        self._view.show_overview_income_text(overview["income_total"])
        self._view.show_overview_spending_text(overview["spending_total"])
        self._view.show_overview_disposable_income_text(
            overview["disposable_income_total"]
        )
        self._view.show_overview_income(overview["income"])
        self._view.show_overview_spending(overview["spending"])
        self._view.show_overview_cards(overview["cards"])

    def _show_transactions_tab(self):
        transactions_report = self._model.report_transactions(
            constraints=self._collect_report_constraints(),
            settings=self._collect_report_settings(),
        )
        self._view.show_transactions(
            income=transactions_report["income"],
            spending=transactions_report["spending"],
        )

    def _show_operations_tab(self):
        operations = self._model.report_operations(
            constraints=self._collect_report_constraints(),
            settings=self._collect_report_settings(),
        )
        self._view.show_operations_table(operations["table"])

    def _show_help_tab(self):
        pass

    def _collect_report_constraints(self):
        return [
            {
                "date_range": self._view.get_date_range(),
                "card_numbers": self._view.get_card_numbers(),
                "categories": self._view.get_categories(),
                "descriptions": self._view.get_descriptions(),
                "data_files": self._view.get_data_files(),
            }
        ]

    def _collect_report_settings(self):
        return {
            "transactions_report_type": self._view.get_transactions_plot_mode(),
            "transactions_period": self._view.get_transactions_period(),
            "currency": self._view.get_currency(),
        }

    def _init_operations(self, files):
        self._view.show_loading_exchange_rates_status_message()
        try:
            self._model.init_operations(files)
        except (
            app.exceptions.ReadOperationsError,
            app.exceptions.ConvertOperationsError,
        ) as error:
            self._view.show_status_message(error.message)
            raise error
        else:
            constraints = None
            settings = self._collect_report_settings()
            self._view.update_controls_values(
                self._model.report_operations_stats(constraints, settings)
            )
            self._view.show_load_successful_status_message()
            self._show_active_tab(self._view.get_active_tab_id())
