# Generated by Django 5.2.4 on 2025-07-05 18:51

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_remove_brandproduct_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandcampaign',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='generatedad',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='brandcampaign',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='campaign_logos/'),
        ),
        migrations.AlterField(
            model_name='brandproduct',
            name='category',
            field=models.CharField(default='General', max_length=100),
        ),
        migrations.AlterField(
            model_name='brandproduct',
            name='sub_category',
            field=models.CharField(default='Uncategorized', max_length=100),
        ),
        migrations.AlterField(
            model_name='generatedad',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='generated_ads/'),
        ),
        migrations.AlterField(
            model_name='generatedad',
            name='platform',
            field=models.CharField(choices=[('instagram', 'Instagram'), ('facebook', 'Facebook'), ('twitter', 'Twitter'), ('linkedin', 'LinkedIn'), ('pinterest', 'Pinterest')], default='instagram', max_length=20),
        ),
        migrations.AlterField(
            model_name='generatedad',
            name='source_post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.likedpost'),
        ),
    ]
