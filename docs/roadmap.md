# EvalHub Roadmap

## Day 10 baseline

- JSONL dataset loading and validation
- Exact Match evaluation
- Mock Provider abstraction
- Pydantic request and response validation
- SQLite datasets, jobs and runs with full CRUD
- Public repository, architecture document and automated tests

## Day 11–20

1. Git and GitHub feature-to-PR workflow
2. HTTP and REST debugging
3. Async calls, queues, workers and concurrency limits
4. FastAPI request and response APIs
5. Structured errors, dependency injection and logging
6. SQLAlchemy repositories
7. Pytest fixtures, parameterization and mocks
8. Docker and persistent SQLite storage

## Known risks

- Concurrent SQLite writes require deliberate transaction boundaries.
- Pydantic fields and database columns can drift if changed independently.
- Real model APIs introduce timeouts, rate limits and secret management.
- Tests must cover failures as well as successful paths.
