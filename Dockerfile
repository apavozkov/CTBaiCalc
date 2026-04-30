FROM python:3.12-slim
WORKDIR /app
COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app /app/app
COPY categories.json /app/categories.json
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
