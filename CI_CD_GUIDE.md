# CI/CD Guide for Budget.rip

**Goal:** Automate building Docker images and deploying them to your VPS whenever code is pushed to the main branch.

**Prerequisites:** Complete `DOCKER_GUIDE.md` first.

**Time:** 2-3 hours

---

## Part 1: Understanding CI/CD (20 min)

### What is CI/CD?

**CI (Continuous Integration)**: Automatically test and build code when changes are pushed.

**CD (Continuous Deployment)**: Automatically deploy passing builds to production.

### The Problem Without CI/CD

```
Developer workflow (manual):
1. Write code
2. Run tests locally (maybe... if you remember)
3. Commit and push
4. SSH into VPS
5. git pull
6. docker compose build
7. docker compose up -d
8. Hope nothing broke
9. Repeat for every change

Problems:
- Forgot to test? Broken code in production
- Deployment steps inconsistent? Different behavior each time
- Manual SSH deployment? Slow and error-prone
```

### The Solution: Automated Pipeline

```
Push to GitHub → Tests run → Build Docker images → Push to registry → Deploy to VPS
     ↓              ↓              ↓                    ↓                 ↓
 Automatic     Automatic      Automatic            Automatic         Automatic
```

---

## Part 2: Understanding Your Current CI (30 min)

You already have CI set up! Let's understand what it does.

### Exercise 1: Analyze Existing Workflows

**File: `.github/workflows/python-app.yml`**

```yaml
name: Python application

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        # ... health checks

    steps:
    - uses: actions/checkout@v3
    - name: Install uv
      # ...
    - name: Lint and format with ruff
      run: make lint
    - name: Test with pytest
      run: make test
```

**What this does:**
1. **Trigger** (`on:`): Runs when code is pushed to `main` or when PRs are opened
2. **Environment** (`runs-on:`): Creates a fresh Ubuntu VM
3. **Services** (`services:`): Starts PostgreSQL container for tests
4. **Steps**: Checkout code → Install deps → Lint → Test

**Check your understanding:**
- When does this workflow run?
- Why does it start a PostgreSQL container?
- What happens if tests fail?

<details>
<summary>Answers</summary>

- Runs on every push to main and every PR
- Tests need a database to run against
- The workflow fails, preventing merge if it's a PR
</details>

### Exercise 2: Trigger a Workflow

```bash
# Make a trivial change
echo "# Test CI" >> README.md
git add README.md
git commit -m "Test CI pipeline"
git push

# Watch it run
# Go to: https://github.com/your-username/budget.rip/actions
```

**Observe:**
- The workflow starts automatically
- Each step shows logs in real-time
- Green checkmark = success, red X = failure

---

## Part 3: Docker Image Building in CI (45 min)

Now let's extend CI to build Docker images.

### Why Build Images in CI?

1. **Consistency**: Same build environment every time
2. **Testing**: Ensure images actually build before deploying
3. **Automation**: No manual `docker build` commands
4. **Registry**: Push images to a central registry for deployment

### Exercise 3: Add Docker Build Step

Create a new workflow: `.github/workflows/docker-build.yml`

```yaml
name: Build Docker Images

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build-backend:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build backend image
      uses: docker/build-push-action@v5
      with:
        context: ./server
        file: ./server/Dockerfile
        push: false  # Don't push yet, just test building
        tags: budgit-backend:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max

  build-frontend:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build frontend image
      uses: docker/build-push-action@v5
      with:
        context: ./client
        file: ./client/Dockerfile
        build-args: |
          VITE_API_ENDPOINT=https://api.budget.rip
          VITE_STRIPE_PUBLIC_KEY=${{ secrets.VITE_STRIPE_PUBLIC_KEY }}
        push: false
        tags: budgit-frontend:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

**Key concepts:**

- **Buildx**: Docker's advanced build engine with caching
- **cache-from/cache-to**: Speeds up builds by reusing layers across CI runs
- **build-args**: Pass environment variables at build time
- **secrets**: Access GitHub secrets (we'll set these up next)

**Test it:**

```bash
git add .github/workflows/docker-build.yml
git commit -m "Add Docker build workflow"
git push
```

Watch the workflow in GitHub Actions. Both images should build successfully.

---

## Part 4: Pushing to a Container Registry (30 min)

Built images need to be stored somewhere accessible to your VPS.

### Registry Options

| Registry | Pros | Cons |
|----------|------|------|
| Docker Hub | Easy, free tier | Public images (unless paid) |
| GitHub Container Registry (ghcr.io) | Integrated with GitHub, private | Slightly more setup |
| AWS ECR, Google GCR | Production-grade | More complex, requires cloud account |

We'll use **GitHub Container Registry** (free and private).

### Exercise 4: Set Up GitHub Container Registry

**1. Create a Personal Access Token (PAT)**

- Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
- Generate new token
- Scopes: `write:packages`, `read:packages`, `delete:packages`
- Copy the token

**2. Add it as a repository secret**

- Go to your repo → Settings → Secrets and variables → Actions
- New repository secret:
  - Name: `GHCR_TOKEN`
  - Value: Your PAT

**3. Update the workflow to push images**

Edit `.github/workflows/docker-build.yml`:

```yaml
jobs:
  build-and-push-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ghcr.io/${{ github.repository }}/backend
        tags: |
          type=sha,prefix={{branch}}-
          type=ref,event=branch
          type=semver,pattern={{version}}

    - name: Build and push backend
      uses: docker/build-push-action@v5
      with:
        context: ./server
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

