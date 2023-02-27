FROM python:3.8.10

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /ModernConnect2
WORKDIR /ModernConnect2

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
