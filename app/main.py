from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator, model_validator
from app.db import Task, fetch_task, fetch_tasks, initialize_database, insert_task


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small in-memory API for managing tasks.",
)

initialize_database()


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be empty")
        return value

    @model_validator(mode="after")
    def at_least_one_field_is_required(self) -> "TaskUpdate":
        if self.title is None and self.done is None:
            raise ValueError("at least one field is required")
        return self


tasks: list[Task] = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write report", "done": True},
    {"id": 3, "title": "Call dentist", "done": False},
]


def find_task(task_id: int) -> Task | None:
    return next((task for task in tasks if task["id"] == task_id), None)


def task_not_found(task_id: int) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: object, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "Invalid request"})


@app.get("/", summary="Show API metadata")
def read_root() -> dict[str, str | list[str]]:
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check API health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks", summary="List tasks")
def list_tasks() -> list[Task]:
    return fetch_tasks()


@app.get("/tasks/{task_id}", response_model=None, summary="Get a task")
def get_task(task_id: int) -> Task | JSONResponse:
    task = fetch_task(task_id)
    if task is None:
        return task_not_found(task_id)
    return task


@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(payload: TaskCreate) -> Task:
    return insert_task(payload.title)


@app.put("/tasks/{task_id}", response_model=None, summary="Update a task")
def update_task(task_id: int, payload: TaskUpdate) -> Task | JSONResponse:
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)
    if payload.title is not None:
        task["title"] = payload.title
    if payload.done is not None:
        task["done"] = payload.done
    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a task",
)
def delete_task(task_id: int) -> Response:
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)
    tasks.remove(task)
    return Response(status_code=204)
