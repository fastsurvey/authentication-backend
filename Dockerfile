FROM python:3.7

RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml pyproject.toml
RUN poetry install --no-dev
RUN pip list

EXPOSE 8080
COPY jwtRS256.key jwtRS256.key
COPY jwtRS256.key.pub jwtRS256.key.pub

COPY /app /app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]