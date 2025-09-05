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
        """Créer ou récupérer la session Spark avec gestion intelligente"""
        try:
            from pyspark.sql import SparkSession
            
            # Tenter de récupérer une session existante
            try:
                existing_session = SparkSession.getActiveSession()
                if existing_session is not None:
                    print("✅ Utilisation session Spark existante")
                    return existing_session
            except Exception as e:
                print(f"📡 Pas de session active existante: {e}")
            
            # Créer une nouvelle session si nécessaire
            print("🚀 Création nouvelle session Spark...")
            spark = SparkSession.builder \
                .appName("CryptoViz-V3-Streaming") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
                .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://minio:9000")) \
                .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "minioadmin")) \
                .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "minioadmin")) \
                .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .getOrCreate()
            
            return spark
            
        except Exception as e:
            print(f"❌ Erreur création session Spark: {e}")
            raise

    def setup_minio_buckets(self):
        """Setup MinIO buckets avec nouvelle structure"""
        import boto3
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin")
            )
            
            buckets = ["crypto-raw-partitioned", "crypto-raw"]
            for bucket in buckets:
                try:
                    s3_client.create_bucket(Bucket=bucket)
                    print(f"✅ Bucket créé: {bucket}")
                except Exception as e:
                    if "BucketAlreadyOwnedByYou" in str(e):
                        print(f"📦 Bucket existant: {bucket}")
                    else:
                        print(f"⚠️ Erreur bucket {bucket}: {e}")
                        
        except Exception as e:
            print(f"❌ Erreur setup MinIO: {e}")

    def process_crypto_stream(self):
        """Process crypto stream avec partitioning par année/mois/jour"""
        
        # Schema Kafka
        crypto_schema = StructType([
            StructField("timestamp", StringType(), True),
            StructField("symbol", StringType(), True),
            StructField("price_usd", DoubleType(), True),
            StructField("market_cap", DoubleType(), True),
            StructField("volume_24h", DoubleType(), True),
            StructField("percent_change_24h", DoubleType(), True),
            StructField("source", StringType(), True)
        ])
        
        print("📡 Configuration Kafka streaming...")
        
        # Lecture du stream Kafka
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", os.getenv("KAFKA_SERVERS", "redpanda:9092")) \
            .option("subscribe", "crypto_data") \
            .option("startingOffsets", "latest") \
            .load()
        
        # Parse JSON depuis Kafka
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), crypto_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")
        
        # Ajout des colonnes de partitioning
        enriched_df = parsed_df \
            .withColumn("parsed_timestamp", to_timestamp(col("timestamp"))) \
            .withColumn("year", year(col("parsed_timestamp"))) \
            .withColumn("month", month(col("parsed_timestamp"))) \
            .withColumn("day", dayofmonth(col("parsed_timestamp")))
        
        print("🚀 Démarrage streaming avec partitioning Y/M/D...")
        
        # Écriture avec partitioning
        stream = enriched_df.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", "s3a://crypto-raw-partitioned/") \
            .partitionBy("year", "month", "day") \
            .option("checkpointLocation", "/tmp/checkpoint-partitioned") \
            .trigger(processingTime='120 seconds') \
            .foreachBatch(self.process_partitioned_batch) \
            .start()
        
        return stream

    def process_partitioned_batch(self, batch_df, batch_id):
        """Process chaque batch avec logging et partitioning"""
        try:
            if batch_df.count() > 0:
                print(f"📊 Batch {batch_id}: {batch_df.count()} records")
                
                # Afficher les partitions détectées
                partitions = batch_df.select("year", "month", "day").distinct().collect()
                for p in partitions:
                    print(f"   📁 Partition: {p.year}/{p.month:02d}/{p.day:02d}")
                
                # Écriture avec partitioning
                batch_df.write \
                    .mode("append") \
                    .format("parquet") \
                    .partitionBy("year", "month", "day") \
                    .save("s3a://crypto-raw-partitioned/")
                
                print(f"✅ Batch {batch_id} écrit avec succès")
            else:
                print(f"📭 Batch {batch_id}: aucun record")
                
        except Exception as e:
            print(f"❌ Erreur batch {batch_id}: {e}")

    def compact_daily_partitions(self):
        """Compactage optionnel des partitions journalières"""
        try:
            print("🔧 Démarrage compactage partitions...")
            
            # Lire les données existantes
            df = self.spark.read.parquet("s3a://crypto-raw-partitioned/")
            
            # Réécriture pour optimisation
            df.write \
                .mode("overwrite") \
                .format("parquet") \
                .partitionBy("year", "month", "day") \
                .option("maxRecordsPerFile", 100000) \
                .save("s3a://crypto-raw-partitioned-compacted/")
                
            print("✅ Compactage terminé")
            
        except Exception as e:
            print(f"❌ Erreur compactage: {e}")

    def run(self):
        """Lancer le streaming"""
        print("🚀 CryptoViz V3 - Spark Streaming avec partitioning Y/M/D")
        
        try:
            # Démarrage du stream
            stream = self.process_crypto_stream()
            
            print("⏳ Streaming actif... (Ctrl+C pour arrêter)")
            stream.awaitTermination()
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par utilisateur")
        except Exception as e:
            print(f"❌ Erreur streaming: {e}")
        finally:
            print("🔚 Fermeture Spark session")
            self.spark.stop()

def main():
    print("🚀 Starting Spark Streaming Consumer...")
    pipeline = CryptoSparkStreaming()
    pipeline.run()

if __name__ == "__main__":
    main()
