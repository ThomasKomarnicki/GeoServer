# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lat', models.DecimalField(max_digits=15, decimal_places=10)),
                ('lon', models.DecimalField(max_digits=15, decimal_places=10)),
            ],
        ),
        migrations.CreateModel(
            name='LocationGuess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lat', models.DecimalField(max_digits=15, decimal_places=10)),
                ('lon', models.DecimalField(max_digits=15, decimal_places=10)),
                ('location', models.ForeignKey(to='geo.Location')),
            ],
        ),
    ]
