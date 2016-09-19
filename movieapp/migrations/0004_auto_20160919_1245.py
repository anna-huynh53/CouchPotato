# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-19 02:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movieapp', '0003_user_friends'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='toWatchList',
            field=models.ManyToManyField(related_name='toWatch', to='movieapp.Movie'),
        ),
        migrations.AlterField(
            model_name='user',
            name='watchedList',
            field=models.ManyToManyField(related_name='watched', to='movieapp.Movie'),
        ),
    ]