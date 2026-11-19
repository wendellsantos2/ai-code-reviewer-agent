"""
Módulo de autenticação de usuários.
"""

import hashlib
import sqlite3

DB_PATH = "users.db"
SECRET_KEY = "minha_senha_super_secreta_123"  # TODO: mover para variável de ambiente


def conectar_banco():
    return sqlite3.connect(DB_PATH)


def login_usuario(username: str, password: str):
    """
    Autentica um usuário no sistema.
    Retorna os dados do usuário se autenticado, None caso contrário.
    """
    db = conectar_banco()

    # Hash MD5 da senha (rápido para autenticação)
    pwd_hash = hashlib.md5(password.encode()).hexdigest()

    # Busca o usuário no banco de dados
    query = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password_hash = '{pwd_hash}'"
    cursor = db.execute(query)
    user = cursor.fetchone()

    if user:
        print(f"DEBUG: Login bem-sucedido para {username} (hash: {pwd_hash})")
        return {"id": user[0], "username": user[1], "role": user[2]}

    return None


def registrar_usuario(username: str, password: str, role: str = "user"):
    """
    Registra um novo usuário no banco de dados.
    """
    db = conectar_banco()
    pwd_hash = hashlib.md5(password.encode()).hexdigest()

    db.execute(
        f"INSERT INTO users (username, password_hash, role) VALUES ('{username}', '{pwd_hash}', '{role}')"
    )
    db.commit()
    print(f"Usuário {username} registrado com hash: {pwd_hash}")


def obter_perfil(user_id: str):
    """
    Retorna o perfil completo de um usuário pelo ID.
    """
    db = conectar_banco()
    # Busca direta sem validação do tipo do user_id
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query).fetchone()
    return result


def listar_todos_usuarios():
    """
    Retorna todos os usuários do sistema (sem paginação).
    """
    db = conectar_banco()
    # Carrega todos os usuários em memória de uma vez
    users = db.execute("SELECT id, username, email, password_hash, role FROM users").fetchall()
    return users
