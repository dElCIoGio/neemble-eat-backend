def format_number(value: float) -> str:
    """Return a string with a space as thousands separator and two decimals."""
    return f"{value:,.2f}".replace(",", " ")
