# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0011_auto_20150719_2143'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auth_token',
            field=models.CharField(default='weeueueue', max_length=256),
            preserve_default=False,
        ),
    ]
