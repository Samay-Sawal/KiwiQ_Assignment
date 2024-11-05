import json
from .models import Graph, Node, Edge, GraphRunConfig, Run, RunOutput
from django.core.exceptions import ValidationError
from .validators import GraphValidator
from collections import Counter

class GraphSerializer:
    def serialize(graph):
        return {
            "id": graph.id,
            "name": graph.name,
            "description": graph.description,
            "nodes": [NodeSerializer.serialize_node(node) for node in graph.graph_nodes.all()],
            "edges": [EdgeSerializer.serialize_edge(edge) for edge in Edge.objects.filter(src_node__graph=graph)]
        }

    def deserialize(data, graph=None):
        try:
            name = data['name']
            description = data.get('description', '')
            nodes_data = data['nodes']
            edges_data = data['edges']
        except KeyError as e:
            raise ValidationError(f"Missing field in graph data: {e}")

        node_ids = [node['node_id'] for node in nodes_data]
        duplicates = [item for item, count in Counter(node_ids).items() if count > 1]
        if duplicates:
            raise ValidationError(f"Duplicate node_id(s) found within the graph: {', '.join(duplicates)}")

        if graph is None:
            graph = Graph.objects.create(
                name=name,
                description=description
            )
        else:
            graph.description = description
            graph.save()

        if graph.graph_nodes.exists():
            graph.graph_nodes.all().delete()
            Edge.objects.filter(src_node__graph=graph).delete()

        node_map = {}
        for node_data in nodes_data:
            node = Node.objects.create(
                node_id=node_data['node_id'],
                data_in=node_data.get('data_in', {}),
                data_out=node_data.get('data_out', {}),
                graph=graph
            )
            node_map[node.node_id] = node

        for edge_data in edges_data:
            src_id = edge_data['src_node']
            dst_id = edge_data['dst_node']
            src_to_dst_data_keys = edge_data.get('src_to_dst_data_keys', {})
            src_node = node_map.get(src_id)
            dst_node = node_map.get(dst_id)
            if not src_node or not dst_node:
                raise ValidationError(f"Invalid edge with src: {src_id}, dst: {dst_id}")
            Edge.objects.create(
                src_node=src_node,
                dst_node=dst_node,
                src_to_dst_data_keys=src_to_dst_data_keys
            )

        GraphValidator.validate_graph(graph)

        return graph

class NodeSerializer:
    def serialize_node(node):
        return {
            "node_id": node.node_id,
            "data_in": node.data_in,
            "data_out": node.data_out,
            "paths_in": [
                {
                    "src_node": edge.src_node.node_id,
                    "dst_node": edge.dst_node.node_id,
                    "src_to_dst_data_keys": edge.src_to_dst_data_keys
                }
                for edge in node.in_edges.all()
            ],
            "paths_out": [
                {
                    "src_node": edge.src_node.node_id,
                    "dst_node": edge.dst_node.node_id,
                    "src_to_dst_data_keys": edge.src_to_dst_data_keys
                }
                for edge in node.out_edges.all()
            ]
        }

class EdgeSerializer:
    def serialize_edge(edge):
        return {
            "src_node": edge.src_node.node_id,
            "dst_node": edge.dst_node.node_id,
            "src_to_dst_data_keys": edge.src_to_dst_data_keys
        }

class GraphRunConfigSerializer:
    def deserialize(graph: Graph, data: dict):
        try:
            root_inputs = data.get('root_inputs', {})
            data_overwrites = data.get('data_overwrites', {})
            enable_list = data.get('enable_list', [])
            disable_list = data.get('disable_list', [])
        except KeyError as e:
            raise ValidationError(f"Missing field in run configuration data: {e}")

        if enable_list and disable_list:
            raise ValidationError("Cannot provide both enable_list and disable_list simultaneously.")


        run_config = GraphRunConfig.objects.create(
            graph=graph,
            root_inputs=root_inputs,
            data_overwrites=data_overwrites,
            enable_list=enable_list,
            disable_list=disable_list
        )

        return run_config

class RunSerializer:
    def serialize(run):
        return {
            "run_id": run.run_id,
            "graph_run_config": run.graph_run_config.id,
        }

    def deserialize(data):
        try:
            graph_run_config_id = data['graph_run_config']
        except KeyError as e:
            raise ValidationError(f"Missing field in run data: {e}")

        try:
            graph_run_config = GraphRunConfig.objects.get(id=graph_run_config_id)
        except GraphRunConfig.DoesNotExist:
            raise ValidationError(f"GraphRunConfig with id {graph_run_config_id} does not exist.")

        run = Run.objects.create(
            graph_run_config=graph_run_config
        )
        return run

class RunOutputSerializer:
    def serialize(run_output):
        return {
            "id": run_output.id,
            "run": run_output.run.run_id,
            "node": run_output.node.node_id,
            "data_out": run_output.data_out
        }

    def deserialize(data):
        try:
            run_id = data['run']
            node_id = data['node']
            data_out = data['data_out']
        except KeyError as e:
            raise ValidationError(f"Missing field in run output data: {e}")

        try:
            run = Run.objects.get(run_id=run_id)
        except Run.DoesNotExist:
            raise ValidationError(f"Run with run_id {run_id} does not exist.")

        try:
            node = Node.objects.get(node_id=node_id, graph=run.graph_run_config.graph)
        except Node.DoesNotExist:
            raise ValidationError(f"Node with node_id {node_id} does not exist in the graph associated with the run.")

        run_output = RunOutput.objects.create(
            run=run,
            node=node,
            data_out=data_out
        )
        return run_output
