Platform to trade on Alpaca stocks broker

It can be used to create smart bots

Using API from: https://alpaca.markets/

Based on FastAPI official fullstack template: https://github.com/fastapi/full-stack-fastapi-template

By default, the dotenv files that will be used will be in backend/dotenv/local

For tests, it will be loaded from backend/dotenv/test

For CI (GitHub actions), it will be loaded from backend/dotenv/ci-test-docker-compose

If you want to use another set of .env files please set the ENVIRONMENT, environment variable

Please notice that whichever db.env you choose it must match the POSTGRES credentials in the root .env 

Thank You

## To start the backend with docker-compose:

cd backend

uv sync

docker compose watch

Server should start on localhost:8000

### To recreate the superuser:

Set the credentials in backend/dotenv/local/super_user.env (or your necessary environment)

docker compose exec backend "python" "app/initial_data.py"

To lint the code: uv run bash scripts/lint.sh

## To start the frontend without docker-compose:

npm run dev:

If your backend is running on localhost:8000 then run this or replace the url with your backend url

echo 'VITE_API_URL=http://localhost:8000' > frontend/.env

Frontend should start on localhost:5174




