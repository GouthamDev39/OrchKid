FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app

RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]


