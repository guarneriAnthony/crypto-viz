"""
CryptoViz V3.0 - Spark Streaming Consumer avec PARTITIONING Y/M/D
Version optimisée avec partitioning S3 et compaction
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
        

    def setup_minio_buckets(self):
        """Setup MinIO buckets avec nouvelle structure"""
        import boto3
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "cryptoviz"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
            )
            
            buckets = ['crypto-data-partitioned', 'crypto-data-archive', 'crypto-ml', 'crypto-catalog']
            for bucket in buckets:
                try:
                    s3_client.create_bucket(Bucket=bucket)
                    print(f"✅ Bucket créé: {bucket}")
                except:
                    pass  # Bucket existe déjà
                    
        except Exception as e:
            print(f"⚠️ Erreur setup buckets: {e}")

    def process_crypto_stream(self):
        """Traiter les messages crypto avec PARTITIONING Y/M/D"""
        print("📡 Démarrage streaming avec partitioning Y/M/D")
        
        # Schéma des données crypto
        crypto_schema = StructType([
            StructField("name", StringType(), True),
            StructField("symbol", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("percent_change_24h", DoubleType(), True),
            StructField("market_cap", DoubleType(), True),
            StructField("source", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("ingestion_timestamp", StringType(), True),
            StructField("producer_id", StringType(), True),
            StructField("schema_version", StringType(), True)
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

        # Parse JSON et transformation avec colonnes partitioning
        parsed_df = df.select(
            from_json(col("value").cast("string"), crypto_schema).alias("data"),
            col("offset"),
            col("partition"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp", "offset", "partition")

        # Enrichissement avec colonnes de partitioning optimisées
        enriched_df = parsed_df \
            .withColumn("processing_time", current_timestamp()) \
            .withColumn("timestamp_dt", to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'")) \
            .withColumn("year", year(col("timestamp_dt"))) \
            .withColumn("month", month(col("timestamp_dt"))) \
            .withColumn("day", dayofmonth(col("timestamp_dt"))) \
            .withColumn("hour", hour(col("timestamp_dt"))) \
            .withColumn("date_partition", date_format(col("timestamp_dt"), "yyyy-MM-dd"))

        print("🗂️ Structure partitioning: year/month/day")
        print("⏰ Déclenchement: toutes les 2 minutes (120s)")

        # Écriture streaming avec PARTITIONING
        query = enriched_df.writeStream \
            .format("parquet") \
            .outputMode("append") \
            .option("checkpointLocation", "/tmp/spark-checkpoint-partitioned") \
            .trigger(processingTime="120 seconds") \
            .foreachBatch(self.process_partitioned_batch) \
            .start()

        return query

    def process_partitioned_batch(self, batch_df, batch_id):
        """Process batch avec partitioning Y/M/D et compaction"""
        count = batch_df.count()
        print(f"📦 Processing batch {batch_id} - {count} records")
        
        if count > 0:
            # Stats des cryptos traités
            crypto_counts = batch_df.groupBy("symbol", "source").count().collect()
            for row in crypto_counts:
                print(f"   💰 {row['symbol']} ({row['source']}): {row['count']} records")
            
            try:
                # ÉCRITURE PARTITIONNÉE Y/M/D
                batch_df.write \
                    .mode("append") \
                    .option("compression", "snappy") \
                    .partitionBy("year", "month", "day") \
                    .option("maxRecordsPerFile", 10000) \
                    .parquet("s3a://crypto-data-partitioned/crypto_prices/")
                    
                print(f"✅ Batch {batch_id} écrit avec partitioning Y/M/D")
                
                # Logs de la structure créée
                current_partitions = batch_df.select("year", "month", "day").distinct().collect()
                for partition in current_partitions:
                    year, month, day = partition['year'], partition['month'], partition['day']
                    print(f"   📁 Partition créée: year={year}/month={month:02d}/day={day:02d}")
                
            except Exception as e:
                print(f"❌ Erreur écriture batch {batch_id}: {e}")

    def compact_daily_partitions(self):
        """Compaction des partitions quotidiennes (optionnel)"""
        print("🗜️ Compaction des partitions en cours...")
        
        # Lire les données de la journée actuelle et réécrire avec moins de fichiers
        from datetime import datetime
        today = datetime.now()
        
        try:
            daily_path = f"s3a://crypto-data-partitioned/crypto_prices/year={today.year}/month={today.month:02d}/day={today.day:02d}/"
            
            daily_df = self.spark.read.parquet(daily_path)
            
            # Réécrire avec moins de fichiers
            daily_df.coalesce(1) \
                .write \
                .mode("overwrite") \
                .option("compression", "snappy") \
                .parquet(daily_path)
                
            print(f"✅ Compaction terminée pour {today.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            print(f"⚠️ Compaction échouée: {e}")

    def run(self):
        """Démarre le pipeline complet avec partitioning"""
        print("🚀 CryptoViz V3 - Streaming avec Partitioning Y/M/D")
        
        # Attendre que les services soient prêts
        print("⏳ Attente services (Redpanda, MinIO)...")
        time.sleep(30)
        
        try:
            # Démarrer le streaming partitionné
            query = self.process_crypto_stream()
            
            print("🗂️ Pipeline partitionné en cours. Structure: year/month/day")
            print("📊 Nouveau bucket: crypto-data-partitioned")
            print("🔄 Ctrl+C pour arrêter.")
            
            # Attendre indéfiniment (streaming continu)
            query.awaitTermination()
            
        except KeyboardInterrupt:
            print("🛑 Arrêt du streaming demandé")
            if 'query' in locals():
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
    def create_spark_session(self):
        """Utiliser la session Spark existante ou en créer une nouvelle"""
        try:
            # Essayer d'utiliser la session existante
            from pyspark.sql import SparkSession
            spark = SparkSession.getActiveSession()
            if spark is not None:
                print("✅ Utilisation session Spark existante")
                return spark
            else:
                print("🔧 Création nouvelle session Spark")
                # Fallback vers création nouvelle session
                return SparkSession.builder \
                    .appName("CryptoViz-V3-Streaming-Partitioned") \
                    .config("spark.sql.adaptive.enabled", "true") \
                    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                    .config("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB") \
                    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
                    .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://minio:9000")) \
                    .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "cryptoviz")) \
                    .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")) \
                    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                    .getOrCreate()
        except Exception as e:
            print(f"⚠️ Erreur session Spark: {e}")
            return None
