# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-17 07:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20190116_1844'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ['-update_time'], 'verbose_name': '用户地址', 'verbose_name_plural': '用户地址'},
        ),
        migrations.RenameField(
            model_name='address',
            old_name='updata_time',
            new_name='update_time',
        ),
    ]