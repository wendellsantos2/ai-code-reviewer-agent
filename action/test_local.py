#!/usr/bin/env python3
"""
Script utilitário para testar localmente o Agente de Code Review sem precisar do GitHub Actions.
"""

import os
import sys
from google import genai
from google.genai import types

from prompts import SYSTEM_INSTRUCTION, build_review_prompt

MOCK_DIFF = """
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,14 @@ def login_user(username, password, db):
-    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
-    user = db.execute(query).fetchone()
+    # Nova implementação com hash inseguro e sem validação de tipos
+    import hashlib
+    pwd_hash = hashlib.md5(password.encode()).hexdigest()
+    query = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password_hash = '{pwd_hash}'"
+    user = db.execute(query).fetchone()
+    if user:
+        print(f"DEBUG: User logged in: {user['username']} with hash {pwd_hash}")
     return user
"""

def load_env_file():
    """Carrega variáveis do arquivo .env na raiz do projeto caso exista."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    os.environ[key] = val

def main():
    load_env_file()

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    # Valida se ainda está com o texto de exemplo ou vazia
    if not api_key or "COLE_SUA_NOVA_CHAVE_AQUI" in api_key:
        api_key = os.environ.get("GOOGLE_API_KEY", "").strip()

    if not api_key or "COLE_SUA_NOVA_CHAVE_AQUI" in api_key:
        print("❌ Erro: Chave não encontrada ou não configurada.")
        print("   Abra o arquivo .env e cole sua nova chave na linha:")
        print("   GEMINI_API_KEY=sua-chave-aqui")
        sys.exit(1)

    # Atualiza as variáveis de ambiente com a chave válida
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    print(f"🧪 Rodando simulação de Code Review local com o modelo {model_name}...")

    client = genai.Client(api_key=api_key)
    prompt = build_review_prompt(
        pr_title="feat(auth): melhora autenticação de usuários com hash MD5",
        pr_description="Atualizado login de usuários adicionando MD5 para segurança.",
        diff_text=MOCK_DIFF,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )

    print("\n" + "=" * 50)
    print("📋 RESPOSTA GERADA PELO AGENTE:")
    print("=" * 50 + "\n")
    print(response.text)
    print("\n" + "=" * 50)
    print("✅ Teste local concluído com sucesso!")

if __name__ == "__main__":
    main()
