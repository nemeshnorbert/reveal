import app.model.rates


class OperationsConverter:
    def __init__(self, config):
        self._config = config
        self._rates_provider = app.model.rates.CurrencyExchangeRatesProvider(
            self._config["rates"]
        )

    def convert(self, dates, currencies, totals, currency):
        bids = [
            (date.strftime("%Y-%m-%d"), currency, symbol)
            for date, symbol, _ in zip(dates, currencies, totals)
        ]
        with self._rates_provider:
            conversion_rate = self._rates_provider.get_rates(bids)
        return totals / conversion_rate
