# Tahir Rafique Cloth House — E-Commerce Platform

A complete, production-structured Django e-commerce system for a premium
clothing brand, with WhatsApp-based checkout, full Django Admin content
management, and a modern Tailwind-based storefront.

> **Note on this build:** this codebase was written by hand in an offline
> sandbox (no internet access to `pip install` Django or run the server).
> The code is complete and syntax-checked, but it has **not** been executed
> against a live Django install. Follow the steps below on a machine with
> internet access, and fix any small issue that turns up on first run
> (most likely candidates: a missing migration dependency order, or a
> package version mismatch) — see "First-run checklist" below.

---

## 1. Project Structure

```
project_root/
│
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── config/                 # settings, urls, wsgi, asgi
│
├── apps/
│   ├── core/                # SiteSettings, hero slides, testimonials, newsletter
│   ├── products/             # Category, Product, ProductImage, Review, filters
│   ├── cart/                 # session-based cart
│   ├── orders/                # Order, OrderItem, checkout, WhatsApp service
│   ├── accounts/              # register/login/profile
│   ├── contact/               # contact form + messages
│   └── pages/                 # home, about
│
├── templates/               # base.html + includes/ + per-app templates
├── static/                  # css/js/img (incl. logo.svg)
├── media/                   # uploaded images (created at runtime)
└── fixtures/
```

