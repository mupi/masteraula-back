FROM python:3.6
LABEL mantainer "hacklab/ <contato@hacklab.com.br>"
ENV PYTHONUNBUFFERED 1

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

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/local.txt &&\
    rm -rf /requirements

COPY ./compose/production/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./compose/local/django/runserver.sh /runserver.sh
RUN sed -i 's/\r$//g' /runserver.sh
RUN chmod +x /runserver.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/runserver.sh"]
