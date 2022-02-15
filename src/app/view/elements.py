import collections
import datetime
import math

import bokeh.layouts
import bokeh.models
import bokeh.palettes
import bokeh.plotting


class ViewElements:
    def __init__(self, config):
        self._default_source_data = {}
        self._config = config
        self._localizer = None
        self._root = None

    def setup_elements(self, localizer):
        self._localizer = localizer
        self._root = self._build_root(self._config["root"])

    def get_default_source_data(self, name):
        if name not in self._default_source_data:
            raise RuntimeError(f"Default data is not set for source {name}")
        return self._default_source_data[name]

    def __getitem__(self, name):
        elements = list(self._root.select(dict(name=name)))
        if len(elements) == 0:
            raise RuntimeError(
                f"View object does not contain model with name {name}"
            )
        if len(elements) != 1:
            raise RuntimeError(
                f"View object has more than one model with name {name}"
            )
        return elements[0]

    def _build_root(self, config):
        return bokeh.layouts.column(
            self._build_header(config["header"]),
            bokeh.layouts.row(
                self._build_controls_group(config["controls_group"]),
                self._build_tabs_group(config["tabs_group"]),
                width_policy="max",
                height_policy="max",
            ),
            width_policy="max",
            height_policy="max",
            name="root",
        )

    def _build_header(self, config):
        return bokeh.models.Paragraph(
            text=self._localizer.get_literal("header_control_title"),
            width_policy="max",
            # # height_policy="max",
            style={"font-weight": "bold"},
            name="header",
        )

    # region: tabs group

    def _build_tabs_group(self, config):
        return bokeh.models.Tabs(
            tabs=[
                self._build_overview_tab(config["overview_tab"]),
                self._build_transactions_tab(config["transactions_tab"]),
                self._build_operations_table_tab(config["table_tab"]),
                self._build_help_tab(config["help_tab"]),
            ],
            name="tabs_group",
            width_policy="max",
            height_policy="max",
        )

    def _build_overview_tab(self, config):
        return bokeh.models.Panel(
            child=bokeh.layouts.column(
                self._build_overview_headline_group(config["headline"]),
                self._build_overview_plot(config["plot"]),
                width_policy="max",
                height_policy="max",
            ),
            title=self._localizer.get_literal("overview_tab_title"),
            name="overview_tab",
        )

    def _build_overview_headline_group(self, config):
        return bokeh.layouts.row(
            self._build_overview_income_headline(config["income"]),
            self._build_width_spacer(),
            self._build_width_spacer(),
            self._build_overview_spending_headline(config["spending"]),
            self._build_width_spacer(),
            self._build_width_spacer(),
            self._build_overview_disposable_income_headline(
                config["disposable_income"]
            ),
            self._build_width_spacer(),
            self._build_width_spacer(),
            width_policy="max",
        )

    def _build_overview_income_headline(self, config):
        return self._build_overview_headline(
            title=self._localizer.get_literal(
                "overview_tab_income_headline_title"
            ),
            text="0",
            name="overview_tab_income_text",
        )

    def _build_overview_spending_headline(self, config):
        return self._build_overview_headline(
            title=self._localizer.get_literal(
                "overview_tab_spending_headline_title"
            ),
            text="0",
            name="overview_tab_spending_text",
        )

    def _build_overview_disposable_income_headline(self, config):
        return self._build_overview_headline(
            title=self._localizer.get_literal(
                "overview_tab_disposable_income_headline_title"
            ),
            text="0",
            name="overview_tab_disposable_income_text",
        )

    def _build_overview_headline(self, title, text, name):
        return bokeh.layouts.row(
            bokeh.models.Div(
                text=title,
                style={"font-size": "200%"},
                # width_policy="max",
            ),
            bokeh.models.Div(
                text=text,
                style={"font-size": "200%"},
                # width_policy="max",
                name=name,
            ),
            # width_policy="max",
        )

    def _build_overview_plot(self, config):
        return bokeh.layouts.column(
            bokeh.layouts.row(
                self._build_overview_income_figure(config["income"]),
                self._build_overview_spending_figure(config["spending"]),
                width_policy="max",
                height_policy="max",
            ),
            self._build_overview_cards_figure(
                config=config["cards"],
                source=self._build_overview_cards_transactions_source(
                    name="overview_cards_source"
                ),
            ),
            name="overview_plot",
            width_policy="max",
            height_policy="max",
        )

    def _build_overview_income_figure(self, config):
        return self._build_overview_operations_figure(
            config=config,
            title=self._localizer.get_literal("overview_tab_income_plot_title"),
            source=self._build_overview_operations_source(
                name="overview_income_source"
            ),
            figure_name="overview_income_figure",
            vbars_name="overview_income_vbars",
        )

    def _build_overview_spending_figure(self, config):
        return self._build_overview_operations_figure(
            config=config,
            title=self._localizer.get_literal(
                "overview_tab_spending_plot_title"
            ),
            source=self._build_overview_operations_source(
                name="overview_spending_source"
            ),
            figure_name="overview_spending_figure",
            vbars_name="overview_spending_vbars",
        )

    def _build_overview_operations_figure(
        self, config, title, source, figure_name, vbars_name
    ):
        figure = bokeh.plotting.figure(
            title=title,
            tools=[],
            x_range=source.data["category"],
            name=figure_name,
            width_policy="max",
            height_policy="max",
        )
        figure.vbar(
            x="category",
            top="operation_sum",
            color="color",
            width=0.9,
            source=source,
            name=vbars_name,
        )
        figure.add_tools(
            bokeh.models.SaveTool(),
            bokeh.models.HoverTool(
                tooltips="@category: @operation_sum{0,0.00}"
            ),
        )
        figure.toolbar.logo = None
        figure.xaxis.minor_tick_line_color = None
        figure.xaxis.major_tick_line_color = None
        figure.xaxis.major_label_orientation = math.pi / 4

        figure.yaxis.minor_tick_line_color = None
        figure.yaxis.major_tick_line_color = None
        figure.yaxis.formatter = bokeh.models.NumeralTickFormatter(format="0,0")

        figure.y_range.start = 0

        figure.xgrid.grid_line_color = None

        return figure

    def _build_overview_operations_source(self, name):
        return bokeh.models.ColumnDataSource(
            data=self._build_overview_operations_source_default_data(name),
            name=name,
        )

    def _build_overview_operations_source_default_data(self, name):
        if name not in self._default_source_data:
            self._default_source_data[name] = dict(
                color=[], category=[], operation_sum=[]
            )
        return self._default_source_data[name]

    def _build_overview_cards_figure(self, config, source):
        figure = bokeh.plotting.figure(
            y_range=bokeh.models.FactorRange(
                factors=source.data["card_number"]
            ),
            title=self._localizer.get_literal("overview_tab_cards_plot_title"),
            tools=[],
            name="overview_cards_figure",
            width_policy="max",
            height_policy="max",
        )
        income_renderer = figure.hbar(
            y=bokeh.transform.dodge("card_number", -0.1, range=figure.y_range),
            right="income",
            source=source,
            height=0.1,
            color=bokeh.palettes.Blues[3][0],
            legend_label=self._localizer.get_literal(
                "overview_tab_cards_plot_income_label_title"
            ),
            name="overview_cards_income_bars",
        )
        spending_renderer = figure.hbar(
            y=bokeh.transform.dodge("card_number", 0.1, range=figure.y_range),
            right="spending",
            source=source,
            height=0.1,
            color=bokeh.palettes.OrRd[3][0],
            legend_label=self._localizer.get_literal(
                "overview_tab_cards_plot_spending_label_title"
            ),
            name="overview_cards_spending_bars",
        )
        tooltip_comment = self._localizer.get_literal(
            "overview_tab_cards_plot_tooltip_comment"
        )
        figure.add_tools(
            bokeh.models.SaveTool(),
            bokeh.models.HoverTool(
                tooltips=tooltip_comment + ": @income{0,0.00}",
                renderers=[income_renderer],
            ),
            bokeh.models.HoverTool(
                tooltips=tooltip_comment + ": @spending{0,0.00}",
                renderers=[spending_renderer],
            ),
        )
        figure.toolbar.logo = None

        figure.legend.location = "bottom_right"
        figure.legend.click_policy = "hide"

        figure.xaxis.minor_tick_line_color = None
        figure.xaxis.formatter = bokeh.models.NumeralTickFormatter(format="0,0")

        figure.yaxis.minor_tick_line_color = None
        figure.yaxis.major_tick_line_color = None

        figure.ygrid.grid_line_color = None

        figure.y_range.range_padding = 0.1

        figure.outline_line_color = None
        return figure

    def _build_overview_cards_transactions_source(self, name):
        return bokeh.models.ColumnDataSource(
            data=self._build_overview_cards_transactions_data(name), name=name
        )

    def _build_overview_cards_transactions_data(self, name):
        if name not in self._default_source_data:
            self._default_source_data[name] = dict(
                card_number=[], income=[], spending=[]
            )
        return self._default_source_data[name]

    def _build_transactions_tab(self, config):
        return bokeh.models.Panel(
            child=bokeh.layouts.column(
                self._build_transactions_plot(config["plot"]),
                width_policy="max",
                height_policy="max",
            ),
            title=self._localizer.get_literal("transactions_tab_title"),
            name="transactions_tab",
        )

    def _build_transactions_plot(self, config):
        SourceVisualizationInfo = collections.namedtuple(
            "SourceInfo",
            ["source", "circles_name", "lines_name", "label", "color"],
        )
        sources_info = [
            SourceVisualizationInfo(
                source=self._build_transactions_source(name="income_source"),
                circles_name="income_circles",
                lines_name="income_lines",
                label=self._localizer.get_literal(
                    "transactions_tab_plot_income_label"
                ),
                color=bokeh.palettes.Blues[3][0],
            ),
            SourceVisualizationInfo(
                source=self._build_transactions_source(name="spending_source"),
                circles_name="spending_circles",
                lines_name="spending_lines",
                label=self._localizer.get_literal(
                    "transactions_tab_plot_spending_label"
                ),
                color=bokeh.palettes.OrRd[3][0],
            ),
        ]
        return bokeh.layouts.column(
            bokeh.layouts.row(
                self._build_transactions_plot_mode_selector(
                    config["plot_mode_selector"]
                ),
                self._build_transactions_plot_period_selector(
                    config["period_selector"]
                ),
                name="transactions_tab_controls",
            ),
            self._build_transactions_figure(config, sources_info),
            name="transactions_plot",
            width_policy="max",
            height_policy="max",
        )

    def _build_transactions_plot_mode_selector(self, config):
        incremental_option_title = self._localizer.get_literal(
            "transactions_tab_mode_selector_incremental_option_title"
        )
        cumulative_option_title = self._localizer.get_literal(
            "transactions_tab_mode_selector_cumulative_option_title"
        )

        return bokeh.models.Select(
            title=self._localizer.get_literal(
                "transactions_tab_mode_selector_title"
            ),
            value=incremental_option_title,
            options=[incremental_option_title, cumulative_option_title],
            name="transactions_tab_plot_mode_selector",
        )

    def _build_transactions_plot_period_selector(self, config):
        seconds_option_title = self._localizer.get_literal(
            "transactions_tab_period_selector_seconds_option_title"
        )
        days_option_title = self._localizer.get_literal(
            "transactions_tab_period_selector_days_option_title"
        )
        months_option_title = self._localizer.get_literal(
            "transactions_tab_period_selector_months_option_title"
        )
        years_option_title = self._localizer.get_literal(
            "transactions_tab_period_selector_years_option_title"
        )
        return bokeh.models.Select(
            title=self._localizer.get_literal(
                "transactions_tab_period_selector_title"
            ),
            value=seconds_option_title,
            options=[
                seconds_option_title,
                days_option_title,
                months_option_title,
                years_option_title,
            ],
            name="transactions_tab_period_selector",
        )

    def _build_transactions_figure(self, config, sources_info):
        figure = bokeh.plotting.figure(
            x_axis_type="datetime",
            title=self._localizer.get_literal("transactions_tab_plot_title"),
            tools=[],
            name="transactions_figure",
            width_policy="max",
            height_policy="max",
        )
        for source_info in sources_info:
            figure.circle(
                x="operation_date",
                y="operation_sum",
                size=4,
                color=source_info.color,
                source=source_info.source,
                legend_label=source_info.label,
                name=source_info.circles_name,
            )
            figure.line(
                x="operation_date",
                y="operation_sum",
                color=source_info.color,
                source=source_info.source,
                legend_label=source_info.label,
                name=source_info.lines_name,
            )
        tooltips = [
            (
                self._localizer.get_literal(
                    f"transactions_tab_plot_tooltip_{name}_title"
                ),
                formatter,
            )
            for name, formatter in [
                ("total", "@operation_sum{0,0.00}"),
                ("date", "@operation_date{%F}"),
                ("data_file", "@data_file"),
                ("category", "@category"),
                ("description", "@description"),
            ]
        ]
        figure.add_tools(
            bokeh.models.BoxZoomTool(),
            bokeh.models.WheelZoomTool(),
            bokeh.models.SaveTool(),
            bokeh.models.ResetTool(),
            bokeh.models.HoverTool(
                tooltips=tooltips,
                formatters={"@operation_date": "datetime"},
            ),
        )
        figure.toolbar.logo = None
        figure.legend.location = "top_left"
        figure.legend.click_policy = "hide"

        figure.xaxis.axis_label = None
        figure.xaxis.axis_label_standoff = 300
        figure.xaxis.formatter = bokeh.models.DatetimeTickFormatter(
            days="%b-%d", months="%Y-%b-%d", hours="%H:%M", minutes="%H:%M:%S"
        )

        figure.yaxis.axis_label = None
        figure.yaxis.axis_label_standoff = 300
        figure.yaxis.formatter = bokeh.models.NumeralTickFormatter(format="0,0")

        figure.grid.visible = False
        return figure

    def _build_transactions_source(self, name):
        return bokeh.models.ColumnDataSource(
            data=self._build_transactions_source_default_data(name), name=name
        )

    def _build_transactions_source_default_data(self, name):
        if name not in self._default_source_data:
            self._default_source_data[name] = dict(
                operation_date=[],
                operation_sum=[],
                data_file=[],
                category=[],
                description=[],
            )
        return self._default_source_data[name]

    def _build_operations_table_tab(self, config):
        return bokeh.models.Panel(
            child=bokeh.layouts.column(
                self._build_operations_table(config["operations_table"]),
                width_policy="max",
                height_policy="max",
            ),
            title=self._localizer.get_literal("table_tab_title"),
            name="operations_table_tab",
        )

    def _build_operations_table(self, config):
        formatters = {
            "object": bokeh.models.widgets.StringFormatter(),
            "string": bokeh.models.widgets.StringFormatter(),
            "int": bokeh.models.widgets.NumberFormatter(),
            "int8": bokeh.models.widgets.NumberFormatter(),
            "int16": bokeh.models.widgets.NumberFormatter(),
            "int32": bokeh.models.widgets.NumberFormatter(),
            "int64": bokeh.models.widgets.NumberFormatter(),
            "Int": bokeh.models.widgets.NumberFormatter(),
            "Int8": bokeh.models.widgets.NumberFormatter(),
            "Int16": bokeh.models.widgets.NumberFormatter(),
            "Int32": bokeh.models.widgets.NumberFormatter(),
            "Int64": bokeh.models.widgets.NumberFormatter(),
            "float16": bokeh.models.widgets.NumberFormatter(),
            "float32": bokeh.models.widgets.NumberFormatter(),
            "float64": bokeh.models.widgets.NumberFormatter(),
            "float128": bokeh.models.widgets.NumberFormatter(),
            "datetime64[ns]": bokeh.models.widgets.DateFormatter(),
            "datetime64[ns, UTC]": bokeh.models.widgets.DateFormatter(),
        }
        titles = {}
        for info in config["columns"]:
            name = info["name"]
            titles[name] = self._localizer.get_literal(f"{name}_field_title")
        columns = [
            bokeh.models.TableColumn(
                field=info["field"],
                title=titles[info["name"]],
                formatter=formatters[info["data_type"]],
            )
            for info in config["columns"]
        ]
        return bokeh.models.widgets.DataTable(
            source=self._build_operations_table_source(
                fields=[info["field"] for info in config["columns"]]
            ),
            columns=columns,
            width_policy="max",
            height_policy="max",
            name="operations_table",
        )

    def _build_operations_table_source(self, fields):
        return bokeh.models.ColumnDataSource(
            data=self._build_operations_table_source_default_data(fields),
            name="operations_table_source",
        )

    def _build_operations_table_source_default_data(self, fields):
        name = "operations_table_source"
        if name not in self._default_source_data:
            self._default_source_data[name] = {field: [] for field in fields}
        return self._default_source_data[name]

    def _build_help_tab(self, config):
        return bokeh.models.Panel(
            child=bokeh.layouts.column(
                bokeh.models.Div(
                    text=self._localizer.get_literal("help_tab_description"),
                    width_policy="max",
                    height_policy="max",
                ),
                self._build_help_table(config["help_table"]),
                bokeh.layouts.row(
                    self._build_width_spacer(),
                    self._build_width_spacer(),
                    self._build_width_spacer(),
                    self._build_width_spacer(),
                    self._build_width_spacer(),
                    self._build_example_button(config["example_button"]),
                    width_policy="max",
                    # # # height_policy="max",
                ),
                width_policy="max",
                height_policy="max",
            ),
            title=self._localizer.get_literal("help_tab_title"),
            name="help_tab",
        )

    def _build_help_table(self, config):
        columns = [
            bokeh.models.TableColumn(
                field="field",
                title=self._localizer.get_literal(
                    "help_tab_table_field_field_title"
                ),
            ),
            bokeh.models.TableColumn(
                field="data_type",
                title=self._localizer.get_literal(
                    "help_tab_table_data_type_field_title"
                ),
            ),
            bokeh.models.TableColumn(
                field="value_required",
                title=self._localizer.get_literal(
                    "help_tab_table_value_required_field_title"
                ),
            ),
        ]
        return bokeh.models.DataTable(
            source=self._build_help_table_source(
                "help_table_source", config["columns"]
            ),
            columns=columns,
            width_policy="max",
            # # height_policy="max",
            name="help_table",
        )

    def _build_help_table_source(self, name, columns_info):
        return bokeh.models.ColumnDataSource(
            data=self._build_help_table_data(name, columns_info), name=name
        )

    def _build_help_table_data(self, name, columns_info):
        if name not in self._default_source_data:
            source_data = dict(field=[], data_type=[], value_required=[])
            source_field_names = ["field", "data_type", "value_required"]
            for column_info in columns_info:
                for source_field_name in source_field_names:
                    source_data[source_field_name].append(
                        column_info[source_field_name]
                    )
            self._default_source_data[name] = source_data
        return self._default_source_data[name]

    # endregion: tabs group

    # region: main controls group

    def _build_controls_group(self, config):
        return bokeh.layouts.column(
            bokeh.models.Div(
                text=self._localizer.get_literal("filters_group_title"),
                style={"font-size": "200%"},
            ),
            self._build_filters_group(config["filters_group"]),
            bokeh.models.Div(
                text=self._localizer.get_literal("settings_group_title"),
                style={"font-size": "200%"},
            ),
            self._build_settings_group(config["settings_group"]),
            self._build_height_spacer(),
            bokeh.models.Div(
                text=self._localizer.get_literal("upload_group_title"),
                style={"font-size": "200%"},
            ),
            self._build_upload_group(config["upload_group"]),
            name="main_controls",
            # width_policy="max",
            height_policy="max",
        )

    # region: controls group

    def _build_filters_group(self, config):
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=1)
        return bokeh.layouts.column(
            bokeh.layouts.column(
                self._build_start_date_picker(config["start_date"], start_date),
                self._build_end_date_picker(config["end_date"], end_date),
                name="selectors_group",
                # # width_policy="max",
                height_policy="max",
            ),
            bokeh.layouts.column(
                self._build_category_multi_select(config["category"]),
                self._build_description_multi_select(config["description"]),
                bokeh.layouts.column(
                    self._build_card_number_multi_select(config["card_number"]),
                    self._build_data_file_multi_select(config["data_file"]),
                    name="secondary_filters",
                    # # width_policy="max",
                    height_policy="max",
                ),
                name="primary_filters_group",
                # # width_policy="max",
                height_policy="max",
            ),
            name="filters_group",
            # # width_policy="max",
            height_policy="max",
        )

    def _build_settings_group(self, config):
        return bokeh.layouts.column(
            self._build_currency_select(config["currency"]),
            name="settings_group",
            # # width_policy="max",
            height_policy="max",
        )

    def _build_start_date_picker(self, config, date):
        return bokeh.models.DatePicker(
            title=self._localizer.get_literal(
                "filters_group_start_date_control_title"
            ),
            value=date,
            name="start_date_picker",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_end_date_picker(self, config, date):
        return bokeh.models.DatePicker(
            title=self._localizer.get_literal(
                "filters_group_end_date_control_title"
            ),
            value=date,
            name="end_date_picker",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_category_multi_select(self, config):
        return bokeh.models.MultiSelect(
            title=self._localizer.get_literal(
                "filters_group_category_control_title"
            ),
            value=[],
            options=[],
            size=8,
            name="category_multi_select",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_description_multi_select(self, config):
        return bokeh.models.MultiSelect(
            title=self._localizer.get_literal(
                "filters_group_description_control_title"
            ),
            value=[],
            options=[],
            size=8,
            name="description_multi_select",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_card_number_multi_select(self, config):
        return bokeh.models.MultiSelect(
            title=self._localizer.get_literal(
                "filters_group_card_number_control_title"
            ),
            value=[],
            options=[],
            size=3,
            name="card_number_multi_select",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_data_file_multi_select(self, config):
        return bokeh.models.MultiSelect(
            title=self._localizer.get_literal(
                "filters_group_data_file_control_title"
            ),
            value=[],
            options=[],
            size=3,
            name="data_file_multi_select",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_currency_select(self, config):
        return bokeh.models.Select(
            title=self._localizer.get_literal(
                "settings_group_currency_control_title"
            ),
            value=config["default"],
            options=config["options"],
            name="currency_select",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    # endregion: controls group

    # region: bottom group

    def _build_upload_group(self, config):
        return bokeh.layouts.column(
            bokeh.layouts.row(
                self._build_upload_button(config["upload_button"]),
                name="bottom_controls_group",
                # # # width_policy="max",
                # # # height_policy="max",
            ),
            bokeh.layouts.row(
                self._build_status_bar(config["status_bar"]),
                name="bottom_status_group",
                # # # width_policy="max",
                # # # height_policy="max",
            ),
            name="bottom_group",
            # # # width_policy="max",
            # # # height_policy="max",
        )

    def _build_upload_button(self, config):
        extensions = ",".join(config["file_types"])
        return bokeh.models.FileInput(
            accept=extensions,
            multiple=True,
            name="upload_button",
            width_policy="max",
            # # height_policy="max",
        )

    def _build_width_spacer(self):
        return bokeh.models.Spacer(width_policy="max")

    def _build_height_spacer(self):
        return bokeh.models.Spacer(height_policy="max")

    def _build_status_bar(self, config):
        return bokeh.models.Div(
            text=self._localizer.get_literal("status_bar_ready_title"),
            name="status_bar",
        )

    def _build_example_button(self, config):
        return bokeh.models.Button(
            label=self._localizer.get_literal("example_button_label"),
            button_type="primary",
            name="example_button",
            width_policy="max",
            # # height_policy="max",
        )

    # endregion bottom group

    # endregion: main controls group
