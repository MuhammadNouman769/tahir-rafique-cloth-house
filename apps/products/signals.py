import threading
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from apps.core.models import NewsletterSubscriber, SiteSettings
from .models import Product


def _abs(base, url):
    """Make a media/static URL absolute."""
    if not url:
        return None
    return url if url.startswith('http') else base + url


def _build_html(site, product, product_url, img_url, logo_url, unsub, base):
    name = escape(product.name)
    store = escape(site.store_name)
    price = f"{escape(site.currency_symbol)} {product.price:,.0f}"
    desc = escape((getattr(product, 'short_description', '') or '')[:140])

    logo_block = (
        f'<img src="{logo_url}" alt="{store}" height="48" style="display:block;margin:0 auto;border:0;">'
        if logo_url else
        f'<span style="font-family:Georgia,serif;font-size:24px;font-weight:bold;color:#ffffff;'
        f'letter-spacing:1px;">{store}</span>'
    )

    image_block = (
        f'''<tr><td style="padding:0;">
              <a href="{product_url}"><img src="{img_url}" alt="{name}" width="520"
                 style="display:block;width:100%;max-width:520px;height:auto;border:0;"></a>
            </td></tr>''' if img_url else ''
    )

    desc_block = (
        f'<p style="margin:0 0 20px;font-size:14px;line-height:22px;color:#6b625a;">{desc}</p>'
        if desc else ''
    )

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f0e9df;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f0e9df;padding:24px 12px;">
    <tr><td align="center">

      <table role="presentation" width="520" cellpadding="0" cellspacing="0"
             style="width:100%;max-width:520px;background:#ffffff;border-radius:12px;overflow:hidden;
                    box-shadow:0 4px 18px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr><td align="center" style="background:#1a1512;padding:22px 20px;">{logo_block}</td></tr>

        <!-- Badge -->
        <tr><td align="center" style="padding:24px 24px 8px;">
          <span style="display:inline-block;background:#b8925a;color:#ffffff;font-size:11px;font-weight:bold;
                       letter-spacing:2px;padding:6px 14px;border-radius:20px;">NEW ARRIVAL</span>
        </td></tr>

        <tr><td align="center" style="padding:4px 24px 20px;">
          <h1 style="margin:8px 0 0;font-family:Georgia,serif;font-size:22px;color:#1a1512;">
            Just landed at {store}
          </h1>
        </td></tr>

        <!-- Product image -->
        {image_block}

        <!-- Product details -->
        <tr><td style="padding:24px;">
          <h2 style="margin:0 0 8px;font-family:Georgia,serif;font-size:24px;color:#1a1512;">{name}</h2>
          <p style="margin:0 0 16px;font-size:22px;font-weight:bold;color:#96703f;">{price}</p>
          {desc_block}
          <table role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td style="background:#96703f;border-radius:6px;">
              <a href="{product_url}"
                 style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:15px;font-weight:bold;
                        text-decoration:none;letter-spacing:.5px;">Shop Now &rarr;</a>
            </td>
          </tr></table>
        </td></tr>

        <!-- Perks -->
        <tr><td style="padding:0 24px 24px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="background:#faf7f2;border-radius:8px;">
            <tr>
              <td align="center" style="padding:14px 6px;font-size:12px;color:#6b625a;">&#10003; Premium Quality</td>
              <td align="center" style="padding:14px 6px;font-size:12px;color:#6b625a;">&#10003; Fast Delivery</td>
              <td align="center" style="padding:14px 6px;font-size:12px;color:#6b625a;">&#10003; Order on WhatsApp</td>
            </tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td align="center" style="background:#faf7f2;padding:20px 24px;border-top:1px solid #eee3d4;">
          <p style="margin:0 0 6px;font-size:12px;color:#8a8077;">
            {escape(site.address)} &bull; {escape(site.support_phone)}
          </p>
          <p style="margin:0;font-size:12px;color:#8a8077;">
            You're receiving this because you subscribed to our newsletter.<br>
            <a href="{unsub}" style="color:#96703f;">Unsubscribe</a>
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _send_new_product_emails(product_id):
    product = Product.objects.prefetch_related('images').get(pk=product_id)
    site = SiteSettings.load()
    subscribers = list(NewsletterSubscriber.objects.filter(is_active=True))
    if not subscribers:
        return

    base = settings.SITE_URL.rstrip('/')
    product_url = base + (
        product.get_absolute_url() if hasattr(product, 'get_absolute_url') else '/'
    )
    first_img = product.images.first()
    img_url = _abs(base, first_img.image.url) if first_img and getattr(first_img, 'image', None) else None
    logo_url = _abs(base, site.logo.url) if site.logo else None

    connection = get_connection()
    connection.open()
    for sub in subscribers:
        unsub = base + reverse('core:newsletter_unsubscribe', args=[sub.token])

        text = (
            f"New arrival at {site.store_name}: {product.name}\n"
            f"Price: {site.currency_symbol} {product.price}\n\n"
            f"View it here: {product_url}\n\n"
            f"Unsubscribe: {unsub}"
        )
        html = _build_html(site, product, product_url, img_url, logo_url, unsub, base)

        msg = EmailMultiAlternatives(
            subject=f"New Arrival: {product.name} | {site.store_name}",
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[sub.email],
            connection=connection,
        )
        msg.attach_alternative(html, "text/html")
        try:
            msg.send()
        except Exception:
            continue  # if one email fails, keep sending the rest
    connection.close()


@receiver(post_save, sender=Product)
def notify_subscribers_on_new_product(sender, instance, created, **kwargs):
    if not created or not instance.available:
        return
    # on_commit: send only after admin has saved inline images too
    transaction.on_commit(
        lambda: threading.Thread(
            target=_send_new_product_emails, args=(instance.pk,), daemon=True
        ).start()
    )