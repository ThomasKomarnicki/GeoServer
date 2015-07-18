# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0007_auto_20150714_2121'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='google_auth_id',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
