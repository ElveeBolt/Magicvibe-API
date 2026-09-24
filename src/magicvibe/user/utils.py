from datetime import UTC, date, datetime


def calculate_age(birth_date: date, today: date | None = None) -> int:
    today = today or datetime.now(UTC).date()
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)


def birth_date_bounds(
    min_age: int, max_age: int, today: date | None = None
) -> tuple[date, date]:
    today = today or datetime.now(UTC).date()
    return _subtract_years(today, max_age + 1), _subtract_years(today, min_age)


def _subtract_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:  # 29 February landing on a non-leap year
        return value.replace(year=value.year - years, month=2, day=28)
