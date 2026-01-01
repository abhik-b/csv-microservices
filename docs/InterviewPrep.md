## Docker

### Dockerfile

This file acts as a "recipe" to build a Docker Image—a self-contained package that includes the OS, Python, our code, and all dependencies. It ensures that if the app runs on our machine, it will run exactly the same way in production.

- `FROM python:3.11-slim`: Uses a lightweight version of Python 3.11. "Slim" images are preferred in 2026 because they reduce the attack surface by excluding unnecessary system tools.
- `WORKDIR /app`: Creates and sets the primary directory inside the container where all following commands will run.
- `ENV ...`.: Sets Python environment variables.
  `PYTHONDONTWRITEBYTECODE=1` prevents Python from writing .pyc files, keeping the container clean.
  `PYTHONUNBUFFERED=1` ensures logs are sent immediately to the terminal (crucial for Docker logs).
- `RUN apt-get update...`: Installs essential system-level tools (like gcc for compiling some Python packages) needed for database connections like PostgreSQL.
- `COPY requirements.txt .` then `RUN pip install...`: By copying only the requirements first, Docker can cache this layer. If you change your code but not your requirements, Docker skips the slow install process during the next build.
- `COPY . .`: Copies the rest of your actual source code into the image.
- `CMD [...]`: Defines the default command to start the app. It uses Uvicorn, a high-performance server required for FastAPI's asynchronous features

## Redis & Celery

### Question N

**The Backend is the "Result Store."
The Broker is for sending the task.
The Backend is for storing the result after the task is finished.
Why use the same URL?**

In a small or medium project, we use Redis for both because it's convenient and saves us from setting up a third service. Redis can handle both the "queue" (the broker) and the "storage" (the backend) at the same time. If you didn't have a backend defined, your FastAPI app would never be able to ask: "Hey, is task #42 actually done yet?"

### Question N+1

**The `include` list tells Celery exactly which files to import to find functions decorated with @app.task. Does it add more workers?**

No. Adding more items to the include list does not add more workers. It just gives the current worker more "skills" or "knowledge".

If you have src.worker.tasks (for CSVs) and you add src.worker.emails (for sending mail), the worker now knows how to do both. But it's still just one worker process.

### Question N+2

**So how do you actually add more Workers?**

If you want more workers to process CSVs faster, we don't change the code; we change the Docker command or our scaling.

In our docker-compose.yml, we would change replicas: 3, or just run the celery worker command in three different terminal windows/containers.

Each of those 3 workers will "include" the same tasks, and they will all watch the same "broker" for work.

### Question N+3

**What do they do in celery config?**

- `task_time_limit=30 * 60` (Hard Limit)
- and `task_soft_time_limit=25 * 60` (Soft Limit)

These are the "kill switches."

The Soft Limit gives the task a "warning" at 25 minutes so it can try to save its progress and close gracefully.

The Hard Limit at 30 minutes just kills the task process immediately. This is super important because it prevents a "zombie" CSV task from running forever and eating up all your CPU if the code gets stuck in a loop.
