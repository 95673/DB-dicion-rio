# DB-Dicionário — USSD

Dicionário interactivo PT⇄EN com 1000 palavras e chat de dúvidas sobre os serviços Vodacom, pronto para correr via USSD.

## Menu do cliente

1. Inglês > Português
2. Português > Inglês
3. Palavra do dia
4. Dúvidas Vodacom — o cliente escreve a dúvida e recebe a resposta das FAQs

Nos ecrãs USSD os textos vão sem acentos, para aparecerem bem em qualquer telemóvel.

Se a palavra não for encontrada, o app tenta formas parecidas e, se for uma gralha, pergunta *"Quis dizer: house?"* (ver "Como a busca funciona").

## Ficheiros

**Dados**

- `dicionario.csv` — as 1000 palavras (id, word_en, pron, trad_pt), editável em Excel/Sheets
- `dicionario.db` — mesmo conteúdo em SQLite, usado pelo backend
- `faq_vodacom.json` — as perguntas e respostas do chat de dúvidas (ver mais abaixo)
- `codigos_vodacom.json` — os códigos USSD e os contactos da Vodacom, num só sítio (ver "Manutenção")
- `build_db.py` — recria o `.db` a partir do `.csv`/`raw_words.txt` se editares as palavras

**Código** (todos no mesmo nível, sem pastas)

- `app.py` — backend Flask compatível com o webhook USSD da Africa's Talking: só tem as rotas (`/`, `/ussd`, `/stats`) e o fluxo dos ecrãs
- `config.py` — caminhos, limites e segredos (lidos de variáveis de ambiente)
- `menus.py` — textos dos ecrãs
- `base_dados.py` — SQLite e logs das buscas
- `tradutor.py` — busca tolerante de palavras no dicionário e sugestões para gralhas
- `chat.py` — chat de dúvidas Vodacom
- `ia.py` — Grok (xAI) como reserva do tradutor (opcional)
- `texto.py` — ferramentas de texto (normalizar, truncar, tirar acentos)
- `codigos.py` — lê o `codigos_vodacom.json` e preenche os `{CODIGOS}` das FAQs
- `verificar.py` — verifica se as FAQs e os códigos estão certos (também na rota `/verificar`)
- `simulador.py` — testa o fluxo completo no terminal, sem precisar de servidor nem internet
- `requirements.txt` — bibliotecas necessárias

## Testar agora, sem instalar nada de USSD

```
pip install flask
python3 simulador.py
```

Isto simula a experiência completa do telemóvel no terminal, incluindo o chat de dúvidas, e mostra o número de caracteres de cada ecrã. O simulador não grava nada nos logs.

## Como a busca funciona

Nas opções 1 e 2, a busca segue esta ordem e pára à primeira que acertar:

1. **Forma exacta**, sem distinguir maiúsculas nem acentos.
2. **Formas parecidas:** ignora "to", "the" e "a" no início (inglês) e "o", "a", "os", "as", "um", "uma" (português), e tenta o singular e o infinitivo. Exemplos: `houses` → `house`, `going` → `go`, `wanted` → `want`, `the house` → `house`, `casas` → `casa`, `falando` → `falar`.
3. **Grok**, só se houver `GROK_API_KEY` configurada.
4. **Gralhas:** sugere a palavra mais parecida. Exemplo: `hosue` → *"Quis dizer: house?"*. Se o cliente responder 1, vê a tradução.
5. Se nada servir, mostra "nao encontrada".

**Limites:** as expressões com várias palavras só acertam na forma exacta, e os verbos irregulares (`went`, `gone`) têm de estar no `dicionario.csv`. A tabela é lida uma só vez ao arrancar, por isso depois de mudar o dicionário é preciso reiniciar o serviço (no Render, o deploy faz isso).

## Chat de dúvidas Vodacom

O chat não usa IA: só responde com o que está em `faq_vodacom.json`, por isso nunca inventa.

**Como funciona:** cada FAQ tem palavras-chave. Uma palavra-chave "acerta" se todas as suas palavras aparecem na pergunta do cliente. Cada acerto vale tantos pontos quantas palavras tem a chave (assim "ser agente" ganha a "agente"). Ganha a FAQ com mais pontos, e em caso de empate a que vem primeiro no ficheiro. Se nenhuma acertar, o cliente vê: *"Ligue 100 ou fale no WhatsApp Vodacom: 841110111"* (os números vêm de `codigos_vodacom.json`).

**Formato de cada FAQ:**

```json
{
  "id": 3,
  "modulo": "M-Pesa",
  "pergunta": "Como mudo o meu PIN do M-Pesa?",
  "palavras_chave": ["mudar pin", "alterar pin"],
  "resposta": "Para mudar o PIN, marque {MPESA} > 9 > 6 > 1, digite o novo PIN e confirme-o.",
  "verificado": "2026-10-31"
}
```

**Regras:**

- A `resposta` tem no máximo **160 caracteres**, já com os códigos preenchidos.
- Em vez de escrever um código, usa o nome dele entre chavetas, como `{MPESA}` ou `{MENU}`. O valor vem de `codigos_vodacom.json`.
- Para respostas mais longas, acrescenta `resposta_continuacao` (segundo ecrã) e termina a primeira parte com `(1/2)`. O cliente vê "1. Mais".
- Os acentos são tirados automaticamente no ecrã USSD.
- `verificado` é a data da última verificação da informação (`null` se ainda não foi verificada). `nota` é opcional.
- Depois de editar o ficheiro, volta a carregar o serviço (no Render, o deploy faz isso sozinho).

**Dica:** o painel `/stats` mostra as **dúvidas sem resposta**. São as que convém acrescentar às FAQs.

## Manutenção: onde mudar cada coisa

