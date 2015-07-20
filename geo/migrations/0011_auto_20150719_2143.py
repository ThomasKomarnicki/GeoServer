# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0010_auto_20150719_2137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='lat',
            field=models.DecimalField(max_digits=20, decimal_places=17),
        ),
        migrations.AlterField(
            model_name='location',
            name='lon',
            field=models.DecimalField(max_digits=20, decimal_places=17),
        ),
        migrations.AlterField(
            model_name='locationguess',
            name='lat',
            field=models.DecimalField(max_digits=20, decimal_places=17),
        ),
        migrations.AlterField(
            model_name='locationguess',
            name='lon',
            field=models.DecimalField(max_digits=20, decimal_places=17),
        ),
    ]
