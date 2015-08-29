# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0015_user_total_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='locationguess',
            name='score',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
