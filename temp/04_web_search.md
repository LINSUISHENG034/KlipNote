## FastAPI starter template boilerplate CLI create command 2024 2025

Based on your search for FastAPI starter templates, boilerplates, and CLI creation commands for 2024 and 2025, here are the most relevant and popular options.

The methods generally fall into three categories: the official FastAPI tools, dedicated third-party CLI generators, and versatile Cookiecutter templates.

---

### 1. Official FastAPI Tools

FastAPI's creator and team provide official tools that are a great starting point.

* **Official `fastapi` CLI:** The `fastapi` library itself (when installed with standard dependencies like `pip install "fastapi[all]"`) now includes a built-in CLI. It's not for *generating* complex boilerplates but for *running* your app.
    * **Development:** `fastapi dev main.py`
    * **Production:** `fastapi run main.py`

* **Official Full-Stack Template:** This is the go-to official boilerplate for a full-stack application. It is kept up-to-date and includes:
    * **Features:** FastAPI, React, SQLModel, PostgreSQL, Docker, automatic HTTPS, and more.
    * **Repository:** `github.com/fastapi/full-stack-fastapi-template`

---

### 2. Dedicated CLI Project Generators

These are installable Python packages designed to create new projects from your terminal with a single command.

* **`fastapi-starter-cli` (New in 2025):**
    * **What it is:** A new (Jan 2025) CLI tool specifically for generating FastAPI projects.
    * **Features:** Supports multiple databases (PostgreSQL, MySQL, etc.), SQLModel, and Alembic migrations.
    * **Install:** `pip install fastapi-starter-cli`
    * **Create Command:** `fastapi start create-project`

* **`create-fastapi-project`:**
    * **What it is:** A popular, interactive CLI tool.
    * **Features:** Provides an interactive setup to include SQLModel (async), Celery, and JWT authentication.
    * **Install:** `pip install create-fastapi-project`
    * **Create Command:** `create-fastapi-project` (This will start the interactive prompts)

* **`fastapi-utilities`:**
    * **What it is:** A broader utilities library that includes a project initializer.
    * **Install:** `pip install fastapi-utilities`
    * **Create Command:** `python -m fastapi_utilities init`

---

### 3. Cookiecutter Templates

**Cookiecutter** is a powerful command-line tool that creates projects from templates. You install Cookiecutter, then use it to "cut" a new project from a template repository. This is one of the most popular and flexible methods.

**How it works (General):**
1.  Install Cookiecutter: `pip install cookiecutter`
2.  Run the command: `cookiecutter <template-github-url>`

**Popular FastAPI Templates (2024-2025):**

* **`Tobi-De/cookiecutter-fastapi`:**
    * **What it is:** A highly-regarded and feature-rich template inspired by `cookiecutter-django`.
    * **Features:** Includes `fastapi-users` for authentication, Tortoise-ORM or Beanie (for MongoDB), Alembic, and a CLI tool for managing your project.
    * **Create Command:** `cookiecutter https://github.com/Tobi-De/cookiecutter-fastapi`

* **`fastapi-alembic-sqlmodel-async`:**
    * **What it is:** A focused template for a modern async stack.
    * **Features:** Uses FastAPI, Pydantic 2.0, Alembic, and async SQLModel.
    * **Create Command:** `cookiecutter https://github.com/jonra1993/fastapi-alembic-sqlmodel-async`

* **`zhiwei2017/FastAPI-Cookiecutter` (Updated 2024):**
    * **What it is:** A template that generates a project with an MVC (Model-View-Controller) like structure.
    * **Create Command:** `cookiecutter https://github.com/zhiwei2017/FastAPI-Cookiecutter.git`

---

## Vue 3 Vite starter template create command latest options 2024 2025

Here are the latest (2024-2025) create commands and options for starting a new Vue 3 project with Vite.

The **official and recommended** way to create a new Vue 3 + Vite project is to use the `create-vue` tool.

-----

### � Official Create Command

This single command will launch an interactive setup wizard:

```bash
npm create vue@latest
```

During the setup, you will be prompted to choose which features to include. This is the best part, as you can build your starter template to your exact needs.

**Key Options You Can Select:**

  * **TypeScript:** Add TypeScript support.
  * **Pinia:** Include Pinia for state management (the official, recommended choice).
  * **Vue Router:** Add Vue Router for client-side routing.
  * **Testing:** Options to add Vitest for unit testing and Cypress for E2E testing.
  * **ESLint:** Set up ESLint for code linting.
  * **Prettier:** Set up Prettier for code formatting.

This interactive method is superior to most static boilerplates because it's always up-to-date and tailored to your specific project requirements.

-----

### ⚡️ Non-Interactive / CLI Flag Commands

If you want to skip the interactive prompts and create a project with specific features, you can use command-line flags.

**1. Using `create-vue` (Recommended):**

The `create-vue` tool itself accepts flags. For example, to create a new app with TypeScript and Pinia:

```bash
# Note: The '--' is necessary to pass flags to the underlying script
npm create vue@latest my-vue-app -- --typescript --pinia --router
```

**2. Using `create-vite` (More General):**

You can also use Vite's native creator, `create-vite`. This is faster but provides fewer Vue-specific options out of the box (like Pinia or testing setup).

```bash
# Creates a project with Vue and TypeScript
npm create vite@latest my-vue-app -- --template vue-ts

# Creates a project with plain Vue (JavaScript)
npm create vite@latest my-vue-app -- --template vue
```

