import app.exceptions
import app.model.convert
import app.model.read
import app.model.report


class RevealAppModel:
    def __init__(self, config):
        self._config = config
        self._operations = None
        self._reader = None
        self._converter = None
        self._reporter = None

    def setup(self):
        self._reader = app.model.read.OperationsReader(self._config["read"])
        self._converter = app.model.convert.OperationsConverter(
            self._config["convert"]
        )
        self._reporter = app.model.report.OperationsReporter(
            self._config["report"]
        )

    def report_overview(self, constraints, settings):
        report = {
            "income_total": 0,
            "spending_total": 0,
            "disposable_income_total": 0,
            "income": None,
            "spending": None,
            "cards": None,
        }
        if self._operations is not None:
            report = self._reporter.report_overview(
                self._operations, constraints, settings
            )
        return report

    def report_transactions(self, constraints, settings):
        report = {
            "income": None,
            "spending": None,
        }
        if self._operations is not None:
            report = self._reporter.report_transactions(
                self._operations, constraints, settings
            )
        return report

    def report_operations(self, constraints, settings):
        report = {"table": None}
        if self._operations is not None:
            self._convert_operations(settings["currency"])
            report = self._reporter.report_operations(
                self._operations, constraints, settings
            )
        return report

    def report_operations_stats(self, constraints, settings):
        assert self._operations is not None
        self._convert_operations(settings["currency"])
        return self._reporter.report_operations_stats(
            self._operations, constraints, settings
        )

    def init_operations(self, files):
        try:
            operations = self._read_operations(files)
        except Exception as error:
            message = "Failed to read operations"
            raise app.exceptions.ReadOperationsError(message) from error
        self._operations = operations

    def _read_operations(self, files):
        return self._reader.read(files)

    def _convert_operations(self, currency):
        column_name = f"operation_sum_{currency}"
        if column_name not in self._operations:
            try:
                self._operations[column_name] = self._converter.convert(
                    self._operations["operation_date"],
                    self._operations["operation_currency"],
                    self._operations["operation_total"],
                    currency,
                )
            except Exception as error:
                message = f"Failed to convert to {currency}"
                raise app.exceptions.ConvertOperationsError(message) from error
        self._operations["operation_sum"] = self._operations[column_name]