| Quero... | Edito... |
|---|---|
| Mudar um código USSD ou um contacto (linha de apoio, WhatsApp) | `codigos_vodacom.json` |
| Acrescentar ou corrigir uma resposta do chat | `faq_vodacom.json` |
| Acrescentar palavras ao dicionário | `dicionario.csv` e depois `python3 build_db.py` |
| Mudar os textos dos menus | `menus.py` |
| Mudar caminhos ou limites | `config.py` |
| Mudar senhas e chaves | variáveis de ambiente no Render |
| Ver se está tudo certo | `/verificar?chave=SENHA` (ou `python3 verificar.py`) |

**Códigos USSD.** Cada código escreve-se uma só vez, em `codigos_vodacom.json`. Nas FAQs usa-se o nome entre chavetas, por exemplo `{MPESA}` ou `{MENU}`. Assim, se a Vodacom mudar o `*150#`, alteras uma linha e todas as respostas ficam certas.

**Regra de ouro:** depois de editar qualquer ficheiro de dados, abre o `/verificar`. Mostra os erros (código que não existe, resposta com mais de 160 caracteres, ids repetidos) antes de os clientes os verem. Cada FAQ confirmada leva a data em `verificado`.

## Rodar como servidor real (para conectar à Africa's Talking)

```
pip install flask
python3 app.py
```

O servidor sobe em `http://localhost:5000/ussd`. No painel da Africa's Talking (sandbox), aponta a callback URL para esse endereço (usando ngrok se estiveres a testar localmente, ex: `ngrok http 5000`).

## Passo 1 — Publicar o servidor no Render (grátis para começar)

1. Cria uma conta em [render.com](https://render.com) (dá para entrar com o GitHub).
2. Carrega todos os ficheiros para um repositório no GitHub. Se nunca usaste o GitHub: no site, abre o repositório e usa **Add file → Upload files**, depois faz o commit.
3. No Render, clica **New → Web Service** e liga esse repositório.
4. Configura:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
5. Clica **Create Web Service**. O deploy leva cerca de 2 minutos.
6. No fim, recebes uma URL pública, tipo `https://db-dicionario.onrender.com`.
7. Testa no navegador: abrir essa URL deve mostrar `DB-Dicionario online.` O endereço que a operadora/Africa's Talking vai chamar é `https://db-dicionario.onrender.com/ussd`.

## Variáveis de ambiente

No painel do Render, abre o teu serviço, vai a **Environment** e clica **Add Environment Variable** para cada uma. Depois de guardar, o Render reinicia o serviço sozinho.

| Variável | Para quê | Obrigatória? |
|---|---|---|
| `HASH_SALT` | Texto longo e secreto que protege os números de telefone nos logs. Os números são guardados cifrados, nunca em claro. **Não a mudes depois**, senão a contagem de números únicos recomeça. | Recomendada |
| `STATS_PASSWORD` | Senha dos painéis `/stats` e `/verificar`. | Só se quiseres os painéis |
| `GROK_API_KEY` | Chave da API do Grok, para o tradutor perguntar ao Grok quando a palavra não está nas 1000 da base local. | Não |

⚠️ Estas chaves nunca devem ser coladas no código nem no GitHub público. É assim que vazam e alguém gasta o teu crédito. A variável de ambiente é o lugar certo.

**Grok (opcional):** sem a chave, o app funciona normalmente só com a base local. Para a obter, vai a [console.x.ai](https://console.x.ai) (secção API Keys). O Grok só é usado no tradutor. O chat de dúvidas Vodacom nunca o usa.

## Painel de estatísticas

Com a variável `STATS_PASSWORD` definida, abre:

```
https://SEU-APP.onrender.com/stats?chave=A_SUA_SENHA
```

Mostra o total de buscas, a taxa de sucesso, os números únicos, as palavras mais buscadas, as **palavras não encontradas**, as dúvidas Vodacom mais feitas, as **dúvidas sem resposta** e as buscas por dia.

**Como melhorar o dicionário:** abre a lista de palavras não encontradas (indica se é `en-pt` ou `pt-en`), acrescenta as que fazem sentido ao `dicionario.csv` e corre `python3 build_db.py` para recriar o `dicionario.db`. As gralhas também aparecem na lista, por isso escolhe só as palavras que realmente faltam.

## Verificar se está tudo certo

Com a `STATS_PASSWORD` definida, abre:

```
https://SEU-APP.onrender.com/verificar?chave=A_SUA_SENHA
```

Mostra quantas FAQs estão verificadas e quantas faltam, os **problemas** (corrigir antes de publicar), os avisos (por exemplo, a mesma palavra-chave em duas FAQs) e as FAQs com uma nota por confirmar. Os problemas também aparecem nos logs do Render quando o serviço arranca.

## Passo 2 — Configurar o sandbox da Africa's Talking

1. Cria conta em [africastalking.com](https://africastalking.com) (gratuita).
2. No painel, vai a **USSD → Sandbox** e cria um novo canal.
3. Em **Callback URL**, cola `https://SEU-APP.onrender.com/ussd`.
4. Descarrega a app "Africa's Talking USSD Simulator" (ou usa o simulador web).
5. Digita o código de teste do sandbox. O menu do DB-Dicionário deve aparecer exactamente como no `simulador.py`.

## Depois disso (produção real)

- Trocar o SQLite por PostgreSQL se o volume de acessos crescer.
- Pedir contrato + shortcode real (ex: `*555#`) junto à operadora ou através da Africa's Talking.
- Acrescentar cobrança por sessão/assinatura conforme o modelo comercial.
- Enviar por SMS o link do WhatsApp da Vodacom (`https://wa.me/258841110111`), para o cliente abrir a conversa com um toque.
- Rever as FAQs ainda sem data em `verificado`, antes de as mostrar aos clientes.