-----

### � Popular Third-Party Boilerplates

If you want a more opinionated, "batteries-included" starter with features like layouts, UI components, and advanced folder structures already built, you can use a community boilerplate.

  * **Vitesse:** A popular and opinionated starter template by Vue core team member Anthony Fu. It's built for speed and comes with a huge set of features pre-configured.

      * **Features:** Vue 3, Vite, TypeScript, Pinia, Vue Router, UnoCSS, and much more.
      * **Create Command:** `npm create vitesse@latest`

  * **`vue3-ts-vite-starter-template`:**

      * **What it is:** A popular GitHub template with a clean setup.
      * **Features:** Vue 3, Vite, TypeScript, Pinia, Vue Router, and Tailwind CSS.
      * **How to use:** You would typically fork this repository or use it as a template on GitHub.

For most new projects in 2024-2025, starting with **`npm create vue@latest`** is the recommended best practice.

---

### FastAPI Celery Redis project template structure best practices

Here are the best practices and a recommended project structure for building a FastAPI application with Celery and Redis, based on my findings.

The core best practice is to **use Docker and Docker Compose** to manage your services. This approach neatly separates your FastAPI web application, your Celery worker, and your Redis database into distinct, manageable containers.

-----

### � Best Practices

1.  **Use Redis for Dual Roles:** Use Redis as *both* the Celery **message broker** (to queue tasks) and the **result backend** (to store task results).
2.  **Separate Your Services:** Your application will run as at least three separate processes (services) defined in your `docker-compose.yaml`:
      * **`web`:** The FastAPI application, run by Uvicorn. This service receives API requests and dispatches tasks to Celery.
      * **`worker`:** The Celery worker. This service listens to the Redis queue, picks up tasks, and executes them.
      * **`redis`:** The Redis container itself, acting as the broker and backend.
3.  **Use `@shared_task`:** In your `tasks.py` file, use the `@shared_task` decorator from Celery. This avoids circular import issues that can happen when you try to import your main Celery app instance into your task modules.
4.  **Centralize Configuration:** Use a `.env` file to store your configuration variables (like `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`). A `config.py` file can load these variables into your application.
5.  **Monitor with Flower:** Include **Flower** as a fourth service in your Docker Compose file. It's a real-time web-based monitoring tool for Celery that is invaluable for development and production.

-----

### � Recommended Project Structure

Here is a robust, scalable project structure that separates your FastAPI app from your Celery configuration.

```bash
fastapi-celery-project/
├── docker-compose.yaml       # Defines and connects all services
├── .env                      # Stores configuration and secrets
├── requirements.txt          # Project dependencies
└── app/                      # Main application source code
    ├── __init__.py
    ├── main.py               # FastAPI app creation and API endpoints
    ├── config.py             # Loads settings from .env
    ├── celery_utils.py       # Celery instance configuration
    └── tasks/
        ├── __init__.py
        └── worker.py         # Defines your Celery tasks (e.g., @shared_task)
```

-----

### � Key File Examples

Here are the simplified contents of the most important files to connect everything.

#### 1\. `.env`

This is where you define the connection string for Redis.

```ini
# .env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

#### 2\. `app/config.py`

A simple Pydantic class to load your settings from the `.env` file.

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"

settings = Settings()
```

#### 3\. `app/celery_utils.py`

This file creates the Celery application instance.

```python
# app/celery_utils.py
from celery import Celery
from app.config import settings

celery = Celery(
    __name__,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Load task modules from all registered Django app configs.
celery.autodiscover_tasks(['app.tasks.worker'])
```

#### 4\. `app/tasks/worker.py`

This is where you define your actual background tasks.

```python
# app/tasks/worker.py
from celery import shared_task
import time

@shared_task
def my_long_running_task(x: int, y: int) -> int:
    """A sample long-running task."""
    time.sleep(10)  # Simulate 10 seconds of work
    return x + y
```

#### 5\. `app/main.py`

Your FastAPI app, which creates and dispatches tasks.

```python
# app/main.py
from fastapi import FastAPI
from celery.result import AsyncResult
from app.tasks.worker import my_long_running_task

app = FastAPI()

@app.post("/tasks/run")
def run_task(x: int, y: int):
    """
    Enqueues a new background task.
    """
    task = my_long_running_task.delay(x, y)
    return {"task_id": task.id}

@app.get("/tasks/status/{task_id}")
def get_task_status(task_id: str):
    """
    Queries the status of a background task.
    """
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
```

#### 6\. `docker-compose.yaml`

This file ties everything together.

```yaml
# docker-compose.yaml
version: '3.8'

services:
  # FastAPI Web Service
  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./app:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis

  # Celery Worker Service
  worker:
    build: .
    # Command to start the celery worker
    command: celery -A app.celery_utils.celery worker --loglevel=info
    volumes:
      - ./app:/app
    depends_on:
      - redis

  # Redis Service
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Flower Monitoring Service
  flower:
    image: mher/flower
    command: flower --broker=${CELERY_BROKER_URL} --port=5555
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    ports:
      - "5555:5555"
    depends_on:
      - redis
```

[Background Tasks with FastAPI and Celery](https://www.youtube.com/watch?v=eAHAKowv6hk)

This video provides a detailed, step-by-step walkthrough of how to integrate Celery and Redis into a FastAPI application for handling background tasks.
http://googleusercontent.com/youtube_content/0

---