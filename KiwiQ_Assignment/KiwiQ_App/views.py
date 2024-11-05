from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from .serializers import GraphSerializer, GraphRunConfigSerializer, RunOutputSerializer
from .models import Graph, Node, Edge, GraphRunConfig, Run, RunOutput
from django.core.exceptions import ValidationError
from .executor import GraphExecutor
from .validators import GraphValidator
import json

def create_graph(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        graph = GraphSerializer.deserialize(data)
        return JsonResponse({"message": "Graph created successfully", "graph_id": graph.id}, status=201)
    except (ValidationError, KeyError) as e:
        return HttpResponseBadRequest(json.dumps({"error": str(e)}), content_type="application/json")

def get_graph(request, graph_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        graph = Graph.objects.get(id=graph_id)
        serialized_graph = GraphSerializer.serialize(graph)
        return JsonResponse(serialized_graph, status=200)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")

def update_graph(request, graph_id):
    if request.method != 'PUT':
        return HttpResponseNotAllowed(['PUT'])
    try:
        graph = Graph.objects.get(id=graph_id)
        data = json.loads(request.body)
        graph.graph_nodes.all().delete()
        Edge.objects.filter(src_node__graph=graph).delete()
        graph = GraphSerializer.deserialize(data)
        return JsonResponse({"message": "Graph updated successfully"}, status=200)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")
    except (ValidationError, KeyError) as e:
        return HttpResponseBadRequest(json.dumps({"error": str(e)}), content_type="application/json")

def delete_graph(request, graph_id):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])
    try:
        graph = Graph.objects.get(id=graph_id)
        graph.delete()
        return JsonResponse({"message": "Graph deleted successfully"}, status=200)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")

def run_graph(request, graph_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        graph = Graph.objects.get(id=graph_id)
        data = json.loads(request.body)
        run_config = GraphRunConfigSerializer.deserialize(graph, data)
        GraphValidator.validate_graph(graph)
        executor = GraphExecutor(graph, run_config)
        run_id = executor.execute()
        return JsonResponse({"run_id": run_id}, status=201)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")
    except (ValidationError, KeyError) as e:
        return HttpResponseBadRequest(json.dumps({"error": str(e)}), content_type="application/json")

def get_run_output(request, run_id, node_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        run = Run.objects.get(run_id=run_id)
        node = Node.objects.get(node_id=node_id, graph=run.graph_run_config.graph)
        run_output = RunOutput.objects.get(run=run, node=node)
        serialized_output = RunOutputSerializer.serialize(run_output)
        return JsonResponse(serialized_output, status=200)
    except Run.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Run not found"}), content_type="application/json")
    except Node.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Node not found"}), content_type="application/json")
    except RunOutput.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Run output not found for the node"}), content_type="application/json")

def get_leaf_outputs(request, run_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        run = Run.objects.get(run_id=run_id)
        graph = run.graph_run_config.graph
        # Leaf nodes have no outgoing edges
        leaf_nodes = graph.graph_nodes.filter(out_edges__isnull=True)
        outputs = RunOutput.objects.filter(run=run, node__in=leaf_nodes)
        serialized_outputs = [RunOutputSerializer.serialize(output) for output in outputs]
        return JsonResponse({"leaf_outputs": serialized_outputs}, status=200)
    except Run.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Run not found"}), content_type="application/json")

def get_islands(request, graph_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        graph = Graph.objects.get(id=graph_id)
        run_configs = graph.run_configs.all()
        if not run_configs.exists():
            return JsonResponse({"islands": []}, status=200)
        run_config = run_configs.latest('id')
        enabled_nodes = set(run_config.enable_list) if run_config.enable_list else set(graph.graph_nodes.values_list('node_id', flat=True))
        if run_config.disable_list:
            enabled_nodes -= set(run_config.disable_list)
        adj = defaultdict(list)
        for edge in Edge.objects.filter(src_node__graph=graph, src_node__node_id__in=enabled_nodes, dst_node__node_id__in=enabled_nodes):
            adj[edge.src_node.node_id].append(edge.dst_node.node_id)
        visited = set()
        islands = []

        for node in enabled_nodes:
            if node not in visited:
                island = []
                queue = deque([node])
                while queue:
                    current = queue.popleft()
                    if current not in visited:
                        visited.add(current)
                        island.append(current)
                        for neighbor in adj[current]:
                            if neighbor not in visited:
                                queue.append(neighbor)
                islands.append(island)
        return JsonResponse({"islands": islands}, status=200)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")

def get_toposort(request, graph_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        graph = Graph.objects.get(id=graph_id)
        run_configs = graph.run_configs.all()
        if not run_configs.exists():
            return HttpResponseBadRequest(json.dumps({"error": "No run configurations found for the graph"}), content_type="application/json")
        run_config = run_configs.latest('id')
        executor = GraphExecutor(graph, run_config)
        toposort = executor.topological_sort()
        return JsonResponse({"toposort": toposort}, status=200)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")
    except ValidationError as e:
        return HttpResponseBadRequest(json.dumps({"error": str(e)}), content_type="application/json")

def get_level_traversal(request, graph_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        graph = Graph.objects.get(id=graph_id)
        run_configs = graph.run_configs.all()
        if not run_configs.exists():
            return HttpResponseBadRequest(json.dumps({"error": "No run configurations found for the graph"}), content_type="application/json")
        run_config = run_configs.latest('id')
        executor = GraphExecutor(graph, run_config)
        executor.topological_sort()
        levels = defaultdict(list)
        for node, level in executor.levels.items():
            levels[level].append(node)
        sorted_levels = dict(sorted(levels.items()))
        return JsonResponse({"level_traversal": sorted_levels}, status=200)
    except Graph.DoesNotExist:
        return HttpResponseBadRequest(json.dumps({"error": "Graph not found"}), content_type="application/json")
    except ValidationError as e:
        return HttpResponseBadRequest(json.dumps({"error": str(e)}), content_type="application/json")
