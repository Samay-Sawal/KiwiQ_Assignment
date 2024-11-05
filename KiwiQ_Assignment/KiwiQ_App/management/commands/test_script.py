from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from KiwiQ_App.models import Graph, Node, Edge, GraphRunConfig, Run, RunOutput
from KiwiQ_App.serializers import GraphSerializer, GraphRunConfigSerializer
from KiwiQ_App.executor import GraphExecutor
from KiwiQ_App.validators import GraphValidator
from django.db import transaction
import json

class Command(BaseCommand):
    help = 'Test CRUD operations, run graph, and query outputs'

    def handle(self, *args, **options):
        # Step 1: Check and delete existing graph
        graph_name = "SampleGraph"
        print(f"Checking for existing graph with name '{graph_name}'...")
        existing_graphs = Graph.objects.filter(name=graph_name)
        if existing_graphs.exists():
            print(f"Found {existing_graphs.count()} existing graph(s) with name '{graph_name}'. Deleting...")
            existing_graphs.delete()
            print("Existing graph(s) deleted.")
        else:
            print("No existing graphs with that name. Proceeding.")

        # Step 2: Create a new graph
        graph_data = {
            "name": "SampleGraph",
            "description": "A sample DAG for testing",
            "nodes": [
                {
                    "node_id": "A",
                    "data_in": {},
                    "data_out": {"out1": 10},
                    "paths_in": [],
                    "paths_out": [{"src_node": "A", "dst_node": "B", "src_to_dst_data_keys": {"out1": "in1"}}]
                },
                {
                    "node_id": "B",
                    "data_in": {"in1": 0},
                    "data_out": {"out2": 20},
                    "paths_in": [{"src_node": "A", "dst_node": "B", "src_to_dst_data_keys": {"out1": "in1"}}],
                    "paths_out": [{"src_node": "B", "dst_node": "C", "src_to_dst_data_keys": {"out2": "in2"}}]
                },
                {
                    "node_id": "C",
                    "data_in": {"in2": 0},
                    "data_out": {"out3": 30},
                    "paths_in": [{"src_node": "B", "dst_node": "C", "src_to_dst_data_keys": {"out2": "in2"}}],
                    "paths_out": []
                }
            ],
            "edges": [
                {"src_node": "A", "dst_node": "B", "src_to_dst_data_keys": {"out1": "in1"}},
                {"src_node": "B", "dst_node": "C", "src_to_dst_data_keys": {"out2": "in2"}}
            ]
        }

        print("Creating graph...")
        try:
            with transaction.atomic():
                graph = GraphSerializer.deserialize(graph_data)
            print(f"Graph '{graph.name}' created with ID: {graph.id}")
        except ValidationError as e:
            print(f"Error creating graph: {e}")
            return
        except Exception as e:
            print(f"Unexpected error creating graph: {e}")
            return

        # Step 3: Retrieve the graph
        print("Retrieving graph...")
        serialized_graph = GraphSerializer.serialize(graph)
        print(json.dumps(serialized_graph, indent=2))

        # Step 4: Update the graph (Add a new node D)
        print("Updating graph by adding node D...")
        updated_graph_data = serialized_graph.copy()
        updated_graph_data['nodes'].append({
            "node_id": "D",
            "data_in": {"in3": 0},
            "data_out": {"out4": 40},
            "paths_in": [{"src_node": "C", "dst_node": "D", "src_to_dst_data_keys": {"out3": "in3"}}],
            "paths_out": []
        })
        updated_graph_data['edges'].append({"src_node": "C", "dst_node": "D", "src_to_dst_data_keys": {"out3": "in3"}})
        try:
            with transaction.atomic():
                # Update the existing graph by passing the graph instance to deserialize
                graph = GraphSerializer.deserialize(updated_graph_data, graph=graph)
            print("Graph updated successfully.")
        except ValidationError as e:
            print(f"Error updating graph: {e}")
            return
        except Exception as e:
            print(f"Unexpected error updating graph: {e}")
            return

        # Step 5: Validate the graph
        print("Validating graph...")
        try:
            GraphValidator.validate_graph(graph)
            print("Graph validation passed.")
        except ValidationError as e:
            print(f"Graph validation failed: {e}")
            return
        except Exception as e:
            print(f"Unexpected error during validation: {e}")
            return

        # Step 6: Run the graph
        print("Running the graph...")
        run_config_data = {
            "root_inputs": {
                "A": {"out1": 100}
            },
            "data_overwrites": {
                "B": {"in1": 200}
            },
            "enable_list": ["A", "B", "C", "D"],
            # "disable_list": []  # Ensure this is not provided
        }
        try:
            run_config = GraphRunConfigSerializer.deserialize(graph, run_config_data)
            executor = GraphExecutor(graph, run_config)
            run_id = executor.execute()
            print(f"Graph executed successfully. Run ID: {run_id}")
        except ValidationError as e:
            print(f"Error running graph: {e}")
            return
        except Exception as e:
            print(f"Unexpected error running graph: {e}")
            return

        # Step 7: Query run outputs
        print("Querying run outputs...")
        try:
            run = Run.objects.get(run_id=run_id)
            outputs = RunOutput.objects.filter(run=run)
            for output in outputs:
                print(f"Node {output.node.node_id} output: {output.data_out}")
        except Run.DoesNotExist:
            print("Run not found.")
        except Exception as e:
            print(f"Error querying run outputs: {e}")
            return

        # Step 8: Retrieve leaf outputs
        print("Retrieving leaf outputs...")
        try:
            # Leaf node is D
            run_output = RunOutput.objects.get(run=run, node__node_id="D")
            print(f"Leaf node D output: {run_output.data_out}")
        except RunOutput.DoesNotExist:
            print("Run output for node D not found.")
        except Exception as e:
            print(f"Error retrieving leaf outputs: {e}")

        # Step 9: Get islands
        print("Getting islands...")
        try:
            # For Option 1, islands are already handled by validation (no disconnected components)
            islands = [["A", "B", "C", "D"]]
            print(f"Islands: {islands}")
        except Exception as e:
            print(f"Error getting islands: {e}")

        # Step 10: Get topological sort
        print("Topological sort of the graph:")
        try:
            toposort = executor.topological_sort()
            print(toposort)
        except ValidationError as e:
            print(f"Error getting toposort: {e}")
        except Exception as e:
            print(f"Unexpected error getting toposort: {e}")

        # Step 11: Get level-wise traversal
        print("Level-wise traversal:")
        try:
            levels = executor.levels
            sorted_levels = dict(sorted(levels.items()))
            print(json.dumps({"level_traversal": sorted_levels}, indent=2))
        except Exception as e:
            print(f"Error getting level traversal: {e}")