**What changed:**

- **permissions**: Grants workflow access to push packages
- **docker/login-action**: Authenticates with ghcr.io
- **metadata-action**: Generates smart image tags:
  - `main-abc123` (branch + commit SHA)
  - `main` (branch name)
  - `v1.2.3` (if you tag releases)
- **push**: Only push on pushes to main, not on PRs

**Test it:**

```bash
git add .github/workflows/docker-build.yml
git commit -m "Push images to GHCR"
git push
```

After the workflow completes, check:
- GitHub → Your repo → Packages
- You should see `backend` and `frontend` packages

---

## Part 5: Automated Deployment to VPS (60 min)

Now the exciting part: automatically deploying to your VPS.

### Deployment Strategies

| Strategy | Downtime | Complexity | Rollback |
|----------|----------|------------|----------|
| **Recreate** | Yes (~30s) | Simple | Manual |
| **Rolling update** | No | Medium | Automatic |
| **Blue-green** | No | Complex | Instant |

We'll implement **recreate** (simple, good for low-traffic apps).

### Exercise 5: Set Up SSH Access

**On your VPS:**

```bash
# Create a dedicated deploy user
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh

# Generate SSH key FOR GITHUB ACTIONS (run this locally)
ssh-keygen -t ed25519 -C "github-actions" -f github-actions-deploy-key
# Don't set a passphrase (press Enter)

# Copy the public key to VPS
cat github-actions-deploy-key.pub
# SSH into VPS and add it:
sudo nano /home/deploy/.ssh/authorized_keys
# Paste the public key, save and exit

sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
```

**Add private key to GitHub:**

```bash
# Copy the private key (locally)
cat github-actions-deploy-key

# GitHub repo → Settings → Secrets → New secret
# Name: SSH_PRIVATE_KEY
# Value: Paste the entire private key
```

**Add VPS details as secrets:**

- `VPS_HOST`: Your VPS IP (e.g., `123.45.67.89`)
- `VPS_USER`: `deploy`
- `VPS_PORT`: `22` (or your SSH port)

