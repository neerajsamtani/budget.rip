# Docker Containerization Guide for Budget.rip

**Goal:** By the end of this guide, you'll understand Docker fundamentals and have a fully containerized application that runs identically on your laptop, a colleague's machine, and production servers.

**Time:** 2-3 hours

---

## Part 1: Understanding the Problem (15 min)

### The "Works on My Machine" Problem

Before Docker, our auditor found these issues:

```
Developer A's machine:
- Python 3.11
- PostgreSQL 14
- MongoDB 5.0
- Uses localhost URLs

Developer B's machine:
- Python 3.13
- PostgreSQL 16
- No MongoDB installed
- Different environment setup

Production VPS:
- Python 3.12
- Managed PostgreSQL (PlanetScale)
- Managed MongoDB (Atlas)
- Different connection strings
```

**Result:** Code works on A's machine, breaks on B's machine, behaves differently in production.

### Docker's Solution

Docker packages your app + dependencies into a **container** - a lightweight, isolated environment that runs identically everywhere.

```
┌─────────────────────────────────────────┐
│  Docker Container                       │
│  ┌─────────────────────────────────┐   │
│  │  Your App                       │   │
│  │  + Python 3.12                  │   │
│  │  + All dependencies             │   │
│  │  + Configuration                │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
     Runs the same on ANY machine
```

---

## Part 2: Core Concepts (20 min)

### Key Terms

| Term | Analogy | Technical Definition |
|------|---------|---------------------|
| **Image** | Recipe | Read-only template with your app + dependencies |
| **Container** | Dish made from recipe | Running instance of an image |
| **Dockerfile** | Recipe card | Instructions to build an image |
| **Docker Compose** | Meal plan | Orchestrates multiple containers |
| **Volume** | Storage box | Persistent data that survives container restarts |

### Exercise 1: Your First Container

```bash
# Pull and run a simple container
docker run hello-world

# What happened?
# 1. Docker downloaded the "hello-world" image
# 2. Created a container from that image
# 3. Ran the container
# 4. Container printed a message and exited
```

**Check your understanding:**
- What's the difference between an image and a container?
- Where did the `hello-world` image come from? (Hint: Docker Hub)

---

## Part 3: Building Your First Dockerfile (45 min)

### Understanding Our Backend

Our Flask backend needs:
- Python 3.12
- Dependencies from `pyproject.toml`
- Application code
- Gunicorn to run the server

### Exercise 2: Write a Simple Dockerfile

