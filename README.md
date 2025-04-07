'''
## This is a README file for this E-Wallet web backend project written in python utilizing Flask framework.
#### In this project you can find: 
#### - main Flask app;
#### - celery wotker;
#### - small logging configurations;
#### - utilization of SQLAlchemy and default SQLite database with unique constraint for "Transaction" table and Enum objects;
#### - JWT tokens for authentication and authorization; 
#### - Schema with modified Decimal field for fund for validation;
#### - Blueprints for managing routes/views;
#### - Redis serving as a message broker for a celery worker;
#### - Docker compose file to run docker "claster" container embedding Flask main app, celery worker and redis.
#### You can pull this project and run it locally either it be with docker compose or without. You may want to set up
#### your local environment for local testing, all requirements included.

#### _________________________

#### In case you want to run everyhing in the container "cd" to the "docker-compose" file directpry and execute:
#### "docker compose up"

#### _________________________

#### In case you want to run it locally without the docker compose pelase use the following instructions:
#### 1) So first let"s run our main app from the current directory:
#### "flask run" or "flask --app app run".
#### If you want to run it in debug mode execute add "--debug" at the end of either line.

#### 2) Now let"s run redis sicne ideally it"s need to be up and runnung before we run celry worker.
#### "docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest"
#### "-d" flag means "debug mode", so you can omit it for whatever reason you will have. And "--name" flag indicates
#### that after this flask we set the name of this container as "redis-stack-server", so you can change the name if you want.
#### "-p" flag means port forwarding, where first number"6379" before colon ":" is the port on your local machine and
#### the following "6379" means port in the container. After that we use image "redis/redis-stack-server:latest" for this
#### container.

#### 3) As soon as the redis container and main app are running we can start up our celery worker:
#### "celery -A make_celery worker --loglevel INFO"

#### _________________________

#### Just want to add that I am aspiring deeloper and the code can definitely be imperfect so I will be more than happy for
#### your constructive critique and suggestions.


#### Thank you for taking the time to review this project.

#### Kind regards,
'''
