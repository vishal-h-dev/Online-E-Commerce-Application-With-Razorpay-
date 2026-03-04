FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Install setuptools BEFORE anything that might need pkg_resources (razorpay does)
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD sh -c "python manage.py flush --noinput && python manage.py migrate && python manage.py seed && gunicorn EComStore.wsgi:application --bind 0.0.0.0:$PORT"
