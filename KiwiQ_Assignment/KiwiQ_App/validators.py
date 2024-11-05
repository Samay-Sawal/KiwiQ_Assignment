from .models import Graph, Node, Edge
from django.core.exceptions import ValidationError
from collections import defaultdict, deque

class GraphValidator:
    def validate_graph(graph):
        try:
            GraphValidator.topological_sort(graph)
        except ValidationError as e:
            raise e

        if not GraphValidator.is_connected(graph):
            raise ValidationError("Graph contains multiple disconnected components (islands).")

    def topological_sort(graph):
        in_degree = defaultdict(int)
        adj_list = defaultdict(list)
        for edge in Edge.objects.filter(src_node__graph=graph):
            adj_list[edge.src_node.node_id].append(edge.dst_node.node_id)
            in_degree[edge.dst_node.node_id] += 1

        queue = deque([node.node_id for node in graph.graph_nodes.all() if in_degree[node.node_id] == 0])
        sorted_order = []

        while queue:
            current = queue.popleft()
            sorted_order.append(current)
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != graph.graph_nodes.count():
            raise ValidationError("Graph contains a cycle.")

    def is_connected(graph):
        
        nodes = list(graph.graph_nodes.all())
        if not nodes:
            return True 

        visited = set()
        queue = deque()
        queue.append(nodes[0].node_id)
        visited.add(nodes[0].node_id)

        adj_list = defaultdict(list)
        for edge in Edge.objects.filter(src_node__graph=graph):
            adj_list[edge.src_node.node_id].append(edge.dst_node.node_id)
            adj_list[edge.dst_node.node_id].append(edge.src_node.node_id)

        while queue:
            current = queue.popleft()
            for neighbor in adj_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == graph.graph_nodes.count()
