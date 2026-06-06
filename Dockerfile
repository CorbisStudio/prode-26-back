FROM python:3.13-slim

WORKDIR /app

RUN pip install --upgrade pip "setuptools<70.4.0" wheel
RUN pip install poetry

COPY pyproject.toml /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-root

EXPOSE 8000

COPY src /app/

# CMD de producción (web). Worker y beat sobreescriben el command en sus deployments.
# migrate + collectstatic corren en el arranque del contenedor web (patrón de la skill).
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn prode.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
