from fastapi import FastAPI
from fastapi.responses import JSONResponse


app = FastAPI()

tasks: list[dict[str, int | str | bool]] = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write report", "done": True},
    {"id": 3, "title": "Call dentist", "done": False},
]


def find_task(task_id: int) -> dict[str, int | str | bool] | None:
    return next((task for task in tasks if task["id"] == task_id), None)


@app.get("/")
def read_root() -> dict[str, str | list[str]]:
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> list[dict[str, int | str | bool]]:
    return tasks


@app.get("/tasks/{task_id}", response_model=None)
def get_task(task_id: int) -> dict[str, int | str | bool] | JSONResponse:
    task = find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )
    return task
