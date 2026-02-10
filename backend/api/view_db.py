"""
Script para ver los datos de la base de datos
Ejecutar: docker exec fastapi python view_db.py
"""
import sys
sys.path.insert(0, '/app')

from app.database.base import SessionLocal
from app.models.user import User

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
        print(f"👤 Nombre:     {user.full_name}")
        print(f"🆔 ID:         {user.id}")
        print(f"✅ Activo:     {user.is_active}")
        print(f"🔐 Verificado: {user.is_verified}")
        print(f"📅 Creado:     {user.created_at}")
        print(f"🔑 Último login: {user.last_login_at}")
        print("-" * 60)

print(f"\n📊 Total: {len(users)} usuario(s)\n")

db.close()
