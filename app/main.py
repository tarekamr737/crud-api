from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing_extensions import TypedDict


app = FastAPI()


class Task(TypedDict):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value


tasks: list[Task] = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write report", "done": True},
    {"id": 3, "title": "Call dentist", "done": False},
]


def find_task(task_id: int) -> Task | None:
    return next((task for task in tasks if task["id"] == task_id), None)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: object, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "Invalid request"})


@app.get("/")
def read_root() -> dict[str, str | list[str]]:
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> list[Task]:
    return tasks


@app.get("/tasks/{task_id}", response_model=None)
def get_task(task_id: int) -> Task | JSONResponse:
    task = find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )
    return task


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate) -> Task:
    task: Task = {
        "id": max((task["id"] for task in tasks), default=0) + 1,
        "title": payload.title,
        "done": False,
    }
    tasks.append(task)
    return task
