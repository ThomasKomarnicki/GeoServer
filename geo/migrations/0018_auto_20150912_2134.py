# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0017_auto_20150912_2114'),
    ]

    operations = [
        migrations.AddField(
            model_name='locationguess',
            name='date_added',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 12, 21, 34, 46, 932000)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='location',
            name='date_added',
            field=models.DateTimeField(),
        ),
    ]
