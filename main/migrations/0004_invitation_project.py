# Generated by Django 4.1.7 on 2023-04-19 14:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_remove_projectstaff_project_remove_projectstaff_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='project',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='main.project'),
            preserve_default=False,
        ),
    ]