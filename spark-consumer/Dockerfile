FROM bitnami/spark:3.4.1

USER root

# Install Python dependencies with compatible versions
RUN pip install --no-cache-dir \
    numpy==1.24.4 \
    pandas==2.0.3 \
    pyspark==3.4.1 \
    kafka-python==2.0.2 \
    boto3==1.34.0 \
    pyarrow==13.0.0

# Create app directory
WORKDIR /opt/spark/apps

# Copy application files
COPY crypto_spark_streaming.py /opt/spark/apps/
COPY requirements.txt /opt/spark/apps/

# Set permissions
RUN chmod +x /opt/spark/apps/crypto_spark_streaming.py

# Create entrypoint script with better error handling
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'echo "🚀 Starting Spark Streaming Consumer..."' >> /entrypoint.sh && \
    echo 'sleep 30' >> /entrypoint.sh && \
    echo 'python --version' >> /entrypoint.sh && \
    echo 'python -c "import pandas, numpy, pyspark; print(f\"pandas: {pandas.__version__}, numpy: {numpy.__version__}\")"' >> /entrypoint.sh && \
    echo 'exec python /opt/spark/apps/crypto_spark_streaming.py' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
