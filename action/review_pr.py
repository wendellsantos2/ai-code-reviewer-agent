#!/usr/bin/env python3
"""
Agente de Code Review para GitHub Actions alimentado pelo Google Gemini.
Lê o diff do Pull Request, gera uma análise aprofundada e comenta no PR.
"""

import os
import sys
import json
import fnmatch
from typing import List, Tuple
from github import Github, GithubException
from google import genai
from google.genai import types

from prompts import SYSTEM_INSTRUCTION, build_review_prompt

# Padrões de arquivos ignorados para economizar tokens e focar no código
IGNORED_PATTERNS = [
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Cargo.lock",
    "go.sum",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.svg",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.pdf",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
]

MAX_DIFF_CHARS = int(os.environ.get("MAX_DIFF_CHARS", "100000"))
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def should_ignore(file_path: str) -> bool:
    """Verifica se o arquivo deve ser ignorado na análise."""
    basename = os.path.basename(file_path)
    for pattern in IGNORED_PATTERNS:
        if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def get_pr_details() -> Tuple[int, str]:
    """Obtém o número do PR e o repositório a partir do evento do GitHub Actions."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        raise ValueError("GITHUB_EVENT_PATH não encontrado ou inválido.")

    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    if "pull_request" not in event_data:
        raise ValueError("Este evento não foi disparado por um Pull Request.")

    pr_number = event_data["pull_request"]["number"]
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_name:
        repo_name = event_data["repository"]["full_name"]

    return pr_number, repo_name


def collect_pr_diff(pr) -> Tuple[str, List[str]]:
    """Coleta os patches de cada arquivo do PR ignorando arquivos desnecessários."""
    diff_chunks = []
    analyzed_files = []
    total_chars = 0
    truncated = False

    files = pr.get_files()
    for file in files:
        if should_ignore(file.filename):
            print(f"⏩ Ignorando arquivo: {file.filename}")
            continue

        if not file.patch:
            print(f"ℹ️ Sem patch disponível para: {file.filename} (binário ou renomeado)")
            continue

        chunk = f"--- a/{file.filename}\n+++ b/{file.filename}\n{file.patch}\n\n"
        chunk_len = len(chunk)

        if total_chars + chunk_len > MAX_DIFF_CHARS:
            remaining = MAX_DIFF_CHARS - total_chars
            if remaining > 200:
                diff_chunks.append(chunk[:remaining] + "\n... [diff truncado por tamanho máximo] ...\n")
            truncated = True
            print(f"⚠️ Limite de caracteres atingido ({MAX_DIFF_CHARS}). Truncando diffs subsequentes.")
            break

        diff_chunks.append(chunk)
        analyzed_files.append(file.filename)
        total_chars += chunk_len

    full_diff = "".join(diff_chunks)
    if truncated:
        full_diff += "\n\n*(Nota: O diff foi parcialmente truncado pois excedeu o limite máximo de tokens.)*"

    return full_diff, analyzed_files


def run_gemini_review(pr_title: str, pr_description: str, diff_text: str, api_key: str, model_name: str) -> str:
    """Invoca o modelo Google Gemini para revisar o PR."""
    client = genai.Client(api_key=api_key)
    prompt = build_review_prompt(pr_title, pr_description, diff_text)

    print(f"🤖 Enviando solicitação para o Gemini ({model_name})...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )

    if not response.text:
        raise ValueError("O modelo Gemini retornou uma resposta vazia.")

    return response.text


def load_env_file():
    """Carrega variáveis do arquivo .env caso exista (útil para desenvolvimento local)."""
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
    print("🚀 Iniciando Agente de Code Review do GitHub...")

    github_token = os.environ.get("GITHUB_TOKEN")
    gemini_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if gemini_api_key:
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        os.environ["GOOGLE_API_KEY"] = gemini_api_key

    if not github_token:
        print("❌ Erro: GITHUB_TOKEN não configurado.", file=sys.stderr)
        sys.exit(1)

    if not gemini_api_key:
        print("❌ Erro: GEMINI_API_KEY não configurado.", file=sys.stderr)
        sys.exit(1)

    try:
        pr_number, repo_name = get_pr_details()
        print(f"📦 Repositório: {repo_name} | PR #{pr_number}")

        gh = Github(github_token)
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        print(f"📝 Título do PR: {pr.title}")
        print(f"👤 Autor: {pr.user.login}")

        diff_text, analyzed_files = collect_pr_diff(pr)

        if not diff_text.strip():
            print("ℹ️ Nenhum arquivo de código relevante para análise (apenas arquivos ignorados ou vazios).")
            return

        print(f"📊 Arquivos analisados ({len(analyzed_files)}): {', '.join(analyzed_files)}")

        model_name = DEFAULT_MODEL
        review_content = run_gemini_review(
            pr_title=pr.title,
            pr_description=pr.body or "",
            diff_text=diff_text,
            api_key=gemini_api_key,
            model_name=model_name,
        )

        footer = (
            "\n\n---\n"
            f"<sub>✨ Revisão gerada por **Gemini Code Review Agent** usando `{model_name}` | "
            f"Arquivos analisados: {len(analyzed_files)}</sub>"
        )

        full_comment = review_content.strip() + footer

        print("💬 Publicando comentário no Pull Request...")
        pr.create_issue_comment(full_comment)
        print("✅ Análise publicada com sucesso no Pull Request!")

    except GithubException as ghe:
        print(f"❌ Erro na API do GitHub: {ghe}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
