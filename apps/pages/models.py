from django.db import models


class AboutContent(models.Model):
    """Singleton for the About Us page's editable content."""
    brand_story = models.TextField(default=(
        "Tahir Rafique Cloth House started with a simple idea: everyone deserves to feel "
        "confident in what they wear. What began as a single family-run shop has grown into "
        "a trusted name in premium men's, women's, children's and abaya fashion across Pakistan."
    ))
    mission = models.TextField(default=(
        "To make premium quality clothing accessible and affordable, while giving every "
        "customer a shopping experience built on trust and care."
    ))
    vision = models.TextField(default=(
        "To become Pakistan's most loved fashion destination, known for quality, "
        "authenticity and outstanding customer service."
    ))
    quality_statement = models.TextField(default=(
        "Every piece is carefully selected and quality-checked before it reaches you, "
        "using premium fabrics and expert stitching."
    ))
    years_experience = models.PositiveIntegerField(default=12)
    happy_customers = models.PositiveIntegerField(default=25000)
    products_sold = models.PositiveIntegerField(default=80000)
    cities_served = models.PositiveIntegerField(default=40)
    team_image = models.ImageField(upload_to='pages/', blank=True, null=True)

    class Meta:
        verbose_name = "About Page Content"
        verbose_name_plural = "About Page Content"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "About Page Content"
