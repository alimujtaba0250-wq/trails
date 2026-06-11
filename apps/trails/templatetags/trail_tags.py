from django import template

register = template.Library()

_DIFFICULTY_CLASSES = {
    "easy":     "bg-tertiary-fixed text-on-tertiary-fixed",
    "moderate": "bg-secondary-container text-on-secondary-container",
    "hard":     "bg-error-container text-on-error-container",
}


@register.filter
def difficulty_badge_class(difficulty: str) -> str:
    """Return Tailwind bg/text classes for a difficulty string."""
    return _DIFFICULTY_CLASSES.get((difficulty or "").lower(), "bg-surface-container text-on-surface")


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Build a query string that merges existing GET params with kwargs overrides."""
    request = context.get("request")
    params = request.GET.copy() if request else {}
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()


@register.filter
def split(value, delimiter=","):
    """Split a string by delimiter — e.g. "a,b,c"|split:"," → ['a','b','c']."""
    return value.split(delimiter)


@register.filter
def star_range(rating):
    """Return a list of (filled, index) tuples for 5 stars based on a 0-5 rating."""
    if not rating:
        return []
    full = int(round(float(rating)))
    return [i < full for i in range(5)]
