FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline_doctor.py .

CMD ["python3", "pipeline_doctor.py"]