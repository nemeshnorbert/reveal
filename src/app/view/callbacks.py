class ViewCallbacksManager:
    def __init__(self, elements, controller):
        self._elements = elements
        self._controller = controller
        self._toggles = {
            "upload_button": self._upload_button_toggle,
            "tabs_group": self._tabs_group_toggle,
            "transactions_tab_plot_mode_selector": self._transactions_tab_plot_mode_selector_toggle,
            "transactions_tab_period_selector": self._transactions_tab_period_selector_toggle,
            "start_date_picker": self._start_date_picker_toggle,
            "end_date_picker": self._end_date_picker_toggle,
            "category_multi_select": self._category_multi_select_toggle,
            "description_multi_select": self._description_multi_select_toggle,
            "card_number_multi_select": self._card_number_multi_select_toggle,
            "data_file_multi_select": self._data_file_multi_select_toggle,
            "currency_select": self._currency_select_toggle,
            "example_button": self._example_button_toggle,
        }

    def setup_callbacks(self):
        self._toggle_callbacks(how="on", control_names=self._toggles.keys())

    def reset_callbacks(self):
        self._toggle_callbacks(how="off", control_names=self._toggles.keys())

    def setup_controls_callbacks(self):
        self._toggle_controls_callbacks(how="on")

    def reset_controls_callbacks(self):
        self._toggle_controls_callbacks(how="off")

    def _toggle_controls_callbacks(self, how):
        control_names = [
            "start_date_picker",
            "end_date_picker",
            "card_number_multi_select",
            "category_multi_select",
            "description_multi_select",
            "data_file_multi_select",
        ]
        self._toggle_callbacks(how, control_names)

    def _toggle_callbacks(self, how, control_names):
        for control_name in control_names:
            toggle = self._toggles[control_name]
            toggle(how)

    def _upload_button_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="upload_button",
            attr_name="value",
            handler=self._controller.on_upload_files,
        )
        self._value_callback_toggle(
            how,
            control_name="upload_button",
            attr_name="filename",
            handler=self._controller.on_set_file_names,
        )

    def _tabs_group_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="tabs_group",
            attr_name="active",
            handler=self._controller.on_tab_change,
        )

    def _transactions_tab_plot_mode_selector_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="transactions_tab_plot_mode_selector",
            attr_name="value",
            handler=self._controller.on_transactions_tab_plot_settings_change,
        )

    def _transactions_tab_period_selector_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="transactions_tab_period_selector",
            attr_name="value",
            handler=self._controller.on_transactions_tab_plot_settings_change,
        )

    def _start_date_picker_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="start_date_picker",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _end_date_picker_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="end_date_picker",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _category_multi_select_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="category_multi_select",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _description_multi_select_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="description_multi_select",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _card_number_multi_select_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="card_number_multi_select",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _data_file_multi_select_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="data_file_multi_select",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _currency_select_toggle(self, how):
        self._value_callback_toggle(
            how,
            control_name="currency_select",
            attr_name="value",
            handler=self._controller.on_control_change,
        )

    def _example_button_toggle(self, how):
        if how == "on":
            self._elements["example_button"].on_click(
                self._controller.on_load_example_click
            )
        elif how == "off":
            raise NotImplementedError()
        else:
            assert how in ["on", "off"]

    def _value_callback_toggle(self, how, control_name, attr_name, handler):
        if how == "on":
            self._elements[control_name].on_change(attr_name, handler)
        elif how == "off":
            self._elements[control_name].remove_on_change(attr_name, handler)
        else:
            assert how in ["on", "off"]
