FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ libc-dev

# Hugging Face Spaces require applications to run as a non-root user
RUN useradd -m -u 1000 user
USER user

# Set up environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application files
COPY --chown=user . .

# Make start script executable
RUN chmod +x run.sh

# Expose Streamlit port
EXPOSE 8501

# Boot both API and UI using the shell script
CMD ["./run.sh"]
