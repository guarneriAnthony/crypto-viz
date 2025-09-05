"""
CryptoViz V3.0 - Spark Streaming Consumer
Version corrigée sans problèmes datetime pandas
"""

import os
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json

class CryptoSparkStreaming:
    def __init__(self):
        self.spark = self.create_spark_session()
        self.setup_minio_buckets()
        
    def create_spark_session(self):
        """Créer une session Spark optimisée"""
        return SparkSession.builder \
            .appName("CryptoViz-V3-Streaming") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://minio:9000")) \
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "cryptoviz")) \
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")) \
            .config("spark.hadoop.fs.s3a.path.style.access", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.jars.packages", 
                   "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                   "org.apache.hadoop:hadoop-aws:3.3.4,"
                   "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
            .getOrCreate()

    def setup_minio_buckets(self):
        """Setup MinIO buckets via API simple"""
        import boto3
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "cryptoviz"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
            )
            
            buckets = ['crypto-data', 'crypto-ml', 'crypto-catalog']
            for bucket in buckets:
                try:
                    s3_client.create_bucket(Bucket=bucket)
                    print(f"✅ Bucket créé: {bucket}")
                except:
                    pass  # Bucket existe déjà
                    
        except Exception as e:
            print(f"⚠️ Erreur setup buckets: {e}")

    def process_crypto_stream(self):
        """Traiter les messages crypto en streaming"""
        print("📡 Démarrage du streaming Redpanda → Parquet")
        
        # Schéma des données crypto
        crypto_schema = StructType([
            StructField("name", StringType(), True),
            StructField("symbol", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("market_cap", DoubleType(), True),
            StructField("volume_24h", DoubleType(), True),
            StructField("change_1h", DoubleType(), True),
            StructField("change_24h", DoubleType(), True),
            StructField("change_7d", DoubleType(), True),
            StructField("source", StringType(), True),
            StructField("timestamp", StringType(), True),  # String puis conversion
            StructField("ingestion_timestamp", StringType(), True)
        ])

        # Lecture stream Redpanda
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", os.getenv("REDPANDA_BROKERS", "redpanda:9092")) \
            .option("subscribe", "crypto-raw-data") \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()

        # Parse JSON et transformation
        parsed_df = df.select(
            from_json(col("value").cast("string"), crypto_schema).alias("data"),
            col("offset"),
            col("partition"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp", "offset", "partition")

        # Ajout colonnes partitionnement (conversion timestamp string → datetime)
        enriched_df = parsed_df \
            .withColumn("processing_time", current_timestamp()) \
            .withColumn("timestamp_dt", to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")) \
            .withColumn("date_partition", date_format(col("timestamp_dt"), "yyyy-MM-dd")) \
            .withColumn("hour_partition", date_format(col("timestamp_dt"), "HH")) \
            .withColumn("year", year(col("timestamp_dt"))) \
            .withColumn("month", month(col("timestamp_dt"))) \
            .withColumn("day", dayofmonth(col("timestamp_dt")))

        print("🌊 Streaming démarré - Écriture Parquet partitionné toutes les 30s")

        # Écriture en streaming vers S3/MinIO
        query = enriched_df.writeStream \
            .format("parquet") \
            .outputMode("append") \
            .option("checkpointLocation", "/tmp/spark-checkpoint") \
            .option("path", "s3a://crypto-data/") \
            .trigger(processingTime="30 seconds") \
            .foreachBatch(self.process_batch) \
            .start()

        return query

    def process_batch(self, batch_df, batch_id):
        """Process chaque batch et log les statistiques"""
        count = batch_df.count()
        print(f"📦 Processing batch {batch_id} - {count} records")
        
        if count > 0:
            # Log des cryptos traités
            crypto_counts = batch_df.groupBy("symbol", "source").count().collect()
            for row in crypto_counts:
                print(f"   💰 {row['symbol']} ({row['source']}): {row['count']} records")
            
            # Écriture directe en Parquet vers S3
            try:
                batch_df.write \
                    .mode("append") \
                    .option("compression", "snappy") \
                    .parquet("s3a://crypto-data/")
                    
                print(f"✅ Batch {batch_id} écrit en Parquet (compression Snappy)")
                
            except Exception as e:
                print(f"❌ Erreur écriture batch {batch_id}: {e}")

    def run(self):
        """Démarre le pipeline complet"""
        print("🚀 Démarrage CryptoViz V3 Spark Streaming Pipeline")
        
        # Attendre que les services soient prêts
        print("⏳ Attente services (Redpanda, MinIO)...")
        time.sleep(30)
        
        try:
            # Démarrer le streaming
            query = self.process_crypto_stream()
            
            print("🔄 Pipeline en cours d'exécution. Ctrl+C pour arrêter.")
            
            # Attendre indéfiniment (streaming continu)
            query.awaitTermination()
            
        except KeyboardInterrupt:
            print("🛑 Arrêt du streaming demandé")
            query.stop()
        except Exception as e:
            print(f"❌ Erreur pipeline: {e}")
        finally:
            print("🔒 Fermeture Spark Session")
            self.spark.stop()

def main():
    pipeline = CryptoSparkStreaming()
    pipeline.run()

if __name__ == "__main__":
    main()
