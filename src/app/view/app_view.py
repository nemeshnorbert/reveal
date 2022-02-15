import bokeh.models
import bokeh.palettes
import datetime

import app.view.callbacks
import app.view.elements
import app.view.localizer


def _get_spectral_colors(count):
    assert count <= 12
    palettes = bokeh.palettes.Spectral
    return palettes[max(count, 3)][:count]


def _update_date_picker_element(element, value):
    if value is not None:
        element.value = value


def _update_multi_select_element(element, value):
    element.options = value
    element.value = value


class RevealAppView:
    def __init__(self, config):
        self._config = config
        self._localizer = None
        self._elements = None
        self._callbacks = None

    def setup(self, controller):
        self._controller = controller
        self._localizer = app.view.localizer.AppViewLocalizer(
            self._config["localizer"]["default_locale_name"],
            self._config["localizer"]["localizations"],
        )
        self._elements = app.view.elements.ViewElements(
            self._config["elements"]
        )
        self._elements.setup_elements(self._localizer)
        self._callbacks = app.view.callbacks.ViewCallbacksManager(
            self._elements, self._controller
        )
        self._callbacks.setup_callbacks()

    def _get_representation(self):
        return self._elements["root"]

    representation = property(_get_representation)

    def _set_source_data(self, name, value):
        source = self._elements[name]
        if not isinstance(source, bokeh.models.ColumnDataSource):
            message = (
                f"Element {name} is not a bokeh.models.ColumnDataSource object"
            )
            raise RuntimeError(message)
        if value is None or value.empty:
            data = self._elements.get_default_source_data(name)
        else:
            data = value
        source.data = data

    def get_date_range(self):
        return (
            self._elements["start_date_picker"].value,
            self._elements["end_date_picker"].value,
        )

    def get_categories(self):
        return self._elements["category_multi_select"].value

    def get_descriptions(self):
        return self._elements["description_multi_select"].value

    def get_data_files(self):
        return self._elements["data_file_multi_select"].value

    def get_card_numbers(self):
        return self._elements["card_number_multi_select"].value

    def get_currency(self):
        return self._elements["currency_select"].value

    def get_transactions_plot_mode(self):
        mode = self._elements["transactions_tab_plot_mode_selector"].value
        if mode == self._localizer.get_literal(
            "transactions_tab_mode_selector_incremental_option_title"
        ):
            return "incremental"
        elif mode == self._localizer.get_literal(
            "transactions_tab_mode_selector_cumulative_option_title"
        ):
            return "cumulative"
        else:
            message = "Unknown transactions_tab_plot_mode_selector mode"
            raise RuntimeError(message)

    def get_transactions_period(self):
        mode = self._elements["transactions_tab_period_selector"].value
        if mode == self._localizer.get_literal(
            "transactions_tab_period_selector_seconds_option_title"
        ):
            return "seconds"
        elif mode == self._localizer.get_literal(
            "transactions_tab_period_selector_days_option_title"
        ):
            return "days"
        elif mode == self._localizer.get_literal(
            "transactions_tab_period_selector_months_option_title"
        ):
            return "months"
        elif mode == self._localizer.get_literal(
            "transactions_tab_period_selector_years_option_title"
        ):
            return "years"
        else:
            message = "Unknown transactions_tab_period_selector mode"
            raise RuntimeError(message)

    def update_controls_values(self, values):
        self._callbacks.reset_controls_callbacks()
        _update_date_picker_element(
            element=self._elements["start_date_picker"],
            value=values["date_range"][0],
        )
        _update_date_picker_element(
            element=self._elements["end_date_picker"],
            value=values["date_range"][1],
        )
        _update_multi_select_element(
            element=self._elements["category_multi_select"],
            value=values["categories"],
        )
        _update_multi_select_element(
            element=self._elements["description_multi_select"],
            value=values["descriptions"],
        )
        _update_multi_select_element(
            element=self._elements["card_number_multi_select"],
            value=values["card_numbers"],
        )
        _update_multi_select_element(
            element=self._elements["data_file_multi_select"],
            value=values["data_files"],
        )
        self._callbacks.setup_controls_callbacks()

    def get_active_tab_id(self):
        return self._elements["tabs_group"].active

    def show_overview_income_text(self, income):
        self._setup_overview_text("overview_tab_income_text", income)

    def show_overview_spending_text(self, spending):
        self._setup_overview_text("overview_tab_spending_text", spending)

    def show_overview_disposable_income_text(self, disposable_income):
        self._setup_overview_text(
            "overview_tab_disposable_income_text", disposable_income
        )

    def _setup_overview_text(self, name, value):
        self._elements[name].text = f"{value:,.2f}"

    def show_overview_income(self, income):
        self._setup_overview_operations_source(
            figure_name="overview_income_figure",
            source_name="overview_income_source",
            operations=income,
        )

    def show_overview_spending(self, spending):
        self._setup_overview_operations_source(
            figure_name="overview_spending_figure",
            source_name="overview_spending_source",
            operations=spending,
        )

    def show_overview_cards(self, cards):
        if cards is not None and not cards.empty:
            cards.sort_values(by=["income", "spending"], inplace=True)
            figure = self._elements["overview_cards_figure"]
            figure.y_range.factors = list(cards["card_number"])
        self._set_source_data("overview_cards_source", cards)

    def _setup_overview_operations_source(
        self, figure_name, source_name, operations
    ):
        if operations is not None:
            operations["color"] = _get_spectral_colors(len(operations))
            operations.sort_values(
                by="operation_sum", inplace=True, ascending=False
            )
            figure = self._elements[figure_name]
            figure.x_range.factors = list(operations["category"])
        self._set_source_data(source_name, operations)

    def show_transactions(self, income, spending):
        start_dates = [datetime.datetime(year=2070, month=1, day=1)]
        end_dates = [datetime.datetime(year=1970, month=1, day=1)]
        if income is not None:
            income.sort_values(
                by="operation_date", inplace=True, ascending=True
            )
            if not income.empty:
                start_dates.append(income["operation_date"].iloc[0])
                end_dates.append(income["operation_date"].iloc[-1])
        if spending is not None:
            spending.sort_values(
                by="operation_date", inplace=True, ascending=True
            )
            if not spending.empty:
                start_dates.append(spending["operation_date"].iloc[0])
                end_dates.append(spending["operation_date"].iloc[-1])
        figure = self._elements["transactions_figure"]
        figure.x_range.start = min(start_dates)
        figure.x_range.end = max(end_dates)
        self._set_source_data("income_source", income)
        self._set_source_data("spending_source", spending)

    def show_operations_table(self, operations):
        self._set_source_data("operations_table_source", operations)

    def _show_status_message(self, message):
        self._elements["status_bar"].text = message

    def show_loading_status_message(self):
        self._show_status_message(
            self._localizer.get_literal("status_bar_loading_title")
        )

    def show_loading_exchange_rates_status_message(self):
        self._show_status_message(
            self._localizer.get_literal(
                "status_bar_loading_exchange_rates_title"
            )
        )

    def show_load_successful_status_message(self):
        self._show_status_message(
            self._localizer.get_literal("status_bar_load_successful_title")
        )
