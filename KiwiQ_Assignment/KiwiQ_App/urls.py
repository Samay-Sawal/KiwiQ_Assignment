from django.urls import path
from . import views

urlpatterns = [
    path('graphs/', views.create_graph, name='create_graph'),
    path('graphs/<int:graph_id>/', views.get_graph, name='get_graph'),
    path('graphs/<int:graph_id>/update/', views.update_graph, name='update_graph'),
    path('graphs/<int:graph_id>/delete/', views.delete_graph, name='delete_graph'),
    path('graphs/<int:graph_id>/run/', views.run_graph, name='run_graph'),
    path('runs/<str:run_id>/output/<str:node_id>/', views.get_run_output, name='get_run_output'),
    path('runs/<str:run_id>/leaf_outputs/', views.get_leaf_outputs, name='get_leaf_outputs'),
    path('graphs/<int:graph_id>/islands/', views.get_islands, name='get_islands'),
    path('graphs/<int:graph_id>/toposort/', views.get_toposort, name='get_toposort'),
    path('graphs/<int:graph_id>/level_traversal/', views.get_level_traversal, name='get_level_traversal'),
]
