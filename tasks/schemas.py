from ninja import ModelSchema

from .models import Task


class TaskIn(ModelSchema):
    class Meta:
        model = Task
        fields = ["title", "description"]


class TaskOut(ModelSchema):
    class Meta:
        model = Task
        fields = ["id", "project", "title", "description", "created_at"]
