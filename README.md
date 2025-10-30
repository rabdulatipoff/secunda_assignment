# Secunda Assignment API
A FastAPI-based "yellow pages" application implementing an asynchronous API for querying spatial and other information about buildings and organizations.

- All models/schemas are type-checked and validated where necessary
- Each organization has a name, a residential building, may have multiple phones and business categories assigned to it
- Each building has a name and a coordinate point, specifying its location
- Phone numbers has a type and its organization ID
- Business categories have a name and can be nested (up to 3 levels of depth)

## Local Installation
The following instructions assume running on a Debian-based distribution with access to APT.
``` sh
sudo apt install pipx
pipx install poetry

cd secunda_assignment
# Install dependencies
poetry install
# Get poetry shell
eval $(poetry env activate)

# Provide dotenv configuration
cp .env.example .env.local
cp .env.example .env.docker
set -a; . ./.env.local; set +a

# Replace the database hostname
sed -i "s/\<localhost\>/db/g" .env.docker

# Configure the database
docker compose up -d db
PGPASSWORD=<db_password> psql -hlocalhost -p5432 -Uapp_user app_db < src/secunda_assignment/storage/sql/init.sql

# Populate the database
python -m secunda_assignment.seed

# Run the app in production mode
fastapi run src/secunda_assignment/main.py
```

## Docker deployment

``` sh
# Provide dotenv configuration (if not done before)
cp .env.example .env.local
cp .env.example .env.docker
# Replace the database hostname
sed -i "s/\<localhost\>/db/g" .env.docker

# Export environment variables for Docker
set -a; . ./.env.docker; set +a

# Build and run the containers
docker compose up -d --build

# Populate the database (exposed on localhost)
set -a; . ./.env.local; set +a
python -m secunda_assignment.seed

# Monitor logs
docker compose logs -f
```

You can observe the application API endpoints at http://localhost:8000/docs
