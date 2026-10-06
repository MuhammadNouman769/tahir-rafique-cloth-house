"""Fills the store with realistic DUMMY data so the dashboard has something to show:
customers, orders (spread over the last ~6 months), reviews, contact messages, subscribers.

    python manage.py seed_demo              # add demo data
    python manage.py seed_demo --reset      # remove old demo data first, then add fresh
    python manage.py seed_demo --clear      # only remove demo data

Demo records are easy to recognise and remove:
  * customers  -> username starts with "demo_"
  * orders     -> order number starts with "TRCH-D"
  * reviews    -> comment ends with a zero-width marker (invisible on the site)
  * messages / subscribers -> e-mail ends with "@example.com"
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Profile
from apps.contact.models import ContactMessage
from apps.core.models import NewsletterSubscriber, SiteSettings
from apps.orders.models import Order, OrderItem
from apps.products.models import Product, Review
from apps.dashboard.helpers import recalc_product_rating

MARK = '\u200b'   # zero-width space: marks demo reviews without being visible

FIRST = ['Ahmed', 'Ali', 'Hassan', 'Usman', 'Bilal', 'Hamza', 'Zain', 'Faisal', 'Imran', 'Kamran', 'Saad',
         'Ayesha', 'Fatima', 'Sana', 'Hina', 'Maryam', 'Zainab', 'Iqra', 'Nida', 'Sadia', 'Rabia', 'Areeba',
         'Mehwish', 'Laiba', 'Noor', 'Amna', 'Hira', 'Farah', 'Saima', 'Bushra']
LAST = ['Khan', 'Malik', 'Butt', 'Sheikh', 'Raza', 'Qureshi', 'Siddiqui', 'Chaudhry', 'Mirza', 'Abbasi',
        'Hussain', 'Javed', 'Iqbal', 'Ansari', 'Awan', 'Rana', 'Niazi', 'Gill', 'Baig', 'Zaidi']
CITIES = [('Islamabad', 30), ('Rawalpindi', 18), ('Lahore', 18), ('Karachi', 12), ('Peshawar', 6),
          ('Faisalabad', 5), ('Multan', 4), ('Sialkot', 3), ('Quetta', 2), ('Gujranwala', 2)]
AREAS = {'Islamabad': ['F-10', 'G-11', 'I-8', 'E-11', 'Blue Area', 'DHA Phase 2', 'Bahria Town'],
         'Rawalpindi': ['Saddar', 'Satellite Town', 'Chaklala', 'Bahria Town'],
         'Lahore': ['Gulberg', 'DHA', 'Johar Town', 'Model Town'], 'Karachi': ['Clifton', 'Gulshan', 'North Nazimabad']}
STATUS_BY_AGE = [  # (max age in days, weights for pending, confirmed, processing, shipped, delivered, cancelled)
    (3, [40, 25, 15, 12, 3, 5]), (10, [8, 12, 15, 25, 35, 5]), (10_000, [0, 0, 1, 2, 88, 9])]
REVIEW_TEXT = {
    5: ['Beautiful fabric and the stitching is perfect. Exactly like the pictures!', 'Absolutely love it. Got so many compliments.',
        'Superb quality for the price. Delivery was quick too.', 'Perfect fit and very comfortable. Will order again.',
        'Premium feel, colour is exactly as shown. Highly recommended.', 'Bohat zabardast quality hai, family ne bhi pasand kiya.'],
    4: ['Very good quality, slightly loose on the sleeves but overall happy.', 'Nice product. Delivery took a day longer than expected.',
        'Good value for money. Colour a shade lighter than the photo.', 'Fabric is soft and fits well. Would buy again.'],
    3: ['Decent for the price, but fabric is thinner than I expected.', 'Okay product. Size runs a little small, order one size up.'],
    2: ['Colour faded a bit after the first wash.', 'Stitching on the hem was loose. Support helped but took time.'],
}
SUBJECTS = [('Bulk order enquiry', 'Hello, I need 25 shalwar kameez sets for a family wedding. Do you offer a bulk discount and can you deliver within 10 days?'),
            ('Size exchange', 'I received my kurti but the size is slightly small. Can I exchange it for the next size up?'),
            ('Order status', 'I placed an order three days ago and have not received a confirmation call yet. Please update me.'),
            ('Custom stitching', 'Do you offer custom stitching or alterations for abayas? I need a specific length.'),
            ('Wholesale prices', 'We run a boutique in Faisalabad and are interested in wholesale prices for your women collection.'),
            ('Delivery to Karachi', 'How many days does delivery take to Karachi and what are the charges?'),
            ('Return policy', 'What is your return policy if the product does not match the picture?'),
            ('Product availability', 'Is the embroidered abaya available in size XL? The site shows only M and L.')]


def weighted(pairs):
    return random.choices([p[0] for p in pairs], weights=[p[1] for p in pairs])[0]


class Command(BaseCommand):
    help = 'Create (or remove) demo customers, orders, reviews, messages and subscribers.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Remove existing demo data, then create new.')
        parser.add_argument('--clear', action='store_true', help='Only remove demo data.')
        parser.add_argument('--orders', type=int, default=260)
        parser.add_argument('--customers', type=int, default=70)
        parser.add_argument('--seed', type=int, default=None, help='Random seed for repeatable data.')

    def handle(self, *args, **o):
        if o['seed'] is not None:
            random.seed(o['seed'])
        if o['reset'] or o['clear']:
            self.clear()
            if o['clear']:
                return
        elif Order.objects.filter(order_number__startswith='TRCH-D').exists():
            self.stdout.write(self.style.WARNING('Demo data already exists. Use --reset to replace it.'))
            return
        products = list(Product.objects.filter(available=True).prefetch_related('sizes', 'colors'))
        if not products:
            self.stderr.write('No products found. Run `python manage.py seed_data` first.')
            return
        with transaction.atomic():
            users = self.make_customers(o['customers'])
            n = self.make_orders(o['orders'], users, products)
            r = self.make_reviews(products)
            m = self.make_messages()
            s = self.make_subscribers()
        self.stdout.write(self.style.SUCCESS(
            f'Done: {len(users)} customers, {n} orders, {r} reviews, {m} messages, {s} subscribers.'))

    # ---------- cleanup ----------
    def clear(self):
        Order.objects.filter(order_number__startswith='TRCH-D').delete()
        affected = set(Review.objects.filter(comment__endswith=MARK).values_list('product_id', flat=True))
        Review.objects.filter(comment__endswith=MARK).delete()
        for p in Product.objects.filter(pk__in=affected):
            recalc_product_rating(p)
        User.objects.filter(username__startswith='demo_').delete()
        ContactMessage.objects.filter(email__endswith='@example.com').delete()
        NewsletterSubscriber.objects.filter(email__endswith='@example.com').delete()
        self.stdout.write('Old demo data removed.')

    # ---------- builders ----------
    def phone(self):
        return f"03{random.choice([0, 1, 2, 3, 4])}{random.randint(0, 9)}{random.randint(1000000, 9999999)}"

    def make_customers(self, count):
        users, seen = [], set()
        while len(users) < count:
            fn, ln = random.choice(FIRST), random.choice(LAST)
            uname = f"demo_{fn}{ln}{random.randint(1, 99)}".lower()
            if uname in seen:
                continue
            seen.add(uname)
            city = weighted(CITIES)
            u = User.objects.create_user(username=uname, email=f"{uname[5:]}@example.com", password='demo12345',
                                         first_name=fn, last_name=ln)
            Profile.objects.create(user=u, phone=self.phone(), city=city,
                                   address=f"House {random.randint(1, 120)}, Street {random.randint(1, 30)}, "
                                           f"{random.choice(AREAS.get(city, ['Main Road']))}")
            User.objects.filter(pk=u.pk).update(date_joined=timezone.now() - timedelta(days=random.randint(1, 190)))
            users.append(u)
        return users

    def pick_status(self, age_days):
        for limit, w in STATUS_BY_AGE:
            if age_days <= limit:
                return random.choices(['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'], weights=w)[0]

    def make_orders(self, count, users, products):
        cfg = SiteSettings.load()
        now = timezone.now()
        # a handful of loyal repeat buyers + guests who order by phone only
        loyal = random.sample(users, min(12, len(users)))
        guests = [(f"{random.choice(FIRST)} {random.choice(LAST)}", self.phone(), weighted(CITIES)) for _ in range(25)]
        made = 0
        for i in range(1, count + 1):
            age = random.randint(0, 3) if random.random() < 0.12 else int(random.triangular(0, 185, 70))  # recent-heavy
            when = now - timedelta(days=age, hours=random.choice([9, 10, 11, 13, 15, 18, 19, 20, 21, 22]) - now.hour,
                                   minutes=random.randint(0, 59))
            if when > now:
                when -= timedelta(days=1)   # never create orders in the future
            if random.random() < 0.55:
                u = random.choice(loyal) if random.random() < 0.45 else random.choice(users)
                if u.date_joined > when:
                    User.objects.filter(pk=u.pk).update(date_joined=when - timedelta(days=1))
                name, phone, city = u.get_full_name(), u.profile.phone, u.profile.city
                email, address, customer = u.email, u.profile.address, u
            else:
                name, phone, city = random.choice(guests)
                email, customer = '', None
                address = f"House {random.randint(1, 120)}, Street {random.randint(1, 30)}, {random.choice(AREAS.get(city, ['Main Road']))}"
            status = self.pick_status(age)
            order = Order.objects.create(
                order_number=f"TRCH-D{i:07d}", customer=customer, full_name=name, phone=phone, whatsapp=phone,
                email=email, city=city, area=random.choice(AREAS.get(city, [''])), address=address,
                notes=random.choice(['', '', '', 'Please call before delivery.', 'Gift wrap if possible.', 'Deliver after 5 PM.']),
                status=status)
            subtotal = Decimal('0')
            for p in random.sample(products, random.choices([1, 2, 3, 4], weights=[50, 30, 14, 6])[0]):
                size = random.choice(list(p.sizes.all())).name if p.sizes.all() else ''
                color = random.choice(list(p.colors.all())).name if p.colors.all() else ''
                qty = random.choices([1, 2, 3], weights=[78, 17, 5])[0]
                OrderItem.objects.create(order=order, product=p, product_name=p.name, price=p.current_price,
                                         quantity=qty, size=size, color=color)
                subtotal += p.current_price * qty
            delivery = Decimal('0') if subtotal >= cfg.free_delivery_threshold else cfg.delivery_charges
            Order.objects.filter(pk=order.pk).update(subtotal=subtotal, delivery_charges=delivery,
                                                     total=subtotal + delivery, created_at=when,
                                                     updated_at=when + timedelta(hours=random.randint(1, 48)))
            made += 1
        return made

    def make_reviews(self, products):
        made = 0
        for p in products:
            for _ in range(random.choices([0, 1, 2, 3, 4], weights=[10, 25, 30, 22, 13])[0]):
                rating = random.choices([5, 4, 3, 2], weights=[58, 28, 10, 4])[0]
                r = Review.objects.create(
                    product=p, customer_name=f"{random.choice(FIRST)} {random.choice(LAST[:10])[0]}.",
                    rating=rating, comment=random.choice(REVIEW_TEXT[rating]) + MARK,
                    approved=random.random() > 0.12)
                Review.objects.filter(pk=r.pk).update(created_at=timezone.now() - timedelta(days=random.randint(0, 150)))
                made += 1
            recalc_product_rating(p)
        return made

    def make_messages(self):
        for subject, body in SUBJECTS:
            fn, ln = random.choice(FIRST), random.choice(LAST)
            m = ContactMessage.objects.create(
                name=f"{fn} {ln}", email=f"{fn}.{ln}{random.randint(1, 99)}@example.com".lower(),
                phone=self.phone(), subject=subject, message=body, is_read=random.random() < 0.45)
            ContactMessage.objects.filter(pk=m.pk).update(created_at=timezone.now() - timedelta(days=random.randint(0, 25), hours=random.randint(0, 20)))
        return len(SUBJECTS)

    def make_subscribers(self):
        n = 0
        for _ in range(40):
            email = f"{random.choice(FIRST)}.{random.choice(LAST)}{random.randint(1, 999)}@example.com".lower()
            s, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                NewsletterSubscriber.objects.filter(pk=s.pk).update(subscribed_at=timezone.now() - timedelta(days=random.randint(0, 120)))
                n += 1
        return n
