#!/usr/bin/env python3

import os
import time
from datetime import datetime
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json

class CryptoSparkStreaming:
    def __init__(self):
        self.spark = self.create_spark_session()
        self.setup_minio_buckets()
        
    def create_spark_session(self):
        """Créer session Spark avec JAR Kafka"""
        try:
            from pyspark.sql import SparkSession
            
            # Tenter session existante
            try:
                existing_session = SparkSession.getActiveSession()
                if existing_session is not None:
                    print("✅ Utilisation session Spark existante")
                    return existing_session
            except Exception as e:
                print(f" Création nouvelle session: {e}")
            
            print(" Création session Spark avec JAR Kafka...")
            spark = SparkSession.builder \
                .appName("CryptoViz-V3-Partitioned") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint-v2") \
                .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://192.168.1.76:9002")) \
                .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "cryptoviz")) \
                .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")) \
                .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                       "org.apache.hadoop:hadoop-aws:3.3.4,"
                       "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
                .getOrCreate()
            
            return spark
            
        except Exception as e:
            print(f"❌ Erreur session Spark: {e}")
            raise

    def setup_minio_buckets(self):
        """Créer les buckets nécessaires"""
        import boto3
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("MINIO_ENDPOINT", "http://192.168.1.76:9002"),
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "cryptoviz"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
            )
            
            buckets = ["crypto-data-partitioned"]
            for bucket in buckets:
                try:
                    s3_client.create_bucket(Bucket=bucket)
                    print(f"✅ Bucket créé: {bucket}")
                except Exception as e:
                    if "BucketAlreadyOwnedByYou" in str(e):
                        print(f" Bucket existant: {bucket}")
                    else:
                        print(f"⚠️ Erreur bucket {bucket}: {e}")
                        
        except Exception as e:
            print(f"❌ Erreur setup MinIO: {e}")

    def process_crypto_stream(self):
        """Stream Kafka → Parquet partitionné Y/M/D"""
        
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
            StructField("timestamp", StringType(), True),
            StructField("ingestion_timestamp", StringType(), True)
        ])
        
        print(" Configuration stream Kafka → Parquet Y/M/D")
        
        # Lecture Kafka
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", os.getenv("REDPANDA_BROKERS", "redpanda:9092")) \
            .option("subscribe", "crypto-raw-data") \
            .option("startingOffsets", "latest") \
            .load()
        
        # Parse JSON + ajout colonnes partitioning
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), crypto_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")
        
        # Ajout partitioning Y/M/D
        enriched_df = parsed_df \
            .withColumn("timestamp_dt", coalesce(to_timestamp(col("ingestion_timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"), current_timestamp())) \
            .withColumn("year", year(col("timestamp_dt"))) \
            .withColumn("month", month(col("timestamp_dt"))) \
            .withColumn("day", dayofmonth(col("timestamp_dt")))
        
        print(" Démarrage streaming avec partitioning Y/M/D vers crypto-data-partitioned")
        
        # ÉCRITURE UNIQUE avec partitioning
        stream = enriched_df.writeStream \
            .outputMode("append") \
            .trigger(processingTime='60 seconds') \
            .foreachBatch(self.write_partitioned_batch) \
            .option("checkpointLocation", "/tmp/checkpoint-partitioned-v2") \
            .start()
        
        return stream

    def write_partitioned_batch(self, batch_df, batch_id):
        """Écriture partitionnée Y/M/D dans crypto-data-partitioned"""
        try:
            if batch_df.count() > 0:
                print(f" Batch {batch_id}: {batch_df.count()} records")
                
                # Afficher partitions
                partitions = batch_df.select("year", "month", "day").distinct().collect()
                for p in partitions:
                    print(f"   📁 Partition: {p.year}/{p.month:02d}/{p.day:02d}")
                
                # ÉCRITURE UNIQUE avec partitioning Y/M/D
                batch_df.write \
                    .mode("append") \
                    .partitionBy("year", "month", "day") \
                    .option("compression", "snappy") \
                    .parquet("s3a://crypto-data-partitioned/")
                
                print(f"✅ Batch {batch_id} écrit avec partitioning Y/M/D")
            else:
                print(f"📭 Batch {batch_id}: aucun record")
                
        except Exception as e:
            print(f"❌ Erreur batch {batch_id}: {e}")

    def run(self):
        """Lancer le streaming"""
        print(" CryptoViz V3 - Streaming Partitionné Y/M/D")
        
        try:
            stream = self.process_crypto_stream()
            print(" Streaming actif...")
            stream.awaitTermination()
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé")
        except Exception as e:
            print(f"❌ Erreur streaming: {e}")
        finally:
            print(" Fermeture session")
            self.spark.stop()

def main():
    print(" Starting Partitioned Spark Streaming...")
    pipeline = CryptoSparkStreaming()
    pipeline.run()

if __name__ == "__main__":
    main()
