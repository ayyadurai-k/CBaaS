param (
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Path to your dev compose file
$compose = "docker-compose.dev.yml"

switch ($Command) {
    "up" {
        docker compose -f $compose up -d
    }
    "down" {
        docker compose -f $compose down
    }
    "logs" {
        docker compose -f $compose logs -f
    }
    "logs-web" {
        docker compose -f $compose logs -f web
    }
    "logs-frontend" {
        docker compose -f $compose logs -f frontend
    }
    "migrate" {
        docker compose -f $compose run --rm web python manage.py migrate
    }
    "makemigrations" {
        docker compose -f $compose run --rm web python manage.py makemigrations
    }
    "superuser" {
        docker compose -f $compose run --rm web python manage.py createsuperuser
    }
    "restart-web" {
        docker compose -f $compose restart web
    }
    "restart-frontend" {
        docker compose -f $compose restart frontend
    }
    "restart-worker" {
        docker compose -f $compose restart worker
    }
    "logs-worker" {
        docker compose -f $compose logs -f worker
    }
    "ps" {
        docker compose -f $compose ps
    }
    "help" {
        Write-Host "Usage: ./tasks.ps1 <command>"
        Write-Host "Available commands:"
        Write-Host "  up               Start all services"
        Write-Host "  down             Stop all services"
        Write-Host "  logs             Tail logs for all"
        Write-Host "  logs-web         Tail backend logs"
        Write-Host "  logs-frontend    Tail frontend logs"
        Write-Host "  logs-worker      Tail Celery worker logs"
        Write-Host "  migrate          Run Django migrations"
        Write-Host "  makemigrations   Create new migrations"
        Write-Host "  superuser        Create Django superuser"
        Write-Host "  restart-web      Restart backend"
        Write-Host "  restart-frontend Restart frontend"
        Write-Host "  restart-worker   Restart Celery worker"
        Write-Host "  ps               Show container status"
    }
    Default {
        Write-Host "Unknown command '$Command'. Run './tasks.ps1 help' for list."
    }
}
