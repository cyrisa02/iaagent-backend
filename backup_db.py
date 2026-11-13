import os
import subprocess
from datetime import datetime

# Configuration
DB_USER = "iaagent_user"
DB_NAME = "iaagent_db"
BACKUP_DIR = "./backups"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FILE = os.path.join(BACKUP_DIR, f"iaagent_backup_{TIMESTAMP}.sql")

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Commande pg_dump
    cmd = [
        "docker", "exec", "-i", "iaagent_postgres",
        "pg_dump", "-U", DB_USER, DB_NAME
    ]
    
    try:
        with open(BACKUP_FILE, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)
        print(f"[BACKUP] Sauvegarde réussie : {BACKUP_FILE}")
        
        # Optionnel : Supprimer les backups de plus de 7 jours pour ne pas saturer le disque
        # (À implémenter selon tes besoins)
        
    except subprocess.CalledProcessError as e:
        print(f"[BACKUP] Erreur lors de la sauvegarde : {e}")

if __name__ == "__main__":
    create_backup()