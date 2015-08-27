# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0014_auto_20150812_2132'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='total_score',
            field=models.IntegerField(default=0),
        ),
    ]
