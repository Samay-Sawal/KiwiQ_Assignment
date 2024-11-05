from .models import Graph, Node, Edge, Run, RunOutput, GraphRunConfig
from django.core.exceptions import ValidationError
from collections import defaultdict, deque
import json

class GraphExecutor:
    def __init__(self, graph: Graph, run_config: GraphRunConfig):
        self.graph = graph
        self.run_config = run_config
        self.run = Run.objects.create(graph_run_config=run_config)
        self.run_outputs = {}
        self.toposort = []
        self.levels = {}

    def execute(self):
        enabled_nodes = set()
        if self.run_config.enable_list:
            enabled_nodes = set(self.run_config.enable_list)
        elif self.run_config.disable_list:
            all_nodes = set(node.node_id for node in self.graph.graph_nodes.all())
            enabled_nodes = all_nodes - set(self.run_config.disable_list)
        else:
            enabled_nodes = set(node.node_id for node in self.graph.graph_nodes.all())

        self.topological_sort()

        for node_id in self.toposort:
            if node_id not in enabled_nodes:
                continue
            node = Node.objects.get(graph=self.graph, node_id=node_id)
            if not node.in_edges.exists():
                outputs = {}
                if node_id in self.run_config.root_inputs:
                    for key, value in self.run_config.root_inputs[node_id].items():
                        outputs[key] = value
                if node_id in self.run_config.data_overwrites:
                    for key, value in self.run_config.data_overwrites[node_id].items():
                        outputs[key] = value
                RunOutput.objects.create(
                    run=self.run,
                    node=node,
                    data_out=outputs
                )
                self.run_outputs[node_id] = outputs
            else:
                inputs = {}
                if node_id in self.run_config.data_overwrites:
                    for key, value in self.run_config.data_overwrites[node_id].items():
                        inputs[key] = value
                for edge in node.in_edges.all():
                    src_node_id = edge.src_node.node_id
                    src_output_key = next(iter(edge.src_to_dst_data_keys))
                    dst_input_key = edge.src_to_dst_data_keys[src_output_key]
                    src_output = self.run_outputs.get(src_node_id, {}).get(src_output_key, None)
                    if src_output is None:
                        raise ValidationError(f"Missing input from node '{src_node_id}' for node '{node_id}'.")
                    if dst_input_key not in inputs:
                        inputs[dst_input_key] = src_output
                    else:
                        inputs[dst_input_key] += src_output 

                output = {}
                for key, value in node.data_out.items():
                    input_value = inputs.get(key, 0)
                    if isinstance(input_value, (int, float)) and isinstance(value, (int, float)):
                        output[key] = input_value + value
                    else:
                        output[key] = value 

                RunOutput.objects.create(
                    run=self.run,
                    node=node,
                    data_out=output
                )
                self.run_outputs[node_id] = output

        self.levels = self.get_level_wise_traversal()

        return self.run.run_id

    def topological_sort(self):
        in_degree = defaultdict(int)
        adj_list = defaultdict(list)
        for edge in Edge.objects.filter(src_node__graph=self.graph):
            adj_list[edge.src_node.node_id].append(edge.dst_node.node_id)
            in_degree[edge.dst_node.node_id] += 1

        queue = deque([node.node_id for node in self.graph.graph_nodes.all() if in_degree[node.node_id] == 0])
        sorted_order = []

        while queue:
            current = queue.popleft()
            sorted_order.append(current)
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != self.graph.graph_nodes.count():
            raise ValidationError("Graph contains a cycle.")

        self.toposort = sorted_order

    def get_level_wise_traversal(self):
        levels = defaultdict(list)
        node_levels = {}
        for node_id in self.toposort:
            node = Node.objects.get(graph=self.graph, node_id=node_id)
            if not node.in_edges.exists():
                node_levels[node_id] = 0
            else:
                node_levels[node_id] = max([node_levels[edge.src_node.node_id] for edge in node.in_edges.all()]) + 1
            levels[node_levels[node_id]].append(node_id)
        return levels