## 2. Installation

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. A ready-to-use .env is already included (with a real generated
#    SECRET_KEY) — just review it, or copy .env.example if you'd rather
#    generate your own.

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create an admin account
python manage.py createsuperuser

# 6. Seed realistic dummy data (30+ products, categories, hero slides, etc.)
python manage.py seed_data
# (use `python manage.py seed_data --no-images` if you don't want to
#  download placeholder photography, e.g. on a slow connection)

# 7. Run the development server
python manage.py runserver
```

Visit:
- Storefront: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## 3. Environment Variables (`.env`)

| Variable                  | Purpose                                         |
|----------------------------|--------------------------------------------------|
| `SECRET_KEY`               | Django secret key — set a long random value      |
| `DEBUG`                    | `True` for local dev, `False` in production       |
| `ALLOWED_HOSTS`             | Comma-separated list of allowed hosts             |
| `DEFAULT_WHATSAPP_NUMBER`   | Fallback WhatsApp number (overridden by admin)    |
| `CURRENCY`                  | Currency symbol, e.g. `Rs.`                        |

## 4. Database Setup

SQLite works out of the box for local development (already configured in
`config/settings.py`). To switch to PostgreSQL for production, uncomment the
PostgreSQL `DATABASES` block in `config/settings.py`, install `psycopg2-binary`,
and set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` in `.env`.

## 5. WhatsApp Checkout — How It Works

1. Customer adds products to cart (session-based; works for guests and
   logged-in users).
2. Customer fills in delivery details at `/orders/checkout/`.
3. On submit, the backend (`apps/orders/services.py`):
   - Creates an `Order` + `OrderItem` records with **price snapshots**, so
     historical orders are unaffected by later price changes.
   - Reads the WhatsApp number from `SiteSettings` (editable in Django
     Admin — **never hardcoded in templates**).
   - Converts the local Pakistani number (e.g. `032857948`) to
     international format (`9232857948`) via `SiteSettings.whatsapp_international`.
   - Builds a human-readable order message and URL-encodes it.
   - Returns a `https://wa.me/<number>?text=<encoded message>` link.
4. Customer is redirected to the confirmation page, which auto-opens
   WhatsApp with the pre-filled message for the customer to send.
5. The order is already saved in Django Admin at this point — admin can
   see and manage it regardless of whether the customer completes the
   WhatsApp step.

**Changing the WhatsApp number:** Django Admin → Core → Site Settings →
WhatsApp Number. No code changes needed; it takes effect immediately.

## 6. Implemented Features

- Full product catalog: categories/subcategories, tags, brands, sizes,
  colors, multiple images per product, sale pricing with computed
  discount %, stock tracking, featured/bestseller/new-arrival/deal flags.
- Product card hover image-swap (front/back), premium fashion-forward UI.
- Real database-backed search (name, SKU, description, category, tags).
- Shop, Category, and Deals pages with sidebar filters (category, price
  range, size, color, availability) and sorting (newest, price, popularity,
  discount), all driven by `django-filter`.
- Product detail page: image gallery, variant selection, quantity stepper,
  add-to-cart / buy-now, accordion info (material, care, shipping,
  returns), related products, recently-viewed (session-based).
- Session-based cart (guest + authenticated), quantity update/remove,
  live cart count in header.
- Checkout → Order + OrderItem creation → dynamic WhatsApp message/link.
- Order confirmation, order history, and order detail pages (login
  required for history/detail; guest checkout supported).
- Accounts: register, login, logout, profile edit, password handled via
  Django's built-in secure hashing.
- Contact Us form saving to the database, visible in Django Admin.
- About Us page with admin-editable brand story, mission, vision, and
  stats counters.
- Rich homepage: hero slider (admin-configurable slides), featured
  categories, flash deals, new arrivals, best sellers, trending, editorial
  sections for Men/Women/Abaya/Children, promo banner, "Why Choose Us",
  testimonials, Instagram-style gallery, newsletter signup.
- Django Admin fully wired: products (with inline image upload + preview),
  categories, orders (status changes, order item read-only inline),
  customers/profiles, reviews, newsletter subscribers, contact messages,
  site settings, hero slides, promo banners, testimonials, gallery, about
  page content.
- SEO: slugged URLs, meta description/OG tags, `sitemap.xml`, `robots.txt`.
- Security: CSRF protection on all forms, Django's built-in auth/password
  hashing, environment-variable secrets, no hardcoded credentials.
- Performance: `select_related` / `prefetch_related` used throughout
  product and order queries, pagination on all listing pages.
- Custom 404 / 500 error pages.
- Custom SVG brand logo (industry-level wordmark + monogram) used in
  header and footer; swappable any time via Site Settings → Logo.

## 7. First-Run Checklist

Since this was built without a live Django environment to test against,
please verify these on first run and fix if needed:

1. `python manage.py makemigrations` should generate clean migrations for
   all 7 apps with no circular-dependency errors (app load order in
   `INSTALLED_APPS` was chosen to avoid this: core → accounts → products →
   cart → orders → contact → pages).
2. If `django-filter` isn't picking up `ProductFilter`, confirm
   `'django_filters'` (underscore) is the app name added to
   `INSTALLED_APPS` (already done) vs. the PyPI package name
   `django-filter` (hyphen) used in `requirements.txt` — this is correct
   as written, just flagging the common gotcha.
3. `seed_data` generates all placeholder images **locally with Pillow** —
   simple, on-brand flat-lay clothing silhouettes in each product's own
   color. No internet connection and no third-party photo API are used
   for this, so there is no chance of an unrelated image (an animal, a
   random object, a visible face) ever appearing in the seeded catalog.
   One product — "Floral Print Cotton Kurti with Trousers" — uses the
   store owner's own real reference photos bundled in
   `fixtures/sample_products/` (faceless ghost-mannequin studio shots).
   Add more files there and register them in `seed_real_sample_product()`
   the same way as real product photography becomes available. Use
   `seed_data --no-images` to skip placeholder generation entirely.
4. The **Men** category is intentionally Shalwar Kameez only (no shirts,
   jeans, or Western wear) — this is set in `seed_data.py`'s category
   structure and can be extended with more subcategories there if needed.
5. Run `python manage.py collectstatic` before deploying with `DEBUG=False`.

## 9. AJAX — No Full Page Reloads

`static/js/main.js` intercepts the interactions people do most while
browsing and handles them with `fetch()` instead of a normal page
navigation:

- **Add to Cart** (product cards and the product detail page) — posts in
  the background, updates the cart-count badge in the header, and shows a
  toast message. "Buy Now" is the one deliberate exception: it still does
  a real navigation, since it needs to land on the checkout page.
- **Cart page** — quantity +/− and remove re-render just the cart panel.
- **Shop / Category / Deals / Search** — checking a filter, changing
  price range, picking a size/color swatch, switching the sort order, and
  clicking a pagination link all re-fetch just the product grid and swap
  it in place. The URL is still updated via `history.pushState`, so the
  page stays bookmarkable/shareable and the browser back button works.
- **Newsletter signup** — submits in place and shows an inline message.

Checkout submission and login/register/profile forms intentionally still
do a normal POST-and-redirect, since each of those needs to land the
person on a genuinely different page afterward (order confirmation →
WhatsApp, the profile page, etc.) — there's no reload to avoid there.

On the backend, this works by having the cart, products, and newsletter
views check for an `X-Requested-With: XMLHttpRequest` header (see
`apps/core/utils.py:is_ajax`) and, when present, return either a small
JSON payload or a partial HTML template instead of a full page — see
`apps/products/views.py:_render_listing` and
`apps/cart/views.py:_cart_fragment` for the two patterns used.

## 8. Remaining Production Considerations

- Swap SQLite for PostgreSQL (config included, commented out).
- Put `MEDIA_ROOT` behind real object storage (S3, etc.) for production —
  local `media/` won't persist on most PaaS deployments.
- Add a payment gateway if you later want online payments in addition to
  WhatsApp ordering (JazzCash/EasyPaisa/Stripe are common choices in
  Pakistan).
- Add rate limiting / captcha to the contact form and newsletter signup to
  prevent spam.
- Add automated tests (`apps/*/tests.py` stubs are a natural place to
  start — cart math, WhatsApp URL generation, and checkout flow are the
  highest-value tests to write first).
- Set `DEBUG=False`, a real `SECRET_KEY`, and proper `ALLOWED_HOSTS`
  before deploying.
- Consider Celery + a task queue if you add order-confirmation emails/SMS
  later.
