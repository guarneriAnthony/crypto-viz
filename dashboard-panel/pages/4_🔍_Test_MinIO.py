"""
Page Test MinIO Optimisé - Test de chargement intelligent des 7000+ fichiers Parquet
"""

import sys
import os

# Redirection vers le test MinIO
sys.path.append('/app')

# Import et exécution du test
exec(open('/app/test_minio_simple.py').read())
