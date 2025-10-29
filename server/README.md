# Budget.rip Backend

This is the Flask backend for Budget.rip.

## Running Tests

The backend tests require MongoDB and PostgreSQL databases. We've made this easy with Docker Compose!

### Prerequisites

- Docker and Docker Compose installed on your system
  - **macOS/Windows**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
  - **Linux**: Install `docker` and `docker-compose` packages

### Quick Start

Simply run:

```bash
python run_tests.py
# Or use the Makefile shortcut:
make test
```

This will:
1. ✓ Check if Docker is available
2. ✓ Start MongoDB and PostgreSQL test databases in containers
3. ✓ Wait for databases to be ready
4. ✓ Run database migrations
5. ✓ Execute all tests with pytest
6. ✓ Clean up and stop databases

### Advanced Usage

```bash
# Keep databases running after tests (useful for debugging)
python run_tests.py --keep-alive
# Or: make test-keep-alive

# Stop databases without running tests
python run_tests.py --stop-only
# Or: make test-stop

# Show help
python run_tests.py --help
# Or: make help
```

### Manual Database Management

If you prefer to manage the databases manually:

```bash
# Start databases
docker compose -f docker-compose.test.yml up -d

# Check database status
docker compose -f docker-compose.test.yml ps

# Run migrations
DATABASE_URL=postgresql://postgres:test_password@localhost:5432/budgit_test alembic upgrade head

# Run tests
TEST_MONGO_URI=mongodb://localhost:27017/budgit_test \
DATABASE_URL=postgresql://postgres:test_password@localhost:5432/budgit_test \
pytest

# Stop databases
docker compose -f docker-compose.test.yml down -v
```

### Database Connections

When databases are running, they're accessible at:

- **PostgreSQL**: `localhost:5432`
  - Database: `budgit_test`
  - User: `postgres`
  - Password: `test_password`

- **MongoDB**: `localhost:27017`
  - Database: `budgit_test`

### Troubleshooting

**Port conflicts**: If ports 5432 or 27017 are already in use, you'll need to stop the conflicting service first:

```bash
# Check what's using the ports
lsof -i :5432
lsof -i :27017

# Or stop all test containers
docker compose -f docker-compose.test.yml down
```

**Docker not available**: Make sure Docker Desktop is running (macOS/Windows) or the Docker daemon is started (Linux).

**Tests still failing**: Check the database logs:

```bash
docker compose -f docker-compose.test.yml logs postgres-test
docker compose -f docker-compose.test.yml logs mongodb-test
```

## Development

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Running the Server Locally

```bash
python app.py
```

### Database Migrations

We use Alembic for PostgreSQL migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Test Structure

- `tests/conftest.py` - pytest fixtures and test configuration
- `tests/test_*.py` - test modules for different components
- `docker-compose.test.yml` - test database definitions
- `run_tests.py` - automated test runner script
