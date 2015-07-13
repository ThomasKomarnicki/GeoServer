# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0004_user_current_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='guessed_locations',
            field=models.CommaSeparatedIntegerField(max_length=64000, null=True),
        ),
    ]
