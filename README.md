# DB-Dicionário — USSD

Dicionário interativo PT⇄EN com 1000 palavras, pronto para rodar via USSD.

## Arquivos

- `dicionario.csv` — as 1000 palavras (id, word_en, pron, trad_pt), editável em Excel/Sheets
- `dicionario.db` — mesmo conteúdo em SQLite, usado pelo backend
- `build_db.py` — recria o `.db` a partir do `.csv`/`raw_words.txt` se você editar as palavras
- `app.py` — backend Flask compatível com o webhook USSD da Africa's Talking
- `simulador.py` — testa o fluxo direto no terminal, sem precisar de servidor nem internet

## Testar agora, sem instalar nada de USSD

```bash
pip install flask
python3 simulador.py
```

Isso já simula a experiência completa do celular no terminal.

## Rodar como servidor real (para conectar à Africa's Talking)

```bash
pip install flask
python3 app.py
```

O servidor sobe em `http://localhost:5000/ussd`. No painel da Africa's Talking
(sandbox), aponte a callback URL para esse endereço (usando ngrok se estiver
testando localmente, ex: `ngrok http 5000`).

## Passo 1 — Publicar o servidor no Render (grátis para começar)

1. Crie uma conta em **render.com** (dá para logar com GitHub)
2. Suba esta pasta inteira para um repositório novo no GitHub
   - se nunca usou GitHub: crie o repo pelo site, arraste os arquivos na aba
     "Add file → Upload files", e faça o commit
3. No Render, clique **New → Web Service** e conecte esse repositório
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Clique em **Create Web Service** — o deploy leva ~2 minutos
6. Ao terminar, você recebe uma URL pública, tipo:
   `https://db-dicionario.onrender.com`
7. Teste no navegador: abrir essa URL deve mostrar `DB-Dicionario online.`
   O endpoint que a operadora/Africa's Talking vai chamar é:
   `https://db-dicionario.onrender.com/ussd`

**Variáveis de ambiente (API do Grok)**

O `app.py` já vem preparado para usar a API do Grok (xAI) como *fallback*:
quando uma palavra não está nas 1000 da base local, ele pergunta ao Grok
antes de dizer "não encontrada". Isso é opcional — sem a chave, o app
funciona normalmente só com a base local.

Para ativar:
1. Pegue sua chave em **console.x.ai** (seção API Keys)
2. No painel do Render, vá em **Environment** (menu lateral do seu serviço)
3. Clique **Add Environment Variable**
4. Key: `GROK_API_KEY` — Value: cole sua chave — **Save Changes**
5. O Render reinicia o serviço sozinho com a chave já disponível

⚠️ Nunca cole a chave direto no código nem no GitHub público — é assim que
ela vaza e alguém gasta seu crédito. A variável de ambiente é o lugar certo.

## Passo 2 — Configurar o sandbox da Africa's Talking

1. Crie conta em **africastalking.com** (gratuita)
2. No painel, vá em **USSD → Sandbox** e crie um novo canal
3. Em **Callback URL**, cole: `https://SEU-APP.onrender.com/ussd`
4. Baixe o app "Africa's Talking USSD Simulator" (ou use o simulador web)
5. Digite o código de teste do sandbox — o menu do DB-Dicionário deve
   aparecer exatamente como no `simulador.py`

## Depois disso (produção real)

1. Trocar SQLite por PostgreSQL se o volume de acessos crescer
2. Solicitar contrato + shortcode real (ex: `*555#`) junto à operadora
   ou via Africa's Talking
3. Adicionar cobrança por sessão/assinatura conforme o modelo comercial
