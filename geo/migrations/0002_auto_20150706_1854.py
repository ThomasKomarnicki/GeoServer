# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('other_identifier', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='location',
            name='average_guess_distance',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='location',
            name='best_guess_distance',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='locationguess',
            name='distance',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='location',
            name='lat',
            field=models.DecimalField(max_digits=15, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='location',
            name='lon',
            field=models.DecimalField(max_digits=15, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='locationguess',
            name='lat',
            field=models.DecimalField(max_digits=15, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='locationguess',
            name='lon',
            field=models.DecimalField(max_digits=15, decimal_places=8),
        ),
        migrations.AddField(
            model_name='location',
            name='user',
            field=models.ForeignKey(to='geo.User', null=True),
        ),
        migrations.AddField(
            model_name='locationguess',
            name='user',
            field=models.ForeignKey(to='geo.User', null=True),
        ),
    ]
