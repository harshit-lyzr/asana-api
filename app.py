import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asana
from dotenv import load_dotenv

load_dotenv()
ASANA_KEY = os.getenv("ASANA_TOKEN")
# Initialize FastAPI app
app = FastAPI()

# Set your Asana Personal Access Token (PAT)
client = asana.Client.access_token(ASANA_KEY)

# Define models for request bodies
class TaskCreateRequest(BaseModel):
    workspace_id: str
    project_id: str
    name: str
    notes: str
    followers: list[str]
    assignee: str
    due_on: str

class ProjectCreateRequest(BaseModel):
    workspace_id: str
    name: str
    notes: str
    privacy_setting: str
    due_on: str

class TaskUpdateRequest(BaseModel):
    task_id: str

class CustomFieldCreateRequest(BaseModel):
    project_id: str
    name: str
    field_type: str  # e.g., "enum"
    options: list[dict]

# Create a new task
@app.post("/create-task")
async def create_task(request: TaskCreateRequest):
    try:
        task = client.tasks.create_task({
            'workspace': request.workspace_id,
            'projects': [request.project_id],
            'name': request.name,
            'notes': request.notes,
            'followers': request.followers,
            'assignee': request.assignee,
            'due_on': request.due_on,
        })
        return {"task_id": task['gid'], "task_name": task['name']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Create a new project
@app.post("/create-project")
async def create_project(request: ProjectCreateRequest):
    try:
        project = client.projects.create_project({
            'workspace': request.workspace_id,
            'name': request.name,
            'notes': request.notes,
            'privacy_setting': request.privacy_setting,
            'due_on': request.due_on,
        })
        return {"project_id": project['gid'], "project_name": project['name']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/task/{task_id}")
async def get_task(task_id: str):
    try:
        task = client.tasks.get_task(task_id)
        return {
            "task_id": task['gid'],
            "name": task['name'],
            "notes": task['notes'],
            "assignee": task.get('assignee', None),
            "due_on": task.get('due_on', None),
            "completed": task['completed']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workspaces")
async def get_workspaces():
    try:
        workspaces = client.workspaces.find_all()
        return [{"workspace_id": workspace['gid'], "name": workspace['name']} for workspace in workspaces]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{workspace_id}")
async def get_projects(workspace_id: str):
    try:
        projects = client.projects.find_by_workspace(workspace_id)
        return [{"project_id": project['gid'], "name": project['name']} for project in projects]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{workspace_id}")
async def get_users(workspace_id: str):
    try:
        users = client.users.get_users_for_workspace(workspace_id)
        return [{"user_id": user['gid'], "name": user['name']} for user in users]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get all tasks in a project
@app.get("/tasks/{project_id}")
async def get_tasks(project_id: str):
    try:
        tasks = client.tasks.get_tasks_for_project(project_id)
        return [{"task_id": task['gid'], "task_name": task['name']} for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# @app.post("/custom-field")
# async def create_custom_field(request: CustomFieldCreateRequest):
#     try:
#         # This assumes custom fields are created by updating a project
#         project = client.projects.find_by_id(request.project_id)
#         custom_fields = project.get('custom_field_settings', [])
#
#         # Find existing custom fields with the same name to avoid duplication
#         existing_field = next((field for field in custom_fields if field['custom_field']['name'] == request.name), None)
#         if existing_field:
#             raise HTTPException(status_code=400, detail="Custom field with this name already exists.")
#
#         # Create a new custom field
#         field_data = {
#             'name': request.name,
#             'type': request.field_type,
#             'enum_options': request.options if request.field_type == 'enum' else [],
#         }
#         custom_field = client.custom_fields.create_custom_field({
#             'project': request.project_id,
#             **field_data
#         })
#         return {"custom_field_id": custom_field['gid'], "name": custom_field['name']}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

class CustomFieldCreateRequest(BaseModel):
    workspace_id: str
    project_id: str
    name: str
    field_type: str  # e.g., "text", "number", "enum"
    options: list[str] = []


@app.post("/create-custom-field")
async def create_custom_field(request: CustomFieldCreateRequest):
    try:
        data = {
            'name': request.name,
            'type': request.field_type,
            'workspace': request.workspace_id
        }

        if request.field_type == 'enum' and request.options:
            data['enum_options'] = [{'name': option} for option in request.options]

        # Create the custom field
        custom_field = client.custom_fields.create_custom_field(data)

        # Add the custom field to the project
        client.projects.add_custom_field_setting(request.project_id, {
            'custom_field': custom_field['gid'],
            'precision': '0'  # Adjust 'precision' based on the field type
        })

        return {"custom_field_id": custom_field['gid'], "name": custom_field['name'],"options": custom_field['enum_options']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
