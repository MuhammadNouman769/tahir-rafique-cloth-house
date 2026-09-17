def is_ajax(request):
    """True if the request was made via fetch()/XHR with our JS convention
    header, so views can return a lightweight partial instead of a full page."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
