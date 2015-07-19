# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0008_user_google_auth_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='google_auth_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='guessed_locations',
            field=models.CommaSeparatedIntegerField(max_length=64000, null=True, blank=True),
        ),
    ]
