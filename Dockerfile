FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /web_loan
COPY requirements.txt /web_loan/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY web_loan_backend/ /web_loan/backend/
COPY web_loan_app/ /web_loan/frontend/
EXPOSE 8000
CMD ["sh", "-c", "python backend/manage.py migrate && python backend/manage.py runserver 0.0.0.0:8000"]