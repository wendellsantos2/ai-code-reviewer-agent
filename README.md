# 🤖 GitHub AI Code Reviewer Agent

Um agente inteligente e autônomo para **GitHub Actions**, desenvolvido em Python e alimentado pela API do **Google Gemini**, capaz de analisar automaticamente Pull Requests, identificar vulnerabilidades de segurança, bugs potenciais, gargalos de performance e postar revisões detalhadas com sugestões de código.

---

## 🚀 Como Funciona

```
                    ┌─────────────────────────┐
                    │ Autor abre ou atualiza  │
                    │    um Pull Request      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     GitHub Actions      │
                    │   (pr-reviewer.yml)     │
                    └────────────┬────────────┘
                                 │
            ┌────────────────────┴────────────────────┐
            ▼                                         ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│     PyGithub            │               │      Google Gemini      │
│  - Baixa o diff do PR   │ ────────────> │  - Analisa segurança    │
│  - Filtra lockfiles/imgs│               │  - Identifica bugs/edge │
└─────────────────────────┘               │  - Sugere correções     │
                                          └───────────┬─────────────┘
                                                      │
                                                      ▼
                                          ┌─────────────────────────┐
                                          │ Posta o Review no PR    │
                                          │   com Markdown Rico     │
                                          └─────────────────────────┘
```

---

## 📁 Estrutura do Projeto

```
projeto_agente/
├── .github/
│   └── workflows/
│       └── pr-reviewer.yml    # Workflow disparado nos eventos de Pull Request
├── action/
│   ├── review_pr.py          # Script principal executado no GitHub Actions
│   ├── prompts.py            # Instruções e persona de revisão para a IA
│   ├── requirements.txt      # Dependências (google-genai, PyGithub, etc.)
│   └── test_local.py         # Script utilitário para testar localmente
├── .gitignore
└── README.md
```

---

## ⚙️ Passo a Passo para Configurar no seu Repositório

### 1. Obter uma Chave da API do Google Gemini
1. Acesse o [Google AI Studio](https://aistudio.google.com/).
2. Faça login com sua conta Google.
3. Clique em **"Get API key"** e copie a sua chave.

### 2. Adicionar a Secret no seu Repositório GitHub
1. No seu repositório no GitHub, clique na aba **Settings**.
2. No menu lateral esquerdo, vá em **Secrets and variables** > **Actions**.
3. Clique no botão **New repository secret**.
4. Defina:
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: Cole a sua chave obtida no Google AI Studio.
5. Clique em **Add secret**.

> **Nota:** O `GITHUB_TOKEN` é gerado automaticamente pelo GitHub Actions em cada execução, não sendo necessário criá-lo manualmente.

### 3. Garantir Permissões de Leitura e Escrita
1. Ainda em **Settings** > **Actions** > **General**.
2. Role até a seção **Workflow permissions**.
3. Certifique-se de que a opção **"Read and write permissions"** está marcada (ou use o bloco `permissions` já configurado no arquivo `pr-reviewer.yml`).
4. Clique em **Save**.

### 4. Subir os arquivos para o repositório
Basta fazer o commit e push desta pasta para o seu repositório GitHub:
```bash
git init
git add .
git commit -m "feat: adicionar agente de code review com Gemini"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

A partir desse momento, qualquer Pull Request aberto ou atualizado receberá automaticamente a análise do agente!

---

## 🧪 Testando Localmente

Você pode validar a análise do modelo sem precisar abrir um PR no GitHub usando o script `action/test_local.py`:

1. Instale as dependências:
   ```bash
   pip install -r action/requirements.txt
   ```
2. Defina a variável de ambiente:
   - **Windows (PowerShell)**:
     ```powershell
     $env:GEMINI_API_KEY="sua-chave-aqui"
     ```
   - **Linux / Mac (Bash)**:
     ```bash
     export GEMINI_API_KEY="sua-chave-aqui"
     ```
3. Execute o script de teste:
   ```bash
   python action/test_local.py
   ```

---

## 🎨 Customização das Regras de Revisão

Para ajustar o comportamento do agente (por exemplo, torná-lo mais rígido com tipagem, exigir padrões de arquitetura específicos da sua empresa ou mudar o tom das respostas):
- Abra o arquivo [action/prompts.py](file:///d:/projeto_agente/action/prompts.py).
- Edite a variável `SYSTEM_INSTRUCTION` para incluir regras de negócio ou convenções do seu time.
