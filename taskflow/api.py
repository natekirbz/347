from ninja import NinjaAPI

api = NinjaAPI(title="TaskFlow API", urls_namespace="taskflow")

api.add_router("/projects", "projects.api.router")
api.add_router("/projects/{project_id}/tasks", "tasks.api.router")
