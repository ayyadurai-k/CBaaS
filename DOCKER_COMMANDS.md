# 🐳 Docker Dev Commands for CBaaS

This document lists essential Docker Compose commands for managing the **CBaaS development stack**  
(Django + Celery + Redis + PostgreSQL + pgvector).  

---

## 🚀 Start & Stop Services

### Start all services (detached mode)

```bash
docker compose -f docker-compose.dev.yml up -d
```

### Stop all services

```bash
docker compose -f docker-compose.dev.yml down
```

### Stop & remove **everything** (including DB data)

⚠️ This will wipe your Postgres/Redis volumes.

```bash
docker compose -f docker-compose.dev.yml down -v
```

### Restart all services

```bash
docker compose -f docker-compose.dev.yml restart
```

### Restart a single service (e.g. web only)

```bash
docker compose -f docker-compose.dev.yml restart web
```

---

## 📊 Service Management

### Check running services

```bash
docker compose -f docker-compose.dev.yml ps
```

### View logs (all services)

```bash
docker compose -f docker-compose.dev.yml logs -f
```

### View logs for one service (e.g. worker)

```bash
docker compose -f docker-compose.dev.yml logs -f worker
```

---

## 🛠 Django Commands

### Create superuser

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Django shell

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py shell
```

### Run migrations

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

### Make migrations

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations
```

---

## 🧰 Container Shell Access

### Open a bash shell inside `web` container

```bash
docker compose -f docker-compose.dev.yml exec web bash
```

### Connect to Postgres (psql)

```bash
docker compose -f docker-compose.dev.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

### Connect to Redis

```bash
docker compose -f docker-compose.dev.yml exec redis redis-cli
```

---

## 🔄 Rebuild Images

### Rebuild everything

```bash
docker compose -f docker-compose.dev.yml up --build
```

### Rebuild a single service

```bash
docker compose -f docker-compose.dev.yml build web
```

---
