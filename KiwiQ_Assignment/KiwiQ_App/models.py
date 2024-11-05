from django.db import models
from django.core.exceptions import ValidationError
import uuid
import json

def generate_run_id():
    return str(uuid.uuid4())

class Graph(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    nodes = models.JSONField(null=True, blank=True)  
    edges = models.JSONField(null=True, blank=True)  

    def __str__(self):
        return self.name

class Node(models.Model):
    node_id = models.CharField(max_length=255)
    data_in = models.JSONField()
    data_out = models.JSONField()
    graph = models.ForeignKey(Graph, related_name='graph_nodes', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('node_id', 'graph')

    def __str__(self):
        return self.node_id

class Edge(models.Model):
    src_node = models.ForeignKey(Node, related_name='out_edges', on_delete=models.CASCADE)
    dst_node = models.ForeignKey(Node, related_name='in_edges', on_delete=models.CASCADE)
    src_to_dst_data_keys = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('src_node', 'dst_node', 'src_to_dst_data_keys')

    def __str__(self):
        return f"{self.src_node.node_id} -> {self.dst_node.node_id}"

class GraphRunConfig(models.Model):
    graph = models.ForeignKey(Graph, related_name='run_configs', on_delete=models.CASCADE)
    root_inputs = models.JSONField()
    data_overwrites = models.JSONField(null=True, blank=True)
    enable_list = models.JSONField(null=True, blank=True)
    disable_list = models.JSONField(null=True, blank=True)

    def clean(self):
        if self.enable_list and self.disable_list:
            raise ValidationError("Cannot provide both enable_list and disable_list.")

    def __str__(self):
        return f"RunConfig for {self.graph.name} at {self.id}"

class Run(models.Model):
    run_id = models.CharField(max_length=36, unique=True, default=generate_run_id, editable=False)
    graph_run_config = models.ForeignKey(GraphRunConfig, related_name='runs', on_delete=models.CASCADE)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.run_id

class RunOutput(models.Model):
    run = models.ForeignKey(Run, related_name='outputs', on_delete=models.CASCADE)
    node = models.ForeignKey(Node, related_name='run_outputs', on_delete=models.CASCADE)
    data_out = models.JSONField()

    class Meta:
        unique_together = ('run', 'node')

    def __str__(self):
        return f"Output of {self.node.node_id} for run {self.run.run_id}"
