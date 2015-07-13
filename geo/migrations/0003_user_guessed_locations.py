# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0002_auto_20150706_1854'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='guessed_locations',
            field=models.CommaSeparatedIntegerField(default='', max_length=64000),
            preserve_default=False,
        ),
    ]
