from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False


TODO_FILE = "todos.json"

def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as f:
            data = json.load(f)
            return [Todo(**item) for item in data]
    return []

def save_todos():
    with open(TODO_FILE, "w") as f:
        json.dump([t.dict() for t in todos], f)

todos: List[Todo] = load_todos()


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def render_todo_html(todo):
    completed_class = "completed" if todo.completed else ""
    checkbox = (
        f"<input type='checkbox' class='complete-checkbox' hx-patch='/todos/{todo.id}/toggle' hx-target='#todo-{todo.id}' hx-swap='outerHTML' {'checked' if todo.completed else ''}>"
    )
    delete_btn = (
        f"<button class='delete-btn' title='Delete' hx-delete='/todos/{todo.id}' hx-target='#todo-{todo.id}' hx-swap='outerHTML'>&#10006;</button>"
    )
    return f"""
    <div class='todo {completed_class}' id='todo-{todo.id}'>
        <div>
          <div class='todo-main'>
              {checkbox}
              <div class='todo-title'>{todo.title}</div>
          </div>
          <div class='todo-desc'>{todo.description}</div>
        </div>
        {delete_btn}
    </div>
    """

@app.post("/todos", response_class=HTMLResponse)
async def create_todo(
    request: Request,
    title: str = Form(...),
    description: str = Form("")
):
    # Auto-assign next available ID
    next_id = max([t.id for t in todos], default=0) + 1
    todo = Todo(id=next_id, title=title, description=description)
    todos.insert(0, todo)
    save_todos()
    return render_todo_html(todo)

@app.get("/todos", response_class=HTMLResponse)
def get_todos():
    html = ""
    # Render todos in most-recent-first order (newest at the top)
    for todo in todos:
        html += render_todo_html(todo)
    return html

@app.delete("/todos/{todo_id}", response_class=HTMLResponse)
def delete_todo_htmx(todo_id: int):
    for idx, todo in enumerate(todos):
        if todo.id == todo_id:
            del todos[idx]
            save_todos()
            return ""  # Remove from DOM
    return HTMLResponse("Todo not found", status_code=404)
    return html

# Toggle completion status
@app.patch("/todos/{todo_id}/toggle", response_class=HTMLResponse)
def toggle_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            todo.completed = not todo.completed
            save_todos()
            return render_todo_html(todo)
    return HTMLResponse("Todo not found", status_code=404)

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found.")

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updated_todo: Todo):
    for idx, todo in enumerate(todos):
        if todo.id == todo_id:
            todos[idx] = updated_todo
            return updated_todo
    raise HTTPException(status_code=404, detail="Todo not found.")

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for idx, todo in enumerate(todos):
        if todo.id == todo_id:
            del todos[idx]
            return {"detail": "Todo deleted."}
    raise HTTPException(status_code=404, detail="Todo not found.")
