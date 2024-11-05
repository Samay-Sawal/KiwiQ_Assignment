# Generated by Django 5.1.2 on 2024-11-05 08:51

import KiwiQ_App.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Graph',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('nodes', models.JSONField()),
                ('edges', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='GraphRunConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('root_inputs', models.JSONField()),
                ('data_overwrites', models.JSONField(blank=True, null=True)),
                ('enable_list', models.JSONField(blank=True, null=True)),
                ('disable_list', models.JSONField(blank=True, null=True)),
                ('graph', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='run_configs', to='KiwiQ_App.graph')),
            ],
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('node_id', models.CharField(max_length=255, unique=True)),
                ('data_in', models.JSONField()),
                ('data_out', models.JSONField()),
                ('graph', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='graph_nodes', to='KiwiQ_App.graph')),
            ],
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('run_id', models.CharField(default=KiwiQ_App.models.generate_run_id, editable=False, max_length=36, unique=True)),
                ('executed_at', models.DateTimeField(auto_now_add=True)),
                ('graph_run_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='KiwiQ_App.graphrunconfig')),
            ],
        ),
        migrations.CreateModel(
            name='Edge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src_to_dst_data_keys', models.JSONField(blank=True, null=True)),
                ('dst_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='in_edges', to='KiwiQ_App.node')),
                ('src_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='out_edges', to='KiwiQ_App.node')),
            ],
            options={
                'unique_together': {('src_node', 'dst_node', 'src_to_dst_data_keys')},
            },
        ),
        migrations.CreateModel(
            name='RunOutput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_out', models.JSONField()),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='run_outputs', to='KiwiQ_App.node')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='KiwiQ_App.run')),
            ],
            options={
                'unique_together': {('run', 'node')},
            },
        ),
    ]