Create `server/Dockerfile.simple` (we'll improve it later):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv and dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
RUN uv sync --frozen

# Copy application code
COPY . .

# Run the server
CMD ["gunicorn", "--bind", "0.0.0.0:4242", "application:application"]
```

**Build and run it:**

```bash
cd server
docker build -f Dockerfile.simple -t budgit-backend-simple .
docker run -p 4242:4242 budgit-backend-simple
```

**What each line does:**

- `FROM python:3.12-slim` - Start with a base image that has Python installed
- `WORKDIR /app` - Set working directory inside container
- `COPY pyproject.toml .` - Copy files from your machine into the container
- `RUN uv sync` - Execute commands while building the image
- `CMD [...]` - Command to run when container starts

### Exercise 3: Understanding Layers

Docker images are built in layers. Each instruction creates a new layer.

```bash
# See the layers
docker history budgit-backend-simple
```

**Key insight:** Layers are cached. If you change your Python code but not `pyproject.toml`, Docker reuses the dependency installation layer. This makes rebuilds fast!

**Question:** Why do we `COPY pyproject.toml` before `COPY . .`?

<details>
<summary>Answer</summary>
Layer caching! Dependencies rarely change, but code changes often. By copying dependencies first, Docker can reuse that layer when only code changes.
</details>

### Exercise 4: Multi-Stage Builds

Our simple Dockerfile includes build tools (uv, compilers) in the final image. We only need those during installation, not at runtime.

**Multi-stage builds** solve this:

```dockerfile
# Stage 1: Install dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: Runtime image (smaller, more secure)
FROM python:3.12-slim AS production
WORKDIR /app

# Install only runtime dependencies (psycopg2-binary needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
CMD ["gunicorn", "--bind", "0.0.0.0:4242", "application:application"]
```

**Build and compare sizes:**

```bash
docker build -f Dockerfile.simple -t budgit-simple .
docker build -f Dockerfile -t budgit-optimized .
docker images | grep budgit
```

You should see `budgit-optimized` is significantly smaller!

**Check your understanding:**
- Why is the optimized image smaller?
- When would multi-stage builds NOT be beneficial?

---

## Part 4: Frontend Container (30 min)

### Understanding the Frontend Build Process

React apps have two modes:

1. **Development:** `npm run start` - Vite dev server with hot reload
2. **Production:** `npm run build` → static files (HTML, JS, CSS)

For production, we need to:
1. Build the static files
2. Serve them with a web server (nginx)

### Exercise 5: Frontend Multi-Stage Build

Create `client/Dockerfile`:

```dockerfile
# Build stage
FROM node:24-slim AS builder
WORKDIR /app

# Build-time environment variables (baked into JS bundle)
ARG VITE_API_ENDPOINT=http://localhost:4242
ARG VITE_STRIPE_PUBLIC_KEY
ENV VITE_API_ENDPOINT=$VITE_API_ENDPOINT
ENV VITE_STRIPE_PUBLIC_KEY=$VITE_STRIPE_PUBLIC_KEY

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Key concept: Build Args vs Environment Variables**

- **Build Args (`ARG`)**: Set when building the image, baked into the code
- **Environment Variables (`ENV` at runtime)**: Set when running the container

For React/Vite, the API URL is baked in at build time because the JavaScript bundle is created during `npm run build`.

**Test it:**

```bash
cd client
docker build --build-arg VITE_API_ENDPOINT=http://localhost:4242 \
             --build-arg VITE_STRIPE_PUBLIC_KEY=pk_test_example \
             -t budgit-frontend .
docker run -p 8080:80 budgit-frontend
# Visit http://localhost:8080
```

---

## Part 5: Docker Networking (30 min)

### The Problem

Your backend needs to talk to PostgreSQL. How do containers find each other?

### Exercise 6: Manual Container Networking

```bash
# Create a network
docker network create budgit-net

# Run PostgreSQL
docker run -d --name db --network budgit-net \
  -e POSTGRES_USER=budgit_user \
  -e POSTGRES_PASSWORD=budgit_password \
  -e POSTGRES_DB=budgit \
  postgres:16-alpine

# Run backend (connected to same network)
docker run -d --name backend --network budgit-net \
  -e DATABASE_URL=postgresql://budgit_user:budgit_password@db:5432/budgit \
  -p 4242:4242 \
  budgit-backend

# Backend can now reach PostgreSQL using hostname "db"!
```

**Key insight:** Containers on the same network can reach each other by **container name** as hostname.

**Clean up:**
```bash
docker stop backend db
docker rm backend db
docker network rm budgit-net
```

---

## Part 6: Docker Compose - Orchestration Made Easy (45 min)

Running containers manually is tedious. Docker Compose automates this.

### Exercise 7: Your First Compose File

Create `docker-compose.yml`:

```yaml
services:
  backend:
    build: ./server
    ports:
      - "4242:4242"
    environment:
      - DATABASE_URL=postgresql://budgit_user:budgit_password@postgres:5432/budgit
      - MONGO_URI=mongodb://mongodb:27017/budgit
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - budgit-network

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=budgit_user
      - POSTGRES_PASSWORD=budgit_password
      - POSTGRES_DB=budgit
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U budgit_user -d budgit"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - budgit-network

networks:
  budgit-network:
    driver: bridge

volumes:
  postgres_data:
```

**Run it:**

```bash
docker compose up
# Or in detached mode:
docker compose up -d
```

**Compose does all the hard work:**
- Creates the network
- Builds images if needed
- Starts containers in the right order
- Sets up volume mounts

**Useful commands:**

```bash
docker compose ps           # List running services
docker compose logs -f      # Follow logs
docker compose down         # Stop and remove everything
docker compose down -v      # Also remove volumes
docker compose restart      # Restart services
```

### Exercise 8: Environment Variables from File

Hardcoding secrets in `docker-compose.yml` is bad. Use `.env` files:

**Create `.env`:**
```bash
POSTGRES_PASSWORD=super_secret
JWT_SECRET_KEY=very_secret_key
VITE_API_ENDPOINT=http://localhost:4242
```

**Update `docker-compose.yml`:**
```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://budgit_user:${POSTGRES_PASSWORD}@postgres:5432/budgit
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
```

Docker Compose automatically loads `.env` files!

---

## Part 7: Development vs Production (30 min)

### The Challenge

You want different setups for development and production:

| | Development | Production |
|---|-------------|------------|
| Code changes | Hot reload | Optimized build |
| Databases | Local containers | Managed (PlanetScale, Atlas) |
| Build | Faster (use builder stage) | Smaller (production stage) |
| Debug | Enabled | Disabled |

### Exercise 9: Compose Override Files

Docker Compose supports **override files** that extend the base configuration.

**Base: `docker-compose.yml`** (used by everyone)
```yaml
services:
  backend:
    build: ./server
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

**Dev: `docker-compose.dev.yml`** (local development)
```yaml
services:
  backend:
    build:
      target: builder  # Use builder stage for dev tools
    command: sh -c "uv sync && uv run python application.py"
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
    volumes:
      - ./server:/app  # Mount code for hot reload
      - /app/.venv     # Don't mount .venv (use container's)
```

**Run with override:**
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## Part 8: Production Deployment (30 min)

### Architecture with Managed Databases

```
┌─────────────────────────────────────────────────────┐
│  Your VPS (runs containers)                         │
│  ┌──────────────┐    ┌──────────────┐              │
│  │   backend    │    │  frontend    │              │
│  │   (Flask)    │    │   (nginx)    │              │
│  └──────┬───────┘    └──────────────┘              │
└─────────│──────────────────────────────────────────┘
          │
          ├─── DATABASE_URL → PlanetScale (managed)
          └─── MONGO_URI → MongoDB Atlas (managed)
```

### Exercise 10: Production Compose File

Create `docker-compose.prod.yml`:

```yaml
services:
  backend:
    build:
      context: ./server
      target: production
    environment:
      - DATABASE_URL=${DATABASE_URL}  # From managed PlanetScale
      - MONGO_URI=${MONGO_URI}        # From managed Atlas
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
    restart: unless-stopped

  frontend:
    build:
      context: ./client
      args:
        VITE_API_ENDPOINT: ${VITE_API_ENDPOINT}
        VITE_STRIPE_PUBLIC_KEY: ${VITE_STRIPE_PUBLIC_KEY}
    restart: unless-stopped

  # No postgres or mongodb containers - using managed services!
```

**Deploy to VPS:**

```bash
# On your VPS
git clone <your-repo>
cd budget.rip

# Create production .env
cat > .env << EOF
DATABASE_URL=postgresql://user:pass@aws.connect.psdb.cloud/budgit
MONGO_URI=mongodb+srv://cluster.mongodb.net/budgit
JWT_SECRET_KEY=$(openssl rand -hex 32)
VITE_API_ENDPOINT=https://api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
EOF

# Build and run
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

---

## Part 9: Best Practices (15 min)

### 1. Use .dockerignore

Like `.gitignore` but for Docker. Prevents copying unnecessary files into the image.

**`server/.dockerignore`:**
```
.git
.venv
__pycache__
*.pyc
.env
.env.*
```

### 2. Security

```dockerfile
# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --create-home appuser
USER appuser

# Never commit .env files
.env
.env.*
!.env.example
```

### 3. Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4242/api/')"
```

### 4. Image Size Optimization

- Use `alpine` variants when possible: `python:3.12-alpine`
- Multi-stage builds
- Clean up in the same layer:
  ```dockerfile
  RUN apt-get update && apt-get install -y pkg \
      && rm -rf /var/lib/apt/lists/*
  ```

---

## Part 10: Debugging & Troubleshooting (20 min)

### Common Issues and Solutions

**Issue: Container exits immediately**
```bash
docker compose logs backend
docker compose ps  # Check exit code
```

**Issue: Cannot connect to database**
```bash
# Enter the backend container
docker compose exec backend sh

# Try to ping postgres
ping postgres  # Should resolve!

# Check DATABASE_URL
echo $DATABASE_URL

# Try connecting manually
psql $DATABASE_URL
```

**Issue: Code changes not reflecting**
```bash
# For development (with volumes), restart:
docker compose restart backend

# For production (no volumes), rebuild:
docker compose build backend
docker compose up -d backend
```

**Issue: Port already in use**
```bash
# Find what's using port 4242
lsof -i :4242
# Kill it or change the port in docker-compose.yml
```

---

## Part 11: Verification Checklist

By now, you should be able to:

- [ ] Explain the difference between an image and a container
- [ ] Write a Dockerfile from scratch
- [ ] Understand multi-stage builds and their benefits
- [ ] Build and run a container
- [ ] Explain layer caching and optimization
- [ ] Create a docker-compose.yml orchestrating multiple services
- [ ] Use environment variables and .env files
- [ ] Understand Docker networking (how containers communicate)
- [ ] Differentiate between build args and runtime env vars
- [ ] Set up different configurations for dev vs production
- [ ] Deploy containers to a VPS
- [ ] Debug container issues

---

## Final Exercise: Deploy Budget.rip

**Objective:** Get the full stack running on your local machine using Docker.

```bash
# 1. Clone the repo
git clone <repo-url>
cd budget.rip

# 2. Create .env from example
cp .env.example .env
# Fill in the required values (use dummy values for local dev)

# 3. Start everything
docker compose up -d

# 4. Check it's working
docker compose ps
# All services should be "healthy"

# 5. Access the app
# Frontend: http://localhost:5173
# Backend API: http://localhost:4242/api/

# 6. View logs
docker compose logs -f

# 7. Stop everything
docker compose down
```

**Success criteria:**
- All containers start and stay healthy
- Frontend loads in browser
- Backend API responds
- Database connections work

---

## Going Deeper

### Recommended Reading

1. [Official Docker Tutorial](https://docs.docker.com/get-started/)
2. [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
3. [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
4. [Compose Specification](https://docs.docker.com/compose/compose-file/)

### Next Steps

- Set up CI/CD to build images automatically
- Learn Kubernetes for orchestrating containers at scale
- Explore Docker security scanning
- Implement blue-green deployments

---

## Questions to Test Understanding

1. **Why do we use multi-stage builds?**
2. **What's the difference between `COPY` and `ADD`?**
3. **When should you use `CMD` vs `ENTRYPOINT`?**
4. **How does Docker layer caching work?**
5. **Why do frontend env vars need to be build args?**
6. **What happens if you don't specify a `volumes` section in compose?**
7. **How would you debug a container that keeps crashing?**

Good luck! You now understand containerization better than most developers.