### Exercise 6: Create Deployment Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [ "main" ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    # Only deploy if tests pass
    needs: [test-backend, test-frontend]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Deploy to VPS
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        port: ${{ secrets.VPS_PORT }}
        script: |
          cd /home/deploy/budget.rip

          # Pull latest code
          git pull origin main

          # Pull latest Docker images
          echo ${{ secrets.GHCR_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker compose pull

          # Restart services
          docker compose down
          docker compose up -d

          # Clean up old images
          docker image prune -f
```

**What this does:**

1. **needs**: Waits for tests to pass before deploying
2. **ssh-action**: SSHs into your VPS and runs commands
3. **Commands**:
   - Pull latest code
   - Pull latest Docker images from registry
   - Restart containers
   - Clean up old images (saves disk space)

### Exercise 7: Prepare Your VPS

**On your VPS:**

```bash
# Switch to deploy user
sudo su - deploy

# Clone your repo
git clone https://github.com/your-username/budget.rip.git
cd budget.rip

# Create .env file
nano .env
# Add your production environment variables:
DATABASE_URL=postgresql://user:pass@your-planetscale-url/db
MONGO_URI=mongodb+srv://your-atlas-url/db
JWT_SECRET_KEY=your-secret-key
VITE_API_ENDPOINT=https://api.yourdomain.com
# ... etc

# Create docker-compose.prod.yml (no database containers)
nano docker-compose.prod.yml
```

**docker-compose.prod.yml:**

```yaml
services:
  backend:
    image: ghcr.io/your-username/budget.rip/backend:main
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - MONGO_URI=${MONGO_URI}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      # ... all other env vars
    restart: unless-stopped
    ports:
      - "4242:4242"

  frontend:
    image: ghcr.io/your-username/budget.rip/frontend:main
    restart: unless-stopped
    ports:
      - "80:80"
```

**Set docker-compose to use prod file by default:**

```bash
# Create a symbolic link or use env var
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env
```

**Test manual deployment:**

```bash
docker compose pull
docker compose up -d
docker compose ps  # Should show both services running
```

---

## Part 6: Complete Pipeline (30 min)

Let's put it all together with a complete workflow that tests, builds, and deploys.

### Exercise 8: Unified CI/CD Pipeline

Create `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  # ============================================================================
  # TEST STAGE
  # ============================================================================
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: budgit_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v3
    - name: Set up Python
      run: uv python install 3.12
    - name: Start MongoDB
      uses: supercharge/mongodb-github-action@1.10.0
      with:
        mongodb-version: '6.0'
    - name: Install dependencies
      run: cd server && uv sync
    - name: Lint
      run: cd server && make lint
    - name: Test
      run: cd server && make test
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/budgit_test

  test-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: 24.8.0
        cache: 'npm'
        cache-dependency-path: client/package-lock.json
    - run: cd client && npm ci --legacy-peer-deps
    - run: cd client && npm run build
    - run: cd client && npm test

  # ============================================================================
  # BUILD & PUSH STAGE (only on main branch)
  # ============================================================================
  build-and-push:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to GHCR
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push backend
      uses: docker/build-push-action@v5
      with:
        context: ./server
        push: true
        tags: ghcr.io/${{ github.repository }}/backend:main
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Build and push frontend
      uses: docker/build-push-action@v5
      with:
        context: ./client
        build-args: |
          VITE_API_ENDPOINT=${{ secrets.VITE_API_ENDPOINT }}
          VITE_STRIPE_PUBLIC_KEY=${{ secrets.VITE_STRIPE_PUBLIC_KEY }}
        push: true
        tags: ghcr.io/${{ github.repository }}/frontend:main
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # ============================================================================
  # DEPLOY STAGE (only on main branch, after build)
  # ============================================================================
  deploy:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
    - name: Deploy to VPS
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        port: ${{ secrets.VPS_PORT }}
        script: |
          cd /home/deploy/budget.rip
          git pull origin main
          docker compose pull
          docker compose up -d --remove-orphans
          docker image prune -f

    - name: Verify deployment
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /home/deploy/budget.rip
          docker compose ps
          curl -f http://localhost:4242/api/ || exit 1
```

**Pipeline flow:**

```
┌──────────────────────────────────────────────────────┐
│  PULL REQUEST                                        │
├──────────────────────────────────────────────────────┤
│  test-backend ──┐                                    │
│                 ├─> Tests pass? → Merge allowed      │
│  test-frontend ─┘                                    │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  PUSH TO MAIN                                        │
├──────────────────────────────────────────────────────┤
│  test-backend ──┐                                    │
│                 ├─> Tests pass?                      │
│  test-frontend ─┘      │                             │
│                        ▼                             │
│  build-and-push ──> Push images to GHCR             │
│                        │                             │
│                        ▼                             │
│  deploy ──────────> Update VPS                       │
│                        │                             │
│                        ▼                             │
│  verify ────────> Health check                       │
└──────────────────────────────────────────────────────┘
```

---

## Part 7: Advanced Topics (20 min)

### Environment-Specific Deployments

Add staging environment:

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    steps:
    - name: Deploy to staging
      # ... deploy to staging.yourdomain.com

  deploy-production:
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to production
      # ... deploy to yourdomain.com
```

### Rollback Strategy

If deployment fails, automatically rollback:

```yaml
- name: Deploy with rollback
  uses: appleboy/ssh-action@v1.0.0
  with:
    script: |
      cd /home/deploy/budget.rip

      # Tag current images as backup
      docker tag ghcr.io/.../backend:main ghcr.io/.../backend:backup

      # Pull and deploy new version
      docker compose pull
      docker compose up -d

      # Health check
      sleep 10
      if ! curl -f http://localhost:4242/api/; then
        echo "Deployment failed, rolling back"
        docker tag ghcr.io/.../backend:backup ghcr.io/.../backend:main
        docker compose up -d
        exit 1
      fi
```

### Slack Notifications

Get notified when deployments complete:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    payload: |
      {
        "text": "Deployment ${{ job.status }}: ${{ github.sha }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Part 8: Security Best Practices (20 min)

### 1. Secrets Management

**Never commit secrets!**

```bash
# BAD - hardcoded in workflow
env:
  API_KEY: "sk_live_abc123"

# GOOD - from GitHub secrets
env:
  API_KEY: ${{ secrets.API_KEY }}
```

### 2. Image Scanning

Add vulnerability scanning:

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ghcr.io/${{ github.repository }}/backend:main
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload results
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

### 3. Least Privilege

```yaml
permissions:
  contents: read      # Can read code
  packages: write     # Can push images
  # NOT: admin access, write to main branch, etc.
```

### 4. Branch Protection

Enable in GitHub repo settings:
- Require pull request reviews before merging
- Require status checks to pass (CI tests)
- Require branches to be up to date
- Don't allow force push to main

---

## Part 9: Monitoring & Debugging (15 min)

### View Workflow Runs

```
GitHub repo → Actions tab
- Click on a workflow run
- Click on a job to see logs
- Download logs for offline analysis
```

### Common Issues

**1. Tests fail in CI but pass locally**

```yaml
# Add debug step
- name: Debug environment
  run: |
    python --version
    node --version
    docker --version
    env | sort
```

**2. SSH connection fails**

```bash
# Test SSH locally
ssh -i github-actions-deploy-key deploy@your-vps-ip

# Check VPS logs
sudo journalctl -u ssh -n 50
```

**3. Docker pull fails on VPS**

```bash
# On VPS, manually login
echo $GHCR_TOKEN | docker login ghcr.io -u your-username --password-stdin

# Test pulling
docker pull ghcr.io/your-username/budget.rip/backend:main
```

**4. Out of disk space**

```bash
# On VPS, clean up
docker system prune -a
docker volume prune
```

---

## Part 10: Verification Checklist

By now, you should be able to:

- [ ] Explain what CI/CD is and why it matters
- [ ] Understand GitHub Actions workflow syntax
- [ ] Read and modify existing workflows
- [ ] Build Docker images in CI
- [ ] Push images to a container registry
- [ ] Set up SSH access for deployments
- [ ] Deploy containers to a VPS automatically
- [ ] Use GitHub secrets for sensitive data
- [ ] Implement basic rollback strategies
- [ ] Debug failed CI/CD pipelines
- [ ] Scan images for vulnerabilities

---

## Final Exercise: Complete CI/CD Pipeline

**Objective:** Set up the full pipeline for Budget.rip.

**Steps:**

1. **Add all secrets to GitHub:**
   - `VPS_HOST`, `VPS_USER`, `SSH_PRIVATE_KEY`, `VPS_PORT`
   - `VITE_API_ENDPOINT`, `VITE_STRIPE_PUBLIC_KEY`

2. **Create unified workflow:**
   - Copy the `ci-cd.yml` from Part 6
   - Adjust image names to match your repo

3. **Set up VPS:**
   - Create deploy user
   - Clone repo
   - Add `.env` file
   - Create `docker-compose.prod.yml`

4. **Test the pipeline:**
   ```bash
   # Make a small change
   echo "CI/CD test" >> README.md
   git add README.md
   git commit -m "Test full CI/CD pipeline"
   git push origin main

   # Watch in GitHub Actions
   # Should: test → build → push → deploy
   ```

5. **Verify deployment:**
   - Visit your VPS: `http://your-vps-ip`
   - Check containers: `ssh deploy@vps "docker compose ps"`
   - Check logs: `ssh deploy@vps "docker compose logs -f"`

**Success criteria:**
- ✅ Workflow completes all stages
- ✅ Images are in GHCR
- ✅ VPS containers are running
- ✅ Application is accessible
- ✅ Changes deploy automatically on push

---

## Next Steps

### Improvements to Implement

1. **Zero-downtime deployments**
   - Use Docker Swarm or Kubernetes
   - Implement health checks and rolling updates

2. **Database migrations**
   - Run Alembic migrations automatically before deployment
   - Add migration rollback on deployment failure

3. **Performance monitoring**
   - Add Prometheus + Grafana
   - Set up alerts for high CPU/memory

4. **Automated backups**
   - Schedule database backups
   - Store in S3 or similar

5. **Multi-environment setup**
   - Staging environment for testing
   - Production environment for users
   - Different workflows for each

---

## Questions to Test Understanding

1. **What's the difference between CI and CD?**
2. **Why do we push images to a registry instead of building on the VPS?**
3. **What would happen if you removed the `needs: [test-backend, test-frontend]` from the deploy job?**
4. **How would you rollback to a previous version if the new deployment breaks?**
5. **Why use GitHub Container Registry instead of Docker Hub?**
6. **What security risks exist in the deployment workflow?**
7. **How would you add a staging environment?**

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/marketplace/actions/build-and-push-docker-images)
- [SSH Action](https://github.com/marketplace/actions/ssh-remote-commands)
- [Secrets in GitHub Actions](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

Congratulations! You now have a production-grade CI/CD pipeline.
