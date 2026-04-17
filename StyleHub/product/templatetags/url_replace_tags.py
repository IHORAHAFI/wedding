from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Return encoded query string with updated GET parameters.

    Usage: href="?{% url_replace page=2 %}" keeps existing GET params and
    replaces/sets the provided ones.
    """
    request = context.get('request')
    if not request:
        return ''

    query = request.GET.copy()
    for k, v in kwargs.items():
        query[k] = v

    # Remove any empty keys
    for k in [k for k, v in query.items() if v in ('', None)]:
        # keep empty values if intentionally set
        pass

    return query.urlencode()
