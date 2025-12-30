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

### Logs & healthchecks

- Healthcheck ✅
<!-- - Loguru ✅ -->

```bash
docker compose up --watch
docker compose down

docker exec -it csv-micro-db-1 psql -U postgres -d csv_processin -c "SELECT * FROM tasks LIMIT 5;"
```

### Celery

## Phase 3

- polish the project
- prepare for interview
- prepare a actual readme

### Polishing

- look for inplace processing
<!-- (so that we can get rid of output folder & saving the file twice) -->
- lifespan instead of on_event startup
- datetime.utcnow replace
- proper task service
- add loggers
- Test the API
- admin page tab style ui
- admin page startup show all tasks

## Acknowledgements

1. Thanks to this article on ([setting up pgadmin with docker](https://www.geeksforgeeks.org/postgresql/run-postgresql-on-docker-and-setting-up-pgadmin/))
2. this command shows the table

```bash
docker exec -it csv-micro-db-1 psql -U postgres -d csv_processin -c "SELECT * FROM tasks LIMIT 5;"
```

<!-- <div class="task-list">
       <ul class="flex flex-col items-start gap-2.5">
           {% for task in tasks %}
               <li class="bg-gray-50 w-[660px]">
                   <div class="flex flex-col w-full  leading-1.5 p-4 bg-neutral-secondary-soft rounded-e-base rounded-es-base">
                       <div class="flex items-center justify-between
                                   space-x-1.5 rtl:space-x-reverse w-full">
                           <span class="text-sm font-semibold text-heading">{{task.filename}}</span>
                           <span class="text-sm text-body">{{task.status}}</span>
                       </div>
                       <p class="text-sm text-body">Uploaded at : {{task.created_at.strftime('%d-%m-%Y -- %H:%M:%S')}}</p>
                       <p class="text-sm text-body">Started Processing at : {{task.started_at.strftime('%d-%m-%Y -- %H:%M:%S')}}</p>
                       <p class="text-sm text-body"> Completed Processing at : {{task.completed_at.strftime('%d-%m-%Y -- %H:%M:%S')}}</p>
                   </div>
               </li>
           {% endfor %}
       </ul> -->
