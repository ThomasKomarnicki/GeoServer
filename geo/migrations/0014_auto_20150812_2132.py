# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0013_auto_20150812_1927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='date_added',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
