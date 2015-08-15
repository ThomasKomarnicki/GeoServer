# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0012_user_auth_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='user',
        ),
        migrations.AddField(
            model_name='location',
            name='date_added',
            field=models.DateField(default=datetime.datetime(2015, 8, 12, 23, 27, 34, 8000, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='location',
            name='users',
            field=models.ManyToManyField(to='geo.User'),
        ),
    ]
