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

- Given a task_id → return task status + results
- Tasks are displayed based on filters
- Build the full “frontend API” users will use later.
- Task id page is where the task type (config) is created

### Service 2 revisit

- add schedulers

### Polishing

- look for inplace processing
<!-- (so that we can get rid of output folder & saving the file twice) -->
- lifespan instead of on_event startup
- datetime.utcnow replace
- proper task service
- add loggers
