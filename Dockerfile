# Use official Python image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /bot

# Copy dependency file and install required Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot files to the container
COPY . .

# Expose the port for FastAPI health check
EXPOSE 8080

# Start the bot
CMD ["python", "bot.py"]
