"""
Populates the database with realistic dummy data so the store never looks
empty on first run.

Usage:
    python manage.py seed_data

All images are generated LOCALLY with Pillow (see _placeholder_art.py) —
simple, on-brand flat-lay clothing silhouettes in each product's own
color. No internet connection, no third-party photo API, and therefore no
chance of an unrelated image (an animal, a random object, a visible face)
ever appearing in the seeded catalog.

One real product ("Floral Print Cotton Kurti with Trousers") uses the
store owner's own reference photos (real, faceless ghost-mannequin studio
shots) bundled in fixtures/sample_products/, so at least one catalog entry
is guaranteed to match the exact desired photography style. Add more
files to that folder and register them the same way to grow this list.

Safe to re-run — it skips records that already exist.
"""
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import (
    SiteSettings, HeroSlide, PromoBanner, Testimonial, GalleryImage,
)
from apps.pages.models import AboutContent
from apps.products.models import (
    Category, Tag, Brand, Size, Color, Product, ProductImage, Review, SIZE_CHOICES, COLOR_CHOICES,
)
from . import _placeholder_art as art

# Maps a category key to the garment silhouette used for its placeholder
# art, and a fixed brand color used for category/hero banner tiles (kept
# separate from per-product colors, which use the product's own variant).
CATEGORY_SHAPE = {
    'men': 'kameez', 'men:Shalwar Kameez': 'kameez',
    'women': 'kurti', 'women:Dresses': 'dress', 'women:Suits': 'suit',
    'women:Tops': 'top', 'women:Trousers': 'trousers', 'women:Kurtis': 'kurti',
    'children': 'kids_set', 'children:Boys': 'kids_boy', 'children:Girls': 'kids_girl',
    'children:Kids Sets': 'kids_set',
    'abaya': 'abaya', 'abaya:Classic Abaya': 'abaya', 'abaya:Open Abaya': 'abaya',
    'abaya:Embroidered Abaya': 'abaya', 'abaya:Premium Abaya': 'abaya',
}
CATEGORY_BANNER_COLOR = {
    'men': '#2b4c8c', 'women': '#7a1f2b', 'children': '#c8962c', 'abaya': '#1a1a1a',
}


