"""
Script para ver los datos de la base de datos
Ejecutar: docker exec fastapi python view_db.py
"""

from app.database.base import SessionLocal
from app.models.user import User
from app.models.video import Video
from app.models.job import Job
from app.database.base import engine  # el engine que usás en SessionLocal
from sqlalchemy import inspect
import sys
sys.path.insert(0, '/app')

inspector = inspect(engine)

print("\n" + "="*60)
print("🗂️ Tablas en la base de datos")
print("="*60 + "\n")

tables = inspector.get_table_names()
for t in tables:
    print(f"📌 {t}")
    
db = SessionLocal()

print("\n" + "="*60)
print("👥 USUARIOS EN LA BASE DE DATOS")
print("="*60 + "\n")

users = db.query(User).all()

if not users:
    print("❌ No hay usuarios registrados\n")
else:
    for user in users:
        print(f"📧 Email:      {user.email}")
        #print(f"👤 Nombre:     {user.full_name}")
        print(f"🆔 ID:         {user.id}")
        #print(f"✅ Activo:     {user.is_active}")
        #print(f"🔐 Verificado: {user.is_verified}")
        print(f"📅 Creado:     {user.created_at}")
        #print(f"🔑 Último login: {user.last_login_at}")
        print("-" * 60)

print(f"\n📊 Total: {len(users)} usuario(s)\n")

videos = db.query(Video).all()
if not videos:
    print("❌ No hay videos registrados\n")
else:
    for video in videos:
        print(f"🎥 Video ID:   {video.id}")
        print(f"📁 File:     {video.original_filename}")
        print(f"📁 Seconds:     {video.duration_seconds}")
        print(f"📅 Creado:     {video.created_at}")
        print("-" * 60)

jobs = db.query(Job).all()
if not jobs:
    print("❌ No hay jobs registrados\n")
else:
    for job in jobs:
        print(f"🎬 Job ID:     {job.id}")
        print(f"🎥 Video ID:   {job.video_id}")
        print(f"🗃️ Job Type:   {job.job_type}")
        print(f"ℹ️ Status:     {job.status}")
        print(f"📁 Output:     {job.output_path}")
        print(f"📅 Creado:     {job.created_at}")
        print("-" * 60)

db.close()
