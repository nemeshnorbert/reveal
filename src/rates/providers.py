import abc
import datetime
import logging

import rates.clients
import rates.exceptions

logger = logging.getLogger(__name__)


class _ApiAccount:
    def __init__(self, credential):
        self.credential = credential
        self.successful_accesses = 0
        self.subsequent_successes = 0
        self.subsequent_failures = 0
        self.failed_accesses = 0
        self.last_access = None
        self.last_failed_access = None
        self.last_successful_access = None

    def register_access(self, type_, datetime_):
        assert isinstance(datetime_, datetime.datetime)
        self.last_access = datetime_
        if type_ == "success":
            self.subsequent_failures = 0
            self.subsequent_successes += 1
            self.successful_accesses += 1
            self.last_successful_access = datetime_
        elif type_ == "failure":
            self.subsequent_failures += 1
            self.subsequent_successes = 0
            self.failed_accesses += 1
            self.last_failed_access = datetime_
        else:
            raise RuntimeError(f"Unknown access type {type_} ")


class _ApiUsdRatesProvider(abc.ABC):
    def __init__(self, credentials):
        self._accounts = self._build_accounts(credentials)

    def get_rates(self, bids):
        bid_groups = dict()
        for date, symbol in bids:
            bid_groups.setdefault(date, set([]))
            bid_groups[date].add(symbol)

        group_rates = dict()
        for date, symbols in bid_groups.items():
            for account in self._accounts:
                now = datetime.datetime.now()
                if (
                    account.subsequent_failures >= 3
                    and now - account.last_successful_access
                    < datetime.timedelta(hours=1)
                ):
                    continue
                rates = self._get_rates_impl(date, symbols, account.credential)
                if rates is not None:
                    account.register_access("success", now)
                    break
                else:
                    account.register_access("failure", now)
            else:
                return None
            group_rates[date] = rates
        return [group_rates[date].get(symbol, None) for date, symbol in bids]

    def get_symbols(self):
        for account in self._accounts:
            now = datetime.datetime.now()
            if (
                account.subsequent_failures > 3
                and now - account.last_successful_access
                > datetime.timedelta(hours=1)
            ):
                continue
            symbols = self._get_symbols_impl(account.credential)
            if symbols is not None:
                account.register_access("success", now)
                return symbols
            else:
                account.register_access("failure", now)
        return []

    @abc.abstractmethod
    def _get_rates_impl(self, date, symbols, credential):
        del date
        del symbols
        del credential

    @abc.abstractmethod
    def _get_symbols_impl(self, credential):
        del credential

    @classmethod
    def _build_accounts(self, credentials):
        return [_ApiAccount(credential) for credential in credentials]


class _OpenexchangeratesApiUsdRatesProvider(_ApiUsdRatesProvider):
    def __init__(self, credentials, read_retries):
        super().__init__(credentials)
        self._client = rates.clients.OpenexchangeratesApiClient(read_retries)

    def _get_rates_impl(self, date, symbols, credential):
        app_id = credential["app_id"]
        base = "USD"
        try:
            response = self._client.historical(app_id, date, base, symbols)
        except rates.exceptions.OpenexchangeratesError:
            response = None
        if response is not None:
            return self._parse_historical(response)
        return None

    def _get_symbols_impl(self, credential):
        app_id = credential["app_id"]
        try:
            response = self._client.currencies(app_id)
        except rates.exceptions.OpenexchangeratesError:
            response = None
        if response is not None:
            return self._parse_currencies(response)
        return None

    def _parse_historical(self, response):
        if "error" in response:
            description = response["description"]
            logger.debug(f'Can"t parse response: {description}')
            return None
        assert response["base"] == "USD"
        return {
            symbol: response["rates"][symbol] for symbol in response["rates"]
        }

    def _parse_currencies(self, response):
        if "error" in response:
            logger.debug('Can"t parse response')
            return None
        return list(response.keys())


class _CurrencylayerApiUsdRatesProvider(_ApiUsdRatesProvider):
    def __init__(self, credentials, read_retries):
        super().__init__(credentials)
        self._client = rates.clients.CurrencylayerApiClient(read_retries)

    def _get_rates_impl(self, date, symbols, credential):
        access_key = credential["app_id"]
        source = "USD"
        currencies = symbols
        try:
            response = self._client.historical(
                access_key, date, source, currencies
            )
        except rates.exceptions.CurrencylayerError:
            response = None
        if response is not None:
            return self._parse_historical(response)
        return None

    def _get_symbols_impl(self, credential):
        access_key = credential["app_id"]
        try:
            response = self._client.list(access_key)
        except rates.exceptions.CurrencylayerError:
            response = None
        if response is not None:
            return self.parse_list(response)
        return None

    def _parse_historical(self, response):
        if not response["success"]:
            description = response["error"]["info"]
            logger.debug(f'Can"t parse response: {description}')
            return None
        assert response["source"] == "USD"
        suffix_len = len(response["source"])
        return {
            symbol[suffix_len:]: response["quotes"][symbol]
            for symbol in response["quotes"]
        }

    def _parse_list(self, response):
        if not response["success"]:
            description = response["error"]["info"]
            logger.debug(f'Can"t parse response: {description}')
            return None
        return list(response["currencies"].keys())


def build_currencylayer_api_provider(credentials, read_retries):
    return _CurrencylayerApiUsdRatesProvider(credentials, read_retries)


def build_openexchagerates_api_provider(credentials, read_retries):
    return _OpenexchangeratesApiUsdRatesProvider(credentials, read_retries)


def build_api_provider(name, credentials, read_retries):
    if name == "openexchangerates":
        return rates.providers.build_openexchagerates_api_provider(
            credentials, read_retries
        )
    elif name == "currencylayer":
        return rates.providers.build_currencylayer_api_provider(
            credentials, read_retries
        )
    else:
        raise RuntimeError(f"Unknown exchange rates provider {name}")
