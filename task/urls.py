from django.urls import path
from .views import TaskListCreateView, complete_task, create_task, get_tasks


urlpatterns = [
    path('all/', TaskListCreateView.as_view(), name='task-list-create'),
    path('<int:task_id>/complete/', complete_task, name='complete-task'),
    path('', get_tasks, name="get-tasks"),
    path('create/', create_task, name='create-task'),

]