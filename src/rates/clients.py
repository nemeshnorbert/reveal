import logging

import requests
import requests.adapters
import requests.packages.urllib3.util

import rates.exceptions

logger = logging.getLogger(__name__)


class _ApiClientImpl:
    def __init__(self, read_retries):
        self._session = self._build_session(read_retries)

    def get(self, url, params):
        logger.debug(f"Downloading rates from {url}")
        try:
            response = self._session.get(url, params=params)
        except requests.exceptions.RequestException as error:
            logger.exception(f"Get request to {url} has failed")
            raise rates.exceptions.OpenexchangeratesError from error
        else:
            return response.json()

    @classmethod
    def _build_session(cls, read_retries):
        session = requests.Session()
        retries = read_retries
        retry = requests.packages.urllib3.util.Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504),
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session


def _normalize_list(a_list):
    return ",".join(a_list) if a_list is not None else None


def _normalize_flag(flag):
    return int(flag) if flag is not None else None


def _setup_params(**kwargs):
    return {key: value for key, value in kwargs.items() if value is not None}


class OpenexchangeratesApiClient:
    API_URL = "https://openexchangerates.org/api"
    ENDPOINTS = {
        "latest": API_URL + "/latest.json",
        "historical": API_URL + "/historical/{date}.json",
        "currencies": API_URL + "/currencies.json",
        "time_series": API_URL + "/time-series.json",
        "convert": API_URL + "/convert/{value}/{from_}/{to_}",
        "ohlc": API_URL + "/ohlc.json",
        "usage": API_URL + "usage.json",
    }

    def __init__(self, read_retries):
        self._impl = _ApiClientImpl(read_retries)

    def latest(
        self,
        app_id,
        base=None,
        symbols=None,
        prettyprint=None,
        show_alternative=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["latest"],
            params=_setup_params(
                app_id=app_id,
                base=base,
                symbols=_normalize_list(symbols),
                prettyprint=_normalize_flag(prettyprint),
                show_alternative=_normalize_flag(show_alternative),
            ),
        )

    def historical(
        self,
        app_id,
        date,
        base=None,
        symbols=None,
        prettyprint=None,
        show_alternative=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["historical"].format(date=date),
            params=_setup_params(
                app_id=app_id,
                base=base,
                symbols=_normalize_list(symbols),
                prettyprint=_normalize_flag(prettyprint),
                show_alternative=_normalize_flag(show_alternative),
            ),
        )

    def currencies(
        self,
        app_id,
        prettyprint=None,
        show_alternative=None,
        show_inactive=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["currencies"],
            params=_setup_params(
                prettyprint=_normalize_flag(prettyprint),
                show_alternative=_normalize_flag(show_alternative),
                show_inactive=_normalize_flag(show_inactive),
            ),
        )

    def time_series(
        self,
        app_id,
        start,
        end,
        symbols=None,
        base=None,
        prettyprint=None,
        show_alternative=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["time-series"],
            params=_setup_params(
                app_id=app_id,
                start=start,
                end=end,
                base=base,
                symbols=_normalize_list(symbols),
                prettyprint=_normalize_flag(prettyprint),
                show_alternative=_normalize_flag(show_alternative),
            ),
        )

    def convert(self, app_id, value, from_, to_, prettyprint=None):
        return self._impl.get(
            url=self.ENDPOINTS["convert"].format(
                value=value, from_=from_, to_=to_
            ),
            params=_setup_params(
                app_id=app_id,
                prettyprint=_normalize_flag(prettyprint),
            ),
        )

    def ohlc(
        self,
        app_id,
        start_time,
        period,
        base=None,
        symbols=None,
        prettyprint=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["ohlc"],
            params=_setup_params(
                app_id=app_id,
                start_time=start_time,
                period=period,
                base=base,
                symbols=_normalize_list(symbols),
                prettyprint=_normalize_flag(prettyprint),
            ),
        )

    def usage(self, app_id, prettyprint=None):
        return self._impl.get(
            url=self.ENDPOINTS["usage"],
            params=_setup_params(
                app_id=app_id,
                prettyprint=_normalize_flag(prettyprint),
            ),
        )


class CurrencylayerApiClient:
    API_URL = "https://api.currencylayer.com"
    ENDPOINTS = {
        "live": API_URL + "/latest.json",
        "historical": API_URL + "/historical",
        "list": API_URL + "/list",
        "timeframe": API_URL + "/timeframe",
        "convert": API_URL + "/convert",
        "change": API_URL + "/change",
    }

    def __init__(self, read_retries):
        self._impl = _ApiClientImpl(read_retries)

    def live(
        self,
        access_key,
        source=None,
        currencies=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["latest"],
            params=_setup_params(
                access_key=access_key,
                source=source,
                currencies=_normalize_list(currencies),
            ),
        )

    def historical(
        self,
        access_key,
        date,
        source=None,
        currencies=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["historical"],
            params=_setup_params(
                access_key=access_key,
                date=date,
                source=source,
                currencies=_normalize_list(currencies),
            ),
        )

    def list(self, access_key):
        return self._impl.get(
            url=self.ENDPOINTS["currencies"],
            params=_setup_params(access_key=access_key),
        )

    def timeframe(
        self,
        access_key,
        start_date,
        end_date,
        source=None,
        currencies=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["timeframe"],
            params=_setup_params(
                access_key=access_key,
                start_date=start_date,
                end_date=end_date,
                source=source,
                currencies=_normalize_list(currencies),
            ),
        )

    def convert(self, access_key, from_, to_, amount, date=None):
        return self._impl.get(
            url=self.ENDPOINTS["convert"],
            params=_setup_params(
                **{
                    "access_key": access_key,
                    "from": from_,
                    "to": to_,
                    "amount": amount,
                    "date": date,
                }
            ),
        )

    def change(
        self,
        access_key,
        start_date,
        end_date,
        source=None,
        currencies=None,
    ):
        return self._impl.get(
            url=self.ENDPOINTS["change"],
            params=_setup_params(
                access_key=access_key,
                start_date=start_date,
                end_date=end_date,
                source=source,
                currencies=_normalize_list(currencies),
            ),
        )
