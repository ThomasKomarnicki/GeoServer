# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0003_user_guessed_locations'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='current_location',
            field=models.IntegerField(default=2),
            preserve_default=False,
        ),
    ]
