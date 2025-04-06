FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# We do not specify "CMD" command here, since we do it in the docker compose file in 'app' service, because we use this 
# file to instantiate celery app container as well in the docker compose file.