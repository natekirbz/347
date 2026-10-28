from ninja import ModelSchema

from .models import Project


class ProjectIn(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ProjectOut(ModelSchema):
    class Meta:
        model = Project
        fields = ["id", "name", "description", "created_at"]
