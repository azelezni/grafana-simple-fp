FROM python:3.10-alpine

ENV PYTHONPATH=/app:$PYTHONPATH

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "./app.py"]
