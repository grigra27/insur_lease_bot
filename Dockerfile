FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Accept build arguments
ARG TELEGRAM_BOT_TOKEN
ARG ADMIN_TELEGRAM_BOT_TOKEN
ARG ADMIN_TELEGRAM_USER_ID

# Set environment variables
ENV TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ENV ADMIN_TELEGRAM_USER_ID=$ADMIN_TELEGRAM_USER_ID
ENV ADMIN_TELEGRAM_BOT_TOKEN=$ADMIN_TELEGRAM_BOT_TOKEN

# Copy the rest of the application
COPY . .

CMD ["python3", "bot.py"]
