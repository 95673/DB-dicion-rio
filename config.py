"""
Configuração técnica do DB-Dicionario.

O que muda com mais frequência está em ficheiros de dados:
  codigos_vodacom.json -> códigos USSD e contactos da Vodacom
  faq_vodacom.json     -> perguntas e respostas do chat
Aqui ficam só os caminhos, os limites e os segredos.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Ficheiros de dados (no mesmo nível dos .py) ---
DB_PATH = os.path.join(BASE_DIR, "dicionario.db")
FAQ_PATH = os.path.join(BASE_DIR, "faq_vodacom.json")
CODIGOS_PATH = os.path.join(BASE_DIR, "codigos_vodacom.json")

# --- Limites ---
MAX_LEN = 160  # caracteres de cada ecrã USSD

# --- Grok (opcional, só para o tradutor) ---
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-4"

# --- Segredos e opções: variáveis de ambiente (no Render), nunca escritos aqui ---
GROK_API_KEY = os.environ.get("GROK_API_KEY")
STATS_PASSWORD = os.environ.get("STATS_PASSWORD", "")  # senha dos painéis /stats e /verificar
HASH_SALT = os.environ.get("HASH_SALT", "")  # protege os números de telefone nos logs
MODO_SIMULADOR = os.environ.get("MODO_SIMULADOR") == "1"  # o simulador.py não grava logs

if not HASH_SALT and not MODO_SIMULADOR:
    print("AVISO: defina a variavel de ambiente HASH_SALT para proteger os numeros de telefone nos logs.")
