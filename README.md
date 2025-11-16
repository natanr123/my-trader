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

### To start the backend with docker-compose:

cd backend

uv sync

docker compose watch

Server should start on localhost:8000

### To start the frontend without docker-compose:

npm run dev:

Frontend should start on localhost:5174




