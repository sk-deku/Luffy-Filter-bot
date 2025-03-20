# Use official Python image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /bot

# Copy all bot files to the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for health checks (Koyeb requires this)
EXPOSE 8080

# Command to run the bot
CMD ["python", "bot.py"]
