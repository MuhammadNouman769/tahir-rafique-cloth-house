from apps.contact.models import ContactMessage
from apps.orders.models import Order
from apps.products.models import Review


def dashboard_counts(request):
    """Sidebar badges. Only runs for dashboard pages so the storefront pays nothing."""
    if not request.path.startswith('/dashboard/') or not request.user.is_authenticated:
        return {}
    return {
        'nav_pending_orders': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        'nav_unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'nav_pending_reviews': Review.objects.filter(approved=False).count(),
    }
