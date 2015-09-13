# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0016_locationguess_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='other_identifier',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
