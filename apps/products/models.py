from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children',
                                on_delete=models.CASCADE)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})

    @property
    def is_top_level(self):
        return self.parent_id is None


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


SIZE_CHOICES = [
    ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
]

COLOR_CHOICES = [
    ('Black', 'Black'), ('White', 'White'), ('Blue', 'Blue'), ('Red', 'Red'),
    ('Green', 'Green'), ('Brown', 'Brown'), ('Grey', 'Grey'), ('Maroon', 'Maroon'),
    ('Navy', 'Navy'), ('Beige', 'Beige'), ('Pink', 'Pink'), ('Mustard', 'Mustard'),
]


class Size(models.Model):
    name = models.CharField(max_length=10, choices=SIZE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=20, choices=COLOR_CHOICES, unique=True)
    hex_code = models.CharField(max_length=7, default='#000000',
                                 help_text="Hex color for swatch, e.g. #1a1a1a")

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=40, unique=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, related_name='products', null=True, blank=True,
                               on_delete=models.SET_NULL)
    tags = models.ManyToManyField(Tag, related_name='products', blank=True)

    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(0)])

    stock_quantity = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)

    featured = models.BooleanField(default=False)
    bestseller = models.BooleanField(default=False)
    new_arrival = models.BooleanField(default=False)
    deal_of_day = models.BooleanField(default=False)

    sizes = models.ManyToManyField(Size, related_name='products', blank=True)
    colors = models.ManyToManyField(Color, related_name='products', blank=True)

    material = models.CharField(max_length=200, blank=True, default="Premium fabric blend")
    care_instructions = models.TextField(
        blank=True, default="Machine wash cold with like colors. Do not bleach. Tumble dry low.")

    rating = models.DecimalField(max_digits=2, decimal_places=1, default=Decimal('4.5'),
                                  validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def current_price(self):
        return self.sale_price if self.is_on_sale else self.price

    @property
    def discount_percentage(self):
        if self.is_on_sale and self.price > 0:
            return int(round((self.price - self.sale_price) / self.price * 100))
        return 0

    @property
    def in_stock(self):
        return self.available and self.stock_quantity > 0

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()

    @property
    def secondary_image(self):
        imgs = list(self.images.all()[:2])
        return imgs[1] if len(imgs) > 1 else None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=150, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} image #{self.order}"


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.rating}★ by {self.customer_name}"
