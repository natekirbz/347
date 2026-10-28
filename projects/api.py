from django.shortcuts import get_object_or_404
from ninja import Router, Status

from .models import Project
from .schemas import ProjectIn, ProjectOut

router = Router(tags=["projects"])


@router.get("/", response=list[ProjectOut])
def list_projects(request):
    return Project.objects.order_by("id")


@router.post("/", response={201: ProjectOut})
def create_project(request, payload: ProjectIn):
    return Status(201, Project.objects.create(**payload.dict()))


@router.get("/{project_id}", response=ProjectOut)
def get_project(request, project_id: int):
    return get_object_or_404(Project, id=project_id)


@router.put("/{project_id}", response=ProjectOut)
def update_project(request, project_id: int, payload: ProjectIn):
    project = get_object_or_404(Project, id=project_id)
    for attr, value in payload.dict().items():
        setattr(project, attr, value)
    project.save()
    return project


@router.delete("/{project_id}", response={204: None})
def delete_project(request, project_id: int):
    get_object_or_404(Project, id=project_id).delete()
    return Status(204, None)
