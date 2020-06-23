FROM python:3.5 as django
LABEL mantainer "hacklab/ <contato@hacklab.com.br>"
ENV PYTHONUNBUFFERED 1

ENV DJANGO_SETTINGS_MODULE config.settings.production
ARG DJANGO_AWS_ACCESS_KEY_ID
ARG DJANGO_AWS_SECRET_ACCESS_KEY
ARG DJANGO_AWS_STORAGE_BUCKET_NAME


RUN apt-get update &&\
    # dependencies for building Python packages
    apt-get install -y build-essential &&\
    # psycopg2 dependencies
    apt-get install -y libpq-dev &&\
    # Translations dependencies
    apt-get install -y gettext &&\
    # cleaning up unused files
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

COPY ./compose/production/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./compose/local/django/runserver.sh /gunicorn.sh
RUN sed -i 's/\r$//g' /gunicorn.sh
RUN chmod +x /gunicorn.sh

COPY . /app/

RUN export $(cat /app/env.example | grep -v ^# | xargs) && \
    python /app/manage.py collectstatic --noinput

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/gunicorn.sh"]
