from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator, model_validator
from app.repository import (
    Task,
    create_task as create_task_record,
    delete_task as delete_task_record,
    get_task as get_task_record,
    init_db,
    list_tasks as list_task_records,
    update_task as update_task_record,
)


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small PostgreSQL-backed API for managing tasks.",
)

init_db()


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
    return list_task_records()


@app.get("/tasks/{task_id}", response_model=None, summary="Get a task")
def get_task(task_id: int) -> Task | JSONResponse:
    task = get_task_record(task_id)
    if task is None:
        return task_not_found(task_id)
    return task


@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(payload: TaskCreate) -> Task:
    return create_task_record(payload.title)


@app.put("/tasks/{task_id}", response_model=None, summary="Update a task")
def update_task(task_id: int, payload: TaskUpdate) -> Task | JSONResponse:
    task = update_task_record(task_id, payload.title, payload.done)
    if task is None:
        return task_not_found(task_id)
    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    response_class=Response,
    summary="Delete a task",
)
def delete_task(task_id: int) -> Response:
    if not delete_task_record(task_id):
        return task_not_found(task_id)
    return Response(status_code=204)
