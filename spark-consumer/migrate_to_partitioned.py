"""
Script de migration CryptoViz V3.0
Migration des données existantes vers structure partitionnée Y/M/D
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from datetime import datetime

class CryptoDataMigration:
    def __init__(self):
        self.spark = self.create_spark_session()
        
    def create_spark_session(self):
        """Créer session Spark pour migration"""
        return SparkSession.builder \
            .appName("CryptoViz-Migration-Partitioned") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.hadoop.fs.s3a.endpoint", os.getenv("MINIO_ENDPOINT", "http://minio:9000")) \
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ACCESS_KEY", "cryptoviz")) \
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")) \
            .config("spark.hadoop.fs.s3a.path.style.access", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.jars.packages", 
                   "org.apache.hadoop:hadoop-aws:3.3.4,"
                   "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
            .getOrCreate()

    def migrate_existing_data(self):
        """Migrer les données existantes vers structure partitionnée"""
        print("🔄 Migration des données vers structure partitionnée Y/M/D")
        
        try:
            # Lire toutes les données existantes
            print("📖 Lecture des données existantes...")
            old_df = self.spark.read.parquet("s3a://crypto-data/")
            
            total_records = old_df.count()
            print(f"📊 Total enregistrements à migrer: {total_records}")
            
            if total_records == 0:
                print("⚠️ Aucune donnée à migrer")
                return
            
            # Vérifier les colonnes disponibles
            columns = old_df.columns
            print(f"📋 Colonnes disponibles: {columns}")
            
            # Nettoyer et enrichir les données
            if 'timestamp_dt' in columns:
                # Les colonnes de partitioning existent déjà
                clean_df = old_df
            else:
                # Créer les colonnes de partitioning
                clean_df = old_df.withColumn("timestamp_dt", to_timestamp(col("timestamp")))
            
            # S'assurer que les colonnes year/month/day existent
            if 'year' not in columns:
                clean_df = clean_df \
                    .withColumn("year", year(col("timestamp_dt"))) \
                    .withColumn("month", month(col("timestamp_dt"))) \
                    .withColumn("day", dayofmonth(col("timestamp_dt")))
            
            # Filtrer les données valides
            valid_df = clean_df.filter(col("timestamp_dt").isNotNull())
            valid_count = valid_df.count()
            print(f"✅ Enregistrements valides: {valid_count}")
            
            # Afficher les partitions qui seront créées
            partitions_preview = valid_df.select("year", "month", "day").distinct().orderBy("year", "month", "day").collect()
            print("📁 Partitions qui seront créées:")
            for partition in partitions_preview:
                year, month, day = partition['year'], partition['month'], partition['day']
                print(f"   year={year}/month={month:02d}/day={day:02d}")
            
            # Écriture partitionnée
            print("💾 Écriture des données partitionnées...")
            
            valid_df.write \
                .mode("overwrite") \
                .option("compression", "snappy") \
                .partitionBy("year", "month", "day") \
                .option("maxRecordsPerFile", 10000) \
                .parquet("s3a://crypto-data-partitioned/crypto_prices/")
            
            print("✅ Migration terminée avec succès !")
            
            # Statistiques de migration
            self.migration_stats()
            
        except Exception as e:
            print(f"❌ Erreur pendant la migration: {e}")
            import traceback
            traceback.print_exc()

    def migration_stats(self):
        """Afficher les statistiques de migration"""
        print("\n📊 STATISTIQUES DE MIGRATION")
        print("="*50)
        
        try:
            # Lire les nouvelles données partitionnées
            partitioned_df = self.spark.read.parquet("s3a://crypto-data-partitioned/crypto_prices/")
            
            total = partitioned_df.count()
            print(f"📈 Total enregistrements migrés: {total}")
            
            # Stats par partition
            partition_stats = partitioned_df.groupBy("year", "month", "day").count().orderBy("year", "month", "day").collect()
            
            print("\n📁 Enregistrements par partition:")
            for stat in partition_stats:
                year, month, day = stat['year'], stat['month'], stat['day']
                count = stat['count']
                print(f"   year={year}/month={month:02d}/day={day:02d}: {count} records")
            
            # Stats par crypto
            print(f"\n💰 Cryptos disponibles:")
            crypto_stats = partitioned_df.groupBy("symbol").count().orderBy(desc("count")).limit(10).collect()
            for stat in crypto_stats:
                print(f"   {stat['symbol']}: {stat['count']} records")
            
        except Exception as e:
            print(f"⚠️ Erreur stats: {e}")

    def create_migration_buckets(self):
        """Créer les buckets nécessaires pour la migration"""
        import boto3
        
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "cryptoviz"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
            )
            
            buckets = ['crypto-data-partitioned', 'crypto-data-archive']
            for bucket in buckets:
                try:
                    s3_client.create_bucket(Bucket=bucket)
                    print(f"✅ Bucket créé: {bucket}")
                except:
                    print(f"ℹ️ Bucket existe déjà: {bucket}")
                    
        except Exception as e:
            print(f"⚠️ Erreur création buckets: {e}")

    def run_migration(self):
        """Exécuter la migration complète"""
        print("🚀 DÉMARRAGE MIGRATION CRYPTOVIZ V3.0")
        print("="*50)
        
        try:
            # Créer les buckets
            self.create_migration_buckets()
            
            # Migrer les données
            self.migrate_existing_data()
            
            print("\n🎉 MIGRATION RÉUSSIE !")
            print("📋 Prochaines étapes:")
            print("   1. Redémarrer Spark streaming avec nouveau code")
            print("   2. Adapter le dashboard pour nouvelle structure")
            print("   3. (Optionnel) Archiver ancien bucket crypto-data")
            
        except Exception as e:
            print(f"💥 Erreur migration: {e}")
        finally:
            print("🔒 Fermeture session Spark")
            self.spark.stop()

def main():
    migrator = CryptoDataMigration()
    migrator.run_migration()

if __name__ == "__main__":
    main()
