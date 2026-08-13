from fastapi import Depends, FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator, model_validator
from supabase_auth.errors import AuthError
from src.routes.triage import router as triage_router

from app.auth import get_access_token, get_current_user, supabase, unauthorized
from app.repository import (
    Task,
    create_task as create_task_record,
    delete_task as delete_task_record,
    get_task as get_task_record,
    init_db,
    list_tasks as list_task_records,
    update_task as update_task_record,
)
from supabase_auth.types import User


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


class AuthCredentials(BaseModel):
    email: str
    password: str

    @field_validator("email", "password")
    @classmethod
    def field_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be empty")
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
    if getattr(getattr(request, "url", None), "path", None) == "/triage":
        fields = [
            str(location)
            for error in exc.errors()
            for location in error.get("loc", ())
            if location != "body"
        ]
        field = fields[-1] if fields else "text"
        return JSONResponse(status_code=400, content={"error": f"Invalid field: {field}"})
    return JSONResponse(status_code=400, content={"error": "Invalid request"})


app.include_router(triage_router)


@app.get("/", summary="Show API metadata")
def read_root() -> dict[str, str | list[str]]:
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/triage", "/triage/jobs/{job_id}"],
    }


@app.get("/health", summary="Check API health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/public/info", summary="Show public information")
def public_info() -> dict[str, str]:
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", summary="Show the authenticated user profile")
def protected_profile(
    current_user: User = Depends(get_current_user),
) -> dict[str, str | None]:
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "created_at": str(current_user.created_at),
    }


@app.get("/protected/dashboard", summary="Show protected dashboard data")
def protected_dashboard(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return {
        "message": "This dashboard is protected.",
        "user_id": str(current_user.id),
    }


@app.post(
    "/auth/signup",
    status_code=201,
    response_model=None,
    summary="Create an account",
)
def signup(payload: AuthCredentials) -> dict[str, str | None] | JSONResponse:
    try:
        response = supabase.auth.sign_up(
            {"email": payload.email.strip(), "password": payload.password}
        )
    except AuthError:
        return JSONResponse(
            status_code=400,
            content={"error": "Unable to create account"},
        )

    if response.user is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Unable to create account"},
        )
    return {
        "id": str(response.user.id),
        "email": response.user.email,
        "created_at": str(response.user.created_at),
    }


@app.post(
    "/auth/login",
    response_model=None,
    summary="Log in",
)
def login(payload: AuthCredentials) -> dict[str, str] | JSONResponse:
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": payload.email.strip(), "password": payload.password}
        )
    except AuthError:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid email or password"},
        )

    if response.session is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid email or password"},
        )
    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }


@app.post(
    "/auth/logout",
    status_code=204,
    response_class=Response,
    summary="Log out",
)
def logout(
    current_user: User = Depends(get_current_user),
    access_token: str = Depends(get_access_token),
) -> Response:
    del current_user
    try:
        supabase.auth.admin.sign_out(access_token)
    except AuthError:
        raise unauthorized() from None
    return Response(status_code=204)


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
