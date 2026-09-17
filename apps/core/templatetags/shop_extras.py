from django import template

register = template.Library()


@register.filter
def currency(value, symbol="Rs."):
    try:
        return f"{symbol} {float(value):,.0f}"
    except (TypeError, ValueError):
        return value


@register.filter
def stars_range(rating):
    try:
        return range(int(round(float(rating))))
    except (TypeError, ValueError):
        return range(0)


@register.filter
def empty_stars_range(rating):
    try:
        return range(5 - int(round(float(rating))))
    except (TypeError, ValueError):
        return range(5)
