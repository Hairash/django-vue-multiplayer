# Generated by Django 4.2.1 on 2024-01-20 00:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_game_deck_game_table_player_hand_delete_card'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='state',
            field=models.CharField(choices=[('not_started', 'Not started'), ('game', 'Game'), ('wait', 'Wait')], default='not_started', max_length=15),
        ),
    ]
