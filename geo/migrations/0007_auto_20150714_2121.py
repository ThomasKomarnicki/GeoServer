# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0006_auto_20150711_1540'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='average_guess_distance',
        ),
        migrations.RemoveField(
            model_name='location',
            name='best_guess_distance',
        ),
    ]
