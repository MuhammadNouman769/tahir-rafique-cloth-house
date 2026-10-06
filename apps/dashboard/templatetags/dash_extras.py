from django import template
from django.conf import settings

register = template.Library()

STATUS_COLORS = {
    'pending': 'amber', 'confirmed': 'blue', 'processing': 'violet',
    'shipped': 'cyan', 'delivered': 'green', 'cancelled': 'red',
}


@register.filter
def money(value):
    try:
        return f"{settings.CURRENCY_SYMBOL} {float(value):,.0f}"
    except (TypeError, ValueError):
        return f"{settings.CURRENCY_SYMBOL} 0"


@register.filter
def status_color(status):
    return STATUS_COLORS.get(status, 'gray')


@register.filter
def stars(value):
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        n = 0
    return '★' * n + '☆' * (5 - n)


@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    """Rebuild the current query string with some keys replaced (for pagination/filters)."""
    params = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v in (None, ''):
            params.pop(k, None)
        else:
            params[k] = v
    return params.urlencode()


ICONS = {
    'home': '<path d="M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10"/>',
    'chart': '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    'bag': '<path d="M6 7h12l1 13H5L6 7zM9 7a3 3 0 016 0"/>',
    'box': '<path d="M21 8l-9-5-9 5v8l9 5 9-5V8zM3 8l9 5 9-5M12 13v8"/>',
    'users': '<path d="M16 19v-1a4 4 0 00-4-4H7a4 4 0 00-4 4v1M9.5 10a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM21 19v-1a4 4 0 00-3-3.9M16 3.1a3.5 3.5 0 010 6.8"/>',
    'star': '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9L12 3z"/>',
    'mail': '<path d="M3 6h18v12H3V6zm0 0l9 7 9-7"/>',
    'tag': '<path d="M3 12V3h9l9 9-9 9-9-9zM7.5 7.5h.01"/>',
    'image': '<path d="M3 5h18v14H3V5zm0 11l5-5 4 4 3-3 6 6M8.5 9.5h.01"/>',
    'cog': '<path d="M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"/>',
    'menu': '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'moon': '<path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'download': '<path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16"/>',
    'print': '<path d="M6 9V3h12v6M6 18H4v-7h16v7h-2M6 14h12v7H6v-7z"/>',
    'store': '<path d="M3 9l1.5-5h15L21 9M3 9v11h18V9M3 9c0 2 3 2 3 0 0 2 3 2 3 0 0 2 3 2 3 0 0 2 3 2 3 0 0 2 3 2 3 0"/>',
    'out': '<path d="M9 21H5V3h4M16 17l5-5-5-5M21 12H9"/>',
    'whatsapp': '<path d="M3 21l1.6-5A9 9 0 1112 21a9 9 0 01-4.4-1.2L3 21z"/>',
    'alert': '<path d="M12 9v4m0 4h.01M10.3 3.9L2.4 18a2 2 0 001.7 3h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/>',
}


@register.simple_tag
def icon(name):
    from django.utils.safestring import mark_safe
    return mark_safe(f'<svg class="i" viewBox="0 0 24 24">{ICONS.get(name, "")}</svg>')


@register.filter
def json_script_data(value):
    return value
