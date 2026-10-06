import csv
import re
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import HttpResponse

from apps.products.models import Review


def paginate(request, items, per_page=20):
    paginator = Paginator(items, per_page)
    return paginator.get_page(request.GET.get('page'))


def csv_response(filename, header, rows):
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp.write('\ufeff')  # BOM so Excel opens UTF-8 (Urdu names etc.) correctly
    w = csv.writer(resp)
    w.writerow(header)
    w.writerows(rows)
    return resp


def recalc_product_rating(product):
    """Keep Product.rating / review_count (shown on the storefront) in sync with approved reviews."""
    agg = Review.objects.filter(product=product, approved=True).aggregate(avg=Avg('rating'), n=Count('id'))
    product.review_count = agg['n']
    if agg['n']:
        product.rating = round(agg['avg'], 1)
    product.save(update_fields=['rating', 'review_count'])


def wa_number(raw):
    """03xx-xxxxxxx -> 923xxxxxxxxx for wa.me links."""
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('0'):
        digits = digits[1:]
    if not digits.startswith('92'):
        digits = '92' + digits
    return digits
