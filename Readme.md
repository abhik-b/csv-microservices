## Getting Started

### Prerequisites

- Docker should be installed
- `.env` files of your own

Check the `.env.example` for more info.

### Step 1

Then in the terminal : `docker compose --build --no-cache`

This will get the project built

Then run `docker compose up` to get the project up and running.

## Phase 1

- Build the core services ✅
- write some tests ✅
- make some diagrams

### Service 1 Fast API Backend

- 1. Fast API setup ✅
  - a.basic structure ✅
  - b.Jinja Templates ✅
  - c.Upload Files ✅
- 2. Set up Sqlite ✅
- 3. Create Models ✅
- 4. Task in DB ✅

### Service 2 CSV Processing

- Poll Postgres for tasks with status = “PENDING” ✅
- Lock the task → Set status = “PROCESSING” ✅
- Mark task as “COMPLETED” or “FAILED” ✅
- Process the CSV
  - drop duplicates ✅
  - remove missing rows ✅
  - drop columns ✅
  - fill missing values ✅
- Write results to task_results table ✅

### Service 3 Frontend

- Given a task_id → return task status + results ✅
- Task configuration gets uploaded from frontend ✅
- Build the full “frontend API” users will use later.
  - Task id page is where the task type (config) is created ✅
  - Tasks are displayed based on filters (admin page) ✅
  - File Upload page & redirect to Task id page ✅

### Tests

- CSV Processing Logic

  - duplicates are removed ✅
  - missing rows are dropped ✅
  - columns are dropped correctly ✅
  - fillna works as expected ✅

- Task Lifecycle Tests (DB + Logic) ✅

## Phase 2

- add docker ✅
- add docker compose ✅
- handle the processing part
- add schedulers

### Docker

- prepare a dockerfile ✅
- build docker image ✅
- run docker image ✅
- add docker compose yaml ✅
- docker compose working ✅

```bash
docker compose up --watch
docker compose down

docker exec -it csv-micro-db-1 psql -U postgres -d csv_processin -c "SELECT * FROM tasks LIMIT 5;"
```

### Logs & healthchecks

- Healthcheck ✅
- Loguru ✅

### Redis & Celery

- add then to requriements.txt ✅
- initialize the celery app ✅
- plan new way for csv processing to get triggered ✅
- decorate the csv processing with celery task ✅

## Phase 3

- update the user of the status of the task ✅
- lifespan instead of on_event startup
- datetime.utcnow replace ✅
- proper task service
- add loggers ✅
- Test the API ✅
- admin page tab style ui
- admin page startup show all tasks
- polish the project
- prepare for interview
- prepare a actual readme

### API

### UI

- user cant see the config form after the processing begins ✅

## Acknowledgements

1. Thanks to this article on ([setting up pgadmin with docker](https://www.geeksforgeeks.org/postgresql/run-postgresql-on-docker-and-setting-up-pgadmin/))
2. this command shows the table

```bash
docker exec -it csv-micro-db-1 psql -U postgres -d csv_processin -c "SELECT * FROM tasks LIMIT 5;"
```
