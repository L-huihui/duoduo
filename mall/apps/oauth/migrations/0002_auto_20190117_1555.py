# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-17 07:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='oauthqquser',
            old_name='updata_time',
            new_name='update_time',
        ),
    ]
