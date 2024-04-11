# Generated by Django 5.0.3 on 2024-04-11 04:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_member_height_member_weight'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('diastolic_bp', models.IntegerField(verbose_name='Diastolic Blood Pressure')),
                ('systolic_bp', models.IntegerField(verbose_name='Systolic Blood Pressure')),
                ('height', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Height (cm)')),
                ('weight', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Weight (kg)')),
                ('fitness_goal', models.CharField(blank=True, max_length=255, verbose_name='Fitness Goal')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stats', to='myapp.member')),
            ],
        ),
    ]
