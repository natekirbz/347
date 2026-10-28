from django.shortcuts import get_object_or_404
from ninja import Path, Router, Status

from projects.models import Project

from .models import Task
from .schemas import TaskIn, TaskOut

router = Router(tags=["tasks"])


@router.get("/", response=list[TaskOut])
def list_tasks(request, project_id: Path[int]):
    project = get_object_or_404(Project, id=project_id)
    return project.tasks.order_by("id")


@router.post("/", response={201: TaskOut})
def create_task(request, project_id: Path[int], payload: TaskIn):
    project = get_object_or_404(Project, id=project_id)
    return Status(201, Task.objects.create(project=project, **payload.dict()))


@router.get("/{task_id}", response=TaskOut)
def get_task(request, project_id: Path[int], task_id: int):
    return get_object_or_404(Task, id=task_id, project_id=project_id)
