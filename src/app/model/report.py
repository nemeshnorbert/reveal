import datetime

import pandas


def _make_default_mask(values, default):
    return pandas.Series(default, index=values.index)


def _make_dates_mask(dates, date_range):
    start_date, end_date = date_range
    if start_date is None:
        start_date = dates.min()
    if end_date is None:
        end_date = dates.max()
    return (start_date <= dates) & (dates <= end_date)


def _make_values_mask(values, white_list):
    if white_list is None:
        return _make_default_mask(values, False)
    return values.isin(white_list)


def _make_constraint_mask(operations, constraint):
    column_names = ["data_file", "card_number", "category", "description"]
    value_names = ["data_files", "card_numbers", "categories", "descriptions"]
    mask = _make_dates_mask(
        operations["operation_date"], constraint["date_range"]
    )
    for column_name, value_name in zip(column_names, value_names):
        values_mask = _make_values_mask(
            operations[column_name], constraint[value_name]
        )
        mask = mask & values_mask
    return mask


def _make_constraints_mask(operations, constraints):
    if constraints is None:
        mask = _make_default_mask(operations, True)
    else:
        mask = _make_default_mask(operations, False)
        for constraint in constraints:
            mask |= _make_constraint_mask(operations, constraint)
    return mask


def _get_operations(operations, mask):
    if mask is None:
        mask = _make_default_mask(operations, True)
    return operations[mask].copy()


def _get_income(operations, mask):
    if mask is None:
        mask = _make_default_mask(operations, True)
    income_mask = (operations["operation_sum"] >= 0) & mask
    income = operations[income_mask].copy()
    income.sort_values(by="operation_date", inplace=True)
    income.reset_index(inplace=True)
    return income


def _get_spending(operations, mask):
    if mask is None:
        mask = _make_default_mask(operations, True)
    spending_mask = (operations["operation_sum"] < 0) & mask
    spending = operations[spending_mask].copy()
    spending["operation_sum"] *= -1
    spending.sort_values(by="operation_date", inplace=True)
    spending.reset_index(inplace=True)
    return spending


def _accumulate_operation_sum(operations, accumulation_type):
    if accumulation_type == "cumulative":
        operations["operation_sum"] = operations["operation_sum"].cumsum()
    elif accumulation_type == "incremental":
        pass
    else:
        raise RuntimeError("Unknown transctions_report_type")
    return operations


def _make_digest(strings):
    return ",".join(strings.unique())


def _aggreagate_operations_by_period(operations, period):
    rules = {"seconds": "S", "days": "D", "months": "M", "years": "AS"}
    if period not in rules:
        raise RuntimeError("Unknown period {period}")
    elif period == "seconds":
        return operations
    else:
        aggregated = operations.resample(
            rule=rules[period],
            on="operation_date",
            closed="left",
            label="left",
        ).aggregate(
            {
                "operation_sum": "sum",
                "data_file": _make_digest,
                "category": _make_digest,
                "description": _make_digest,
            }
        )
        aggregated.reset_index(inplace=True)
        return aggregated


def _aggregate_operations_by_category(operations):
    view = operations.groupby("category").aggregate({"operation_sum": "sum"})
    view.sort_values(by="operation_sum", ascending=False, inplace=True)
    view.reset_index(inplace=True)
    return view


def _get_overview_operations_by_category(operations, top_categories_count):
    view = _aggregate_operations_by_category(operations)
    top_categories_count = min(top_categories_count, len(view))
    view.loc[top_categories_count:, "category"] = "Ocтальное"
    return _aggregate_operations_by_category(view)


def _get_overview_operations_by_card(operations, mask):
    view = operations.loc[mask, ["card_number", "operation_sum"]].copy()
    view["type"] = view["operation_sum"].map(
        lambda quantity: "income" if quantity >= 0 else "spending"
    )
    view = view.pivot_table(
        values="operation_sum",
        index="card_number",
        columns="type",
        aggfunc="sum",
    )
    for column_name in ["income", "spending"]:
        if column_name not in view:
            view[column_name] = 0
    view.reset_index(inplace=True)
    view["spending"] *= -1
    return view


def _get_date_range(operations, mask):
    if operations.empty:
        return (None, None)
    if mask is None:
        mask = _make_default_mask(operations, True)
    view = operations.loc[mask, "operation_date"]
    start_date = (
        None if view.empty else view.min().date() - datetime.timedelta(days=1)
    )
    end_date = (
        None if view.empty else view.max().date() + datetime.timedelta(days=1)
    )
    return (start_date, end_date)


def _get_unique_data_files(operations, mask):
    return _get_unique_column(operations, mask, "data_file")


def _get_unique_categories(operations, mask):
    return _get_unique_column(operations, mask, "category")


def _get_unique_descriptions(operations, mask):
    return _get_unique_column(operations, mask, "description")


def _get_unique_card_numbers(operations, mask):
    return _get_unique_column(operations, mask, "card_number")


def _get_unique_column(operations, mask, column):
    if mask is None:
        mask = _make_default_mask(operations, True)
    return list(operations.loc[mask, column].unique())


class OperationsReporter:
    def __init__(self, config):
        self._config = config

    def report_operations(self, operations, constraints, settings):
        del settings
        mask = _make_constraints_mask(operations, constraints)
        return {"table": _get_operations(operations, mask)}

    def report_transactions(self, operations, constraints, settings):
        mask = _make_constraints_mask(operations, constraints)
        income = _aggreagate_operations_by_period(
            operations=_get_income(operations, mask),
            period=settings["transactions_period"],
        )
        _accumulate_operation_sum(
            operations=income,
            accumulation_type=settings["transactions_report_type"],
        )
        spending = _aggreagate_operations_by_period(
            operations=_get_spending(operations, mask),
            period=settings["transactions_period"],
        )
        _accumulate_operation_sum(
            operations=spending,
            accumulation_type=settings["transactions_report_type"],
        )
        return {
            "income": income,
            "spending": spending,
        }

    def report_overview(self, operations, constraints, settings):
        del settings
        mask = _make_constraints_mask(operations, constraints)
        income = _get_overview_operations_by_category(
            _get_income(operations, mask),
            self._config["max_overview_categories_count"],
        )
        spending = _get_overview_operations_by_category(
            _get_spending(operations, mask),
            self._config["max_overview_categories_count"],
        )
        income_total = income["operation_sum"].sum()
        spending_total = spending["operation_sum"].sum()
        return {
            "income_total": income_total,
            "spending_total": spending_total,
            "disposable_income_total": income_total - spending_total,
            "income": income,
            "spending": spending,
            "cards": _get_overview_operations_by_card(operations, mask),
        }

    def report_operations_stats(self, operations, constraints, settings):
        del settings
        mask = _make_constraints_mask(operations, constraints)
        return {
            "date_range": _get_date_range(operations, mask),
            "data_files": _get_unique_data_files(operations, mask),
            "categories": _get_unique_categories(operations, mask),
            "descriptions": _get_unique_descriptions(operations, mask),
            "card_numbers": _get_unique_card_numbers(operations, mask),
        }
