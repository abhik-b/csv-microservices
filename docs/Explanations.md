## Project Structure

- `Dockerfile` : This is necessary to build the Docker image which Will build the environment under which this project will work.
- `docker-compose.yml` : This file holds everything that is necessary for the Docker to run the multiple services together that we use such as on the Postgres database, radius database, celery worker as well as the Project main app.
- `templates` : This folder holds all the html files
- `tests` : This folder holds all the tests that Testing the project
- `pytest.ini` : This file holds certain configuration related to `pytest`
- `logs` : This folder holds all the logs that are outputted by loguru

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

## FastAPI

## Redis & Celery

So basically what happens is when there are multiple users, everyone will upload their file and their specific configuration and then they press the process button. Instead of making the users wait, all these processes go straight into the Redis queue as separate tasks. This way, the FastAPI server stays super light and responsive because it isn’t actually doing the heavy cleaning or processing itself. From there, Celery just picks up the tasks from the queue one by one and it processes them in the background and updates the result for each respective user.

Now let's get one level deeper into the technical side. Inside our FastAPI code, when that API gets called, it saves the configuration into our database and then triggers a Celery task. This actually loads a "task message" into the Redis queue which acts like a waiting room for the workers. Now, the Celery worker is a separate process that is constantly watching Redis; it picks up that task and calls our CSV processing function directly. This function then pulls the configuration from the database, runs all the Pandas logic like dropping duplicates or filling missing values, and then saves the final output back to the database. So the API and the worker are totally independent but they work together through Redis and the shared database.

### So Why Redis ?

So basically, the biggest difference is that Redis is an in-memory database, while PostgreSQL is disk-based. When Celery is picking up tasks, every millisecond counts. Redis works at RAM speed, so it handles read and write operations in sub-milliseconds. PostgreSQL, even if it's very fast, still has the overhead of writing to a disk and managing complex transactions, which makes it slower for a high-speed task queue.

Now, another deep-dive reason is how they handle the "waiting" part. When a Celery worker is waiting for a task, it doesn't want to keep "polling" or asking the database every second—that would just waste resources. Redis has a built-in feature called Blocking Queues (like the BRPOP command). This lets the worker "hang" on a connection until a new task arrives, and Redis pushes it to the worker instantly. Doing this in a relational database like Postgres is much heavier and can lead to locks that slow down your main application.

### And Why celery?

So basically, if we do the processing inside FastAPI itself, it will "block" the worker. FastAPI is like a waiter in a restaurant taking orders. If the waiter also goes into the kitchen to cook the meal (the CSV processing), they can't take orders from any other customers. By using Celery, the waiter just takes the order, hands a ticket to the kitchen (Redis), and is immediately free to help the next user. Without Celery, if a CSV takes 30 seconds to process, your entire website would just "freeze" for that user and potentially others until the file is done.

## Conclusion of the tech stack

So basically, FastAPI is the face of the project. Its only job is to handle the user's request as fast as possible. When a user uploads a CSV, FastAPI doesn't do any of the cleaning or processing. It just saves the file, writes the configuration to the database, and then quickly hands over a "task ticket" to Redis. By doing this, it stays super responsive and is immediately ready to help the next user.

Now, Redis acts like the "waiting room" or the "post office" between the API and the worker. Because it’s an in-memory database, it’s incredibly fast. It takes that task ticket from FastAPI and holds it in a queue. It doesn't know how to process a CSV; it just makes sure the task is stored safely and is ready to be picked up the moment a worker becomes available.

Celery is the real engine of the project. It’s a separate process that is constantly watching the Redis queue. As soon as it sees a new task in Redis, it grabs it and starts the actual CSV processing. It pulls the data from the database, runs your Pandas code to drop duplicates or fill missing values, and saves the final result. Because it runs independently, it can take as long as it needs without ever slowing down the main website.
