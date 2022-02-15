import functools

import db.utils
import rates.providers


class DatabaseUsdRatesProxy(db.utils.DatabaseIO):
    def __init__(self, config):
        super().__init__(config["path"])
        self._config = config

    def get_rates(self, bids):
        return [self._get_rate(date, symbol) for date, symbol in bids]

    @functools.lru_cache(maxsize=65536, typed=True)
    def _get_rate(self, date, symbol):
        if symbol == "USD":
            return 1.0
        cursor = self._connection.cursor()
        cursor.execute(self._get_read_command(), (date, symbol))
        row = cursor.fetchone()
        return row[0] if row is not None else None

    def set_rates(self, bids, rates):
        cursor = self._connection.cursor()
        values = (
            (date, symbol, rate) for (date, symbol), rate in zip(bids, rates)
        )
        cursor.executemany(self._get_write_command(), values)
        self._connection.commit()

    @classmethod
    def _get_read_command(cls):
        return "SELECT rate FROM usd_rates WHERE date=? AND symbol=?"

    @classmethod
    def _get_write_command(cls):
        return (
            "INSERT OR IGNORE INTO usd_rates(date, symbol, rate) "
            "VALUES (?, ?, ?);"
        )


class CurrencyExchangeRatesProvider:
    def __init__(self, config):
        self._config = config
        self._db = DatabaseUsdRatesProxy(self._config["database"])
        self._api = rates.providers.build_api_provider(
            name=self._config["api"]["provider"],
            credentials=self._config["api"]["credentials"],
            read_retries=self._config["api"]["read_retries"],
        )

    def __enter__(self):
        self._db.__enter__()
        return self

    def get_rates(self, bids):
        usd_bids = set([])
        for date, base, symbol in bids:
            if symbol != base:
                usd_bids.add((date, base))
                usd_bids.add((date, symbol))
        usd_rates = dict(zip(usd_bids, self._get_usd_rates(usd_bids)))
        return [
            (
                usd_rates[(date, symbol)] / usd_rates[(date, base)]
                if symbol != base
                else 1.0
            )
            for date, base, symbol in bids
        ]

    def _get_usd_rates(self, bids):
        assert isinstance(bids, set)
        bids = list(bids)
        rates = self._db.get_rates(bids)
        unknown_rate_ids = [
            idx for idx, rate in enumerate(rates) if rate is None
        ]
        if unknown_rate_ids:
            unknown_rates = self._api.get_rates(
                [bids[idx] for idx in unknown_rate_ids]
            )
        else:
            unknown_rates = None
        if unknown_rates is not None:
            for position, idx in enumerate(unknown_rate_ids):
                rates[idx] = unknown_rates[position]
        self._db.set_rates(
            bids=(bids[idx] for idx in unknown_rate_ids),
            rates=(rates[idx] for idx in unknown_rate_ids),
        )
        return rates

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._db.__exit__(exc_type, exc_value, exc_traceback)
        return False