class Command(BaseCommand):
    help = "Seed the database with realistic clothing store dummy data."

    def add_arguments(self, parser):
        parser.add_argument('--no-images', action='store_true',
                             help="Skip generating placeholder images (faster).")

    def handle(self, *args, **options):
        self.make_images = not options['no_images']
        with transaction.atomic():
            self.seed_site_settings()
            self.seed_taxonomy()
            self.seed_products()
            self.seed_real_sample_product()
            self.seed_hero_and_content()
        self.stdout.write(self.style.SUCCESS("✔ Database seeded successfully."))

    # ------------------------------------------------------------------
    def seed_site_settings(self):
        s = SiteSettings.load()
        s.store_name = "Tahir Rafique Cloth House"
        s.tagline = "Premium Fashion For Every Occasion"
        s.whatsapp_number = "032857948"
        s.support_phone = "032857948"
        s.email = "info@tahirrafiqueclothhouse.com"
        s.address = "Blue Area, Islamabad, Pakistan"
        s.facebook_url = "https://facebook.com/tahirrafiqueclothhouse"
        s.instagram_url = "https://instagram.com/tahirrafiqueclothhouse"
        s.tiktok_url = "https://tiktok.com/@tahirrafiqueclothhouse"
        s.delivery_charges = Decimal('250')
        s.free_delivery_threshold = Decimal('5000')
        s.currency_symbol = "Rs."
        s.announcement_text = "Free Delivery on Orders Above Rs. 5,000"
        s.save()
        self.stdout.write("  Site settings ready.")

    # ------------------------------------------------------------------
    def seed_taxonomy(self):
        self.categories = {}
        structure = {
            'men': ("Men", ["Shalwar Kameez"]),
            'women': ("Women", ["Dresses", "Suits", "Tops", "Trousers", "Kurtis"]),
            'children': ("Children", ["Boys", "Girls", "Kids Sets"]),
            'abaya': ("Abaya", ["Classic Abaya", "Open Abaya", "Embroidered Abaya", "Premium Abaya"]),
        }
        order = 0
        for slug, (name, subs) in structure.items():
            order += 1
            parent, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'order': order})
            if self.make_images and not parent.image:
                shape = CATEGORY_SHAPE.get(slug, 'kameez')
                color = CATEGORY_BANNER_COLOR.get(slug, '#8a6d4a')
                img = art.garment_image(shape, color, 900, 700, 'front', seed=f"cat-{slug}")
                fname, cfile = art.to_content_file(img, f"cat-{slug}.jpg")
                parent.image.save(fname, cfile, save=False)
            parent.active = True
            parent.save()
            self.categories[slug] = parent
            for i, sub_name in enumerate(subs, start=1):
                sub, _ = Category.objects.get_or_create(
                    name=sub_name, parent=parent,
                    defaults={'order': i})
                if self.make_images and not sub.image:
                    key = f"{slug}:{sub_name}"
                    shape = CATEGORY_SHAPE.get(key, CATEGORY_SHAPE.get(slug, 'kameez'))
                    color = CATEGORY_BANNER_COLOR.get(slug, '#8a6d4a')
                    img = art.garment_image(shape, color, 900, 700, 'front', seed=f"cat-{key}")
                    fname, cfile = art.to_content_file(img, f"cat-{slug}-{sub_name}.jpg")
                    sub.image.save(fname, cfile, save=True)
                self.categories[f"{slug}:{sub_name}"] = sub

        for name in ["Casual", "Formal", "Party Wear", "Bestseller", "Cotton", "Lawn", "Embroidered"]:
            Tag.objects.get_or_create(name=name)

        for name in ["TRCH Signature", "TRCH Premium", "TRCH Essentials"]:
            Brand.objects.get_or_create(name=name)

        for code, _ in SIZE_CHOICES:
            Size.objects.get_or_create(name=code)

        hex_map = {
            'Black': '#1a1a1a', 'White': '#f5f5f0', 'Blue': '#2b4c8c', 'Red': '#b3202c',
            'Green': '#2f5d3a', 'Brown': '#6b4a2f', 'Grey': '#8a8a85', 'Maroon': '#6e1f2b',
            'Navy': '#1f2a4d', 'Beige': '#d8c9a8', 'Pink': '#d98ba0', 'Mustard': '#c8962c',
        }
        for name, _ in COLOR_CHOICES:
            Color.objects.get_or_create(name=name, defaults={'hex_code': hex_map.get(name, '#000000')})

        self.stdout.write("  Categories, tags, brands, sizes, colors ready.")

    # ------------------------------------------------------------------
    def seed_products(self):
        if Product.objects.count() >= 30:
            self.stdout.write("  Products already seeded (30+ found) — skipping.")
            return

        sizes = list(Size.objects.all())
        colors = list(Color.objects.all())
        tags = list(Tag.objects.all())
        brands = list(Brand.objects.all())

        PRODUCTS = [
            ("Premium Black Abaya", "abaya:Premium Abaya", 6999, 4999, "An elegant flowing black abaya crafted from premium nida fabric with a graceful silhouette, perfect for daily wear and special occasions."),
            ("Classic Open Abaya", "abaya:Open Abaya", 5499, None, "A timeless open-style abaya with clean lines, designed for effortless layering over your everyday outfits."),
            ("Embroidered Emerald Abaya", "abaya:Embroidered Abaya", 8499, 6999, "Delicate hand-inspired embroidery along the sleeves and hem elevates this emerald green abaya for festive occasions."),
            ("Classic Everyday Abaya", "abaya:Classic Abaya", 4499, None, "A comfortable, breathable classic abaya designed for all-day wear with a relaxed, modest fit."),
            ("Premium Pearl Abaya", "abaya:Premium Abaya", 9499, 7499, "Luxurious pearl-detailed abaya made from soft crepe fabric, tailored for a flattering modern silhouette."),
            ("Classic White Shalwar Kameez", "men:Shalwar Kameez", 3999, None, "A crisp white shalwar kameez set in breathable cotton, ideal for Friday prayers and formal gatherings."),
            ("Premium Men's Kurta", "men:Shalwar Kameez", 4499, 3599, "A refined kurta with subtle textured fabric and mother-of-pearl buttons, tailored for a modern fit."),
            ("Embroidered Black Shalwar Kameez", "men:Shalwar Kameez", 5499, 4399, "A sharply tailored black shalwar kameez with fine collar embroidery, perfect for evening events."),
            ("Formal Grey Shalwar Kameez", "men:Shalwar Kameez", 4799, None, "A tailored grey shalwar kameez in a smooth blended fabric, suited for office and formal wear."),
            ("Casual Lawn Shalwar Kameez", "men:Shalwar Kameez", 3299, 2699, "A lightweight lawn shalwar kameez designed for comfort through Pakistan's warmer months."),
            ("Wedding Collection Shalwar Kameez", "men:Shalwar Kameez", 8999, 6999, "An opulent wedding-collection shalwar kameez with detailed embroidery along the collar and cuffs."),
            ("Waistcoat Shalwar Kameez Set", "men:Shalwar Kameez", 6499, None, "A classic three-piece set pairing a tailored waistcoat with matching shalwar kameez."),
            ("Chikankari Shalwar Kameez", "men:Shalwar Kameez", 5999, 4799, "Delicate chikankari hand-embroidery detailing across a soft cotton shalwar kameez."),
            ("Khaddar Shalwar Kameez", "men:Shalwar Kameez", 3599, None, "A warm khaddar-fabric shalwar kameez, perfect for the winter season."),
            ("Eid Collection Shalwar Kameez", "men:Shalwar Kameez", 6999, 5599, "A festive Eid-collection shalwar kameez in a rich fabric with subtle self-print detailing."),
            ("Kurta Pajama Set", "men:Shalwar Kameez", 3799, None, "A comfortable kurta and pajama set suited for both daily wear and casual gatherings."),
            ("Printed Cotton Shalwar Kameez", "men:Shalwar Kameez", 3499, 2799, "A relaxed-fit printed cotton shalwar kameez for everyday comfort and style."),
            ("Sherwani-Collar Shalwar Kameez", "men:Shalwar Kameez", 7499, None, "A modern sherwani-collar shalwar kameez tailored for weddings and formal celebrations."),
            ("Formal Cream Shalwar Kameez", "men:Shalwar Kameez", 4199, None, "A breathable premium cream shalwar kameez perfect for warm-weather formal wear."),
            ("Embroidered Women's Dress", "women:Dresses", 5999, 4799, "A flowing embroidered dress with intricate thread-work detailing across the neckline."),
            ("Floral Print Maxi Dress", "women:Dresses", 4999, None, "A breezy floral maxi dress in soft lawn fabric, perfect for summer days."),
            ("Satin Evening Gown", "women:Dresses", 9999, 7999, "An elegant satin evening gown designed for special occasions."),
            ("Embroidered 3-Piece Suit", "women:Suits", 7999, 6399, "A premium 3-piece embroidered suit including shirt, trouser and dupatta."),
            ("Printed Lawn 2-Piece Suit", "women:Suits", 4499, None, "A vibrant printed lawn 2-piece suit ideal for everyday elegance."),
            ("Casual Chiffon Top", "women:Tops", 2299, 1799, "A lightweight chiffon top with delicate button detailing."),
            ("Embellished Party Top", "women:Tops", 3299, None, "A statement embellished top designed for evening occasions."),
            ("Wide Leg Trousers", "women:Trousers", 2799, None, "Flowy wide-leg trousers in a soft crepe fabric for all-day comfort."),
            ("Cigarette Pants", "women:Trousers", 2199, 1699, "Classic tapered cigarette pants that pair perfectly with kurtis."),
            ("Printed Cotton Kurti", "women:Kurtis", 2499, None, "A relaxed-fit printed cotton kurti perfect for daily wear."),
            ("Embroidered A-Line Kurti", "women:Kurtis", 3499, 2799, "An elegant A-line kurti with embroidered neckline detail."),
            ("Boys Casual Shalwar Kameez Set", "children:Boys", 2199, None, "A comfortable shalwar kameez set for active boys."),
            ("Boys Festive Kurta Set", "children:Boys", 2999, 2399, "A smart festive kurta and pajama set for special occasions."),
            ("Girls Party Frock", "children:Girls", 3299, None, "A sweet layered party frock with a soft tulle underskirt."),
            ("Girls Printed Kurti Set", "children:Girls", 2499, 1999, "A cheerful printed kurti and trouser set for girls."),
            ("Kids Cotton Set", "children:Kids Sets", 1999, None, "A soft cotton co-ord set suitable for boys and girls alike."),
            ("Kids Winter Sweater Set", "children:Kids Sets", 2699, 2199, "A cozy knitted sweater and pants set for cooler days."),
        ]

        for i, (name, cat_key, price, sale_price, desc) in enumerate(PRODUCTS, start=1):
            category = self.categories.get(cat_key)
            if category is None:
                continue
            product, created = Product.objects.get_or_create(
                sku=f"TRCH-{1000 + i}",
                defaults=dict(
                    name=name,
                    category=category,
                    brand=random.choice(brands),
                    description=desc + " Made with premium materials and finished with attention to detail, "
                                        "this piece is designed to be a versatile addition to your wardrobe.",
                    short_description=desc,
                    price=Decimal(price),
                    sale_price=Decimal(sale_price) if sale_price else None,
                    stock_quantity=random.choice([0, 5, 8, 12, 20, 35]),
                    available=True,
                    featured=(i % 4 == 0),
                    bestseller=(i % 5 == 0),
                    new_arrival=(i % 3 == 0),
                    deal_of_day=bool(sale_price) and (i % 2 == 0),
                    rating=Decimal(random.choice(['3.5', '4.0', '4.2', '4.5', '4.8', '5.0'])),
                    review_count=random.randint(3, 120),
                )
            )
            if not created:
                continue

            product.sizes.set(random.sample(sizes, k=min(4, len(sizes))))
            product_colors = random.sample(colors, k=min(3, len(colors)))
            product.colors.set(product_colors)
            product.tags.set(random.sample(tags, k=min(2, len(tags))))

            if self.make_images:
                shape = CATEGORY_SHAPE.get(cat_key, CATEGORY_SHAPE.get(cat_key.split(':')[0], 'kameez'))
                main_color = product_colors[0].hex_code if product_colors else '#8a6d4a'
                for angle, suffix in enumerate(["front", "back"], start=1):
                    img = art.garment_image(shape, main_color, 800, 1000, suffix, seed=f"p{i}-{suffix}")
                    fname, cfile = art.to_content_file(img, f"trch-p{i}-{suffix}.jpg")
                    pi = ProductImage(product=product, alt_text=f"{name} - {suffix}",
                                       is_primary=(angle == 1), order=angle)
                    pi.image.save(fname, cfile, save=True)

            for r in range(random.randint(0, 3)):
                Review.objects.create(
                    product=product,
                    customer_name=random.choice(["Ayesha K.", "Bilal M.", "Sana R.", "Hamza T.", "Zainab S.", "Usman A."]),
                    rating=random.choice([4, 4, 5, 5, 5, 3]),
                    comment=random.choice([
                        "Great quality fabric and true to size. Very happy with this purchase.",
                        "Fast delivery and the product looks even better in person.",
                        "Good value for money. Will order again.",
                        "Loved the stitching quality, highly recommend.",
                    ]),
                )

        self.stdout.write(f"  Seeded {len(PRODUCTS)} products with images, variants and reviews.")

    # ------------------------------------------------------------------
    def seed_real_sample_product(self):
        """Attaches the store owner's own reference photos (real, faceless
        ghost-mannequin studio shots) to one guaranteed catalog entry, so at
        least one product matches the exact desired photography style —
        everything else in fixtures/sample_products/ can be extended the
        same way as real product photography becomes available."""
        sample_dir = Path(django_settings.BASE_DIR) / 'fixtures' / 'sample_products'
        front = sample_dir / 'floral-kurti-front.png'
        back = sample_dir / 'floral-kurti-back.png'
        if not (front.exists() and back.exists()):
            return

        category = self.categories.get('women:Kurtis')
        if category is None:
            return

        product, created = Product.objects.get_or_create(
            sku="TRCH-2000",
            defaults=dict(
                name="Floral Print Cotton Kurti with Trousers",
                category=category,
                description=(
                    "A relaxed-fit orange floral print kurti paired with matching soft cotton "
                    "trousers, finished with a scalloped, contrast-embroidered hem on both the "
                    "kurti and trouser cuffs. Cut for effortless everyday comfort in breathable "
                    "cotton fabric."
                ),
                short_description="Orange floral kurti with matching trousers and a scalloped embroidered hem.",
                price=Decimal('3799'),
                sale_price=Decimal('2999'),
                stock_quantity=18,
                available=True,
                featured=True,
                bestseller=True,
                new_arrival=True,
                rating=Decimal('4.8'),
                review_count=42,
            )
        )
        if created:
            product.sizes.set(Size.objects.filter(name__in=['S', 'M', 'L', 'XL']))
            product.colors.set(Color.objects.filter(name__in=['Mustard', 'Pink', 'White']))
            product.tags.set(Tag.objects.filter(name__in=['Cotton', 'Casual']))

            with open(front, 'rb') as f:
                pi = ProductImage(product=product, alt_text=f"{product.name} - front",
                                   is_primary=True, order=1)
                pi.image.save('floral-kurti-front.png', ContentFile(f.read()), save=True)
            with open(back, 'rb') as f:
                pi = ProductImage(product=product, alt_text=f"{product.name} - back",
                                   is_primary=False, order=2)
                pi.image.save('floral-kurti-back.png', ContentFile(f.read()), save=True)

            for name, rating, comment in [
                ("Ayesha K.", 5, "Exactly like the photos — beautiful print and true to size."),
                ("Hina R.", 5, "Fabric quality is excellent, very comfortable for daily wear."),
            ]:
                Review.objects.create(product=product, customer_name=name, rating=rating, comment=comment)

            self.stdout.write("  Real reference product photos attached to catalog.")

    # ------------------------------------------------------------------
    def seed_hero_and_content(self):
        if not HeroSlide.objects.exists():
            hero_data = [
                ("Discover Your Style", "Premium Fashion For Every Occasion", "Shop Men", "/products/category/men/", "Shop Women", "/products/category/women/"),
                ("New Abaya Collection", "Elegant, Modest & Premium Quality", "Shop Abaya", "/products/category/abaya/", "View All", "/products/"),
                ("Season End Sale", "Up to 40% Off Selected Styles", "Shop Deals", "/products/deals/", "", ""),
            ]
            for i, (title, subtitle, btn1, link1, btn2, link2) in enumerate(hero_data, start=1):
                slide = HeroSlide(title=title, subtitle=subtitle, order=i,
                                   primary_button_text=btn1, primary_button_link=link1,
                                   secondary_button_text=btn2, secondary_button_link=link2)
                if self.make_images:
                    img = art.hero_banner_image(1600, 900, seed=f"hero-{i}")
                    fname, cfile = art.to_content_file(img, f"trch-hero-{i}.jpg")
                    slide.image.save(fname, cfile, save=False)
                slide.save()

        PromoBanner.objects.get_or_create(
            text="Free Delivery on Orders Above Rs. 5,000",
            defaults={'active': True, 'order': 1})

        if not Testimonial.objects.exists():
            testimonials = [
                ("Ayesha Khan", "Lahore", 5, "Beautiful abaya, exactly as shown in pictures. Ordering on WhatsApp was so easy!"),
                ("Bilal Ahmed", "Karachi", 5, "Great quality shalwar kameez, fits perfectly. Fast delivery too."),
                ("Sana Riaz", "Islamabad", 4, "Loved the kurti collection, will definitely shop again."),
                ("Hamza Tariq", "Faisalabad", 5, "Excellent customer service and premium fabric quality."),
                ("Zainab Sheikh", "Multan", 5, "The embroidered suit was stunning, received so many compliments."),
                ("Usman Ali", "Rawalpindi", 4, "Good pricing and reliable delivery across the city."),
            ]
            for name, city, rating, comment in testimonials:
                Testimonial.objects.create(customer_name=name, city=city, rating=rating, comment=comment)

        if self.make_images and not GalleryImage.objects.exists():
            gallery_items = [
                ('kameez', '#2b4c8c'), ('abaya', '#1a1a1a'), ('kurti', '#c8962c'), ('dress', '#7a1f2b'),
                ('abaya', '#6e1f2b'), ('kids_set', '#2f5d3a'), ('suit', '#d98ba0'), ('trousers', '#8a8a85'),
            ]
            for i, (shape, color) in enumerate(gallery_items, start=1):
                img = art.garment_image(shape, color, 500, 500, 'front', seed=f"gallery-{i}")
                fname, cfile = art.to_content_file(img, f"trch-gallery-{i}.jpg")
                gi = GalleryImage(order=i, caption=f"Style #{i}")
                gi.image.save(fname, cfile, save=True)

        AboutContent.load()
        self.stdout.write("  Hero slides, promo banner, testimonials, gallery and about content ready.")
