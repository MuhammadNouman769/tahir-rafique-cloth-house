import uuid
from django.db import migrations, models


def fill_tokens(apps, schema_editor):
    Subscriber = apps.get_model('core', 'NewsletterSubscriber')
    for sub in Subscriber.objects.all():
        sub.token = uuid.uuid4()
        sub.save(update_fields=['token'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),   # jo aap ki file mein pehle se likha hai wohi rakhein
    ]

    operations = [
        migrations.AddField(
            model_name='newslettersubscriber',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        # Step 1: pehle bina unique ke, khali (null) token
        migrations.AddField(
            model_name='newslettersubscriber',
            name='token',
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: har purane subscriber ko alag token dein
        migrations.RunPython(fill_tokens, migrations.RunPython.noop),
        # Step 3: ab unique lagayein
        migrations.AlterField(
            model_name='newslettersubscriber',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]