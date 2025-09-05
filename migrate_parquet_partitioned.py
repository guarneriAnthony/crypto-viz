#!/usr/bin/env python3
"""
Script de migration des parquets vers structure partitionnée Y/M/D
Lit les anciens parquets de crypto-data et les réécrit avec partitioning
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from datetime import datetime

def create_spark_session():
    """Session Spark pour migration"""
    return SparkSession.builder \
        .appName("CryptoViz-Migration-Partitioned") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "cryptoviz") \
        .config("spark.hadoop.fs.s3a.secret.key", "cryptoviz2024") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.jars.packages", 
               "org.apache.hadoop:hadoop-aws:3.3.4,"
               "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .getOrCreate()

def migrate_to_partitioned():
    """Migrer les anciens parquets vers structure partitionnée"""
    print("🚀 Démarrage migration vers structure partitionnée Y/M/D")
    
    spark = create_spark_session()
    
    try:
        print("📖 Lecture des anciens parquets de crypto-data...")
        old_df = spark.read.parquet("s3a://crypto-data/")
        
        print(f"   📊 {old_df.count()} records à migrer")
        print("   📋 Schéma des données:")
        old_df.printSchema()
        
        # Ajouter les colonnes de partitioning si elles n'existent pas
        if "year" not in old_df.columns:
            print("🔧 Ajout des colonnes de partitioning Y/M/D...")
            
            # Utiliser timestamp ou ingestion_timestamp selon disponibilité
            timestamp_col = "timestamp" if "timestamp" in old_df.columns else "ingestion_timestamp"
            
            partitioned_df = old_df \
                .withColumn("timestamp_dt", to_timestamp(col(timestamp_col))) \
                .withColumn("year", year(col("timestamp_dt"))) \
                .withColumn("month", month(col("timestamp_dt"))) \
                .withColumn("day", dayofmonth(col("timestamp_dt")))
        else:
            print("✅ Colonnes de partitioning déjà présentes")
            partitioned_df = old_df
        
        print("💾 Écriture dans crypto-data-partitioned avec structure Y/M/D...")
        partitioned_df.write \
            .mode("append") \
            .partitionBy("year", "month", "day") \
            .option("compression", "snappy") \
            .parquet("s3a://crypto-data-partitioned/")
        
        print("✅ Migration terminée avec succès !")
        
        # Statistiques finales
        final_df = spark.read.parquet("s3a://crypto-data-partitioned/")
        print(f"📈 Données finales: {final_df.count()} records")
        
        partitions = final_df.select("year", "month", "day").distinct().collect()
        print("📁 Partitions créées:")
        for p in partitions:
            print(f"   📂 year={p.year}/month={p.month}/day={p.day}")
            
    except Exception as e:
        print(f"❌ Erreur migration: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    migrate_to_partitioned()
