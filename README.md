# 🗄️ Sistema de Backup Automatizado

Script Python que compacta pastas, envia os arquivos para **Google Drive** e **AWS S3**, e notifica por **e-mail** — com logging completo e tratamento de erros em cada etapa.

---

## 📁 Estrutura do Projeto

```
backup_system/
├── backup.py            # Ponto de entrada principal
├── compressor.py        # Compactação em .zip
├── gdrive_uploader.py   # Upload para Google Drive (OAuth 2.0)
├── s3_uploader.py       # Upload para AWS S3
├── notifier.py          # Envio de e-mail via SMTP
├── requirements.txt     # Dependências Python
├── .env.example         # Modelo do arquivo de configuração
├── .env                 # ⚠️ Suas credenciais reais (NÃO versionar)
├── credentials.json     # ⚠️ Credencial OAuth do Google (NÃO versionar)
├── token.json           # Token gerado automaticamente (NÃO versionar)
├── backups/             # .zip gerados (criado automaticamente)
└── logs/                # Arquivos de log (criado automaticamente)
```

---

## ⚙️ Pré-requisitos

- Python 3.9 ou superior
- Conta Google com acesso ao Google Cloud Console
- Conta AWS com permissões de S3
- Servidor SMTP acessível (Gmail, Outlook, SendGrid, etc.)

---

## 🚀 Instalação

```bash
# 1. Clone ou copie os arquivos do projeto
cd backup_system

# 2. Crie um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com seus valores reais
```

---

## 🔑 Configuração das Credenciais

### Google Drive

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto (ou selecione um existente).
3. Ative a **Google Drive API**: APIs e Serviços → Biblioteca → "Google Drive API" → Ativar.
4. Crie credenciais OAuth 2.0:
   - APIs e Serviços → Credenciais → Criar Credenciais → ID do cliente OAuth.
   - Tipo de aplicativo: **App para computador (Desktop app)**.
   - Baixe o JSON e renomeie para `credentials.json` na raiz do projeto.
5. Na primeira execução, o navegador abrirá automaticamente para você autorizar o acesso.  
   O token será salvo em `token.json` para execuções futuras (sem interação).
6. Copie o **ID da pasta** de destino no Drive (retirado da URL: `drive.google.com/drive/folders/**ID_AQUI**`) e coloque em `GDRIVE_FOLDER_ID` no `.env`.

### AWS S3

1. No [AWS IAM Console](https://console.aws.amazon.com/iam/), crie um usuário com a política:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:PutObject", "s3:GetObject"],
       "Resource": "arn:aws:s3:::NOME-DO-SEU-BUCKET/*"
     }]
   }
   ```
2. Gere as chaves de acesso e adicione ao `.env`:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
3. Crie o bucket S3 e defina `AWS_S3_BUCKET` no `.env`.

### E-mail (Gmail)

1. Ative a **Verificação em duas etapas** na sua conta Google.
2. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Crie um App Password ("Outro") e use-o em `EMAIL_SMTP_PASSWORD` no `.env`.
4. Configure:
   ```
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   ```

> **Outros provedores:** Outlook → `smtp.office365.com:587` | SendGrid → `smtp.sendgrid.net:587` (senha = API Key)

---

## ▶️ Execução Manual

```bash
# Ative o ambiente virtual, se necessário
source .venv/bin/activate

# Execute o backup
python backup.py
```

Os logs são exibidos no terminal **e** salvos em `logs/backup_YYYYMMDD.log`.

---

## ⏰ Agendamento

### Linux — Cron

```bash
crontab -e
```

Adicione uma linha para executar todo dia às 02:00:

```cron
0 2 * * * /caminho/para/backup_system/.venv/bin/python /caminho/para/backup_system/backup.py >> /caminho/para/backup_system/logs/cron.log 2>&1
```

### Windows — Agendador de Tarefas

1. Abra o **Agendador de Tarefas** (`taskschd.msc`).
2. Criar Tarefa Básica → dê um nome.
3. Gatilho: Diariamente, às 02:00.
4. Ação: Iniciar um programa.
   - Programa: `C:\caminho\backup_system\.venv\Scripts\python.exe`
   - Argumentos: `backup.py`
   - Iniciar em: `C:\caminho\backup_system\`
5. Conclua e teste com "Executar".

---

## 📋 Variáveis de Ambiente (`.env`)

| Variável | Descrição | Exemplo |
|---|---|---|
| `BACKUP_FOLDERS` | Pastas a compactar (vírgula) | `/home/user/docs,/etc` |
| `OUTPUT_DIR` | Onde salvar o .zip localmente | `backups` |
| `LOG_DIR` | Diretório de logs | `logs` |
| `GDRIVE_FOLDER_ID` | ID da pasta de destino no Drive | `1AbCdEfGh…` |
| `GDRIVE_CREDENTIALS_FILE` | Caminho do credentials.json | `credentials.json` |
| `GDRIVE_TOKEN_FILE` | Caminho do token OAuth | `token.json` |
| `AWS_ACCESS_KEY_ID` | Chave de acesso AWS | `AKIA…` |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta AWS | `wJal…` |
| `AWS_S3_BUCKET` | Nome do bucket S3 | `meu-bucket` |
| `AWS_REGION` | Região AWS | `us-east-1` |
| `EMAIL_SENDER` | Remetente do e-mail | `backup@dominio.com` |
| `EMAIL_RECIPIENT` | Destinatário do e-mail | `admin@dominio.com` |
| `EMAIL_SMTP_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | Porta SMTP | `587` |
| `EMAIL_SMTP_PASSWORD` | Senha ou App Password SMTP | `abcd efgh…` |

---

## 🔒 Segurança

- **Nunca** versione `.env`, `credentials.json` ou `token.json`. Adicione ao `.gitignore`:
  ```
  .env
  credentials.json
  token.json
  backups/
  logs/
  ```
- Use **App Passwords** do Gmail em vez da senha principal.
- Conceda ao usuário IAM apenas as permissões mínimas necessárias no S3.
- O link S3 no e-mail é uma URL **pré-assinada** (válida por 7 dias), sem tornar o objeto público.

---

## 🐛 Troubleshooting

| Erro | Causa provável | Solução |
|---|---|---|
| `FileNotFoundError: credentials.json` | Arquivo OAuth não encontrado | Baixe do Google Cloud Console |
| `BACKUP_FOLDERS não configurado` | `.env` não criado ou vazio | Copie `.env.example` → `.env` |
| `SMTPAuthenticationError` | Senha SMTP incorreta | Use App Password do Gmail |
| `NoCredentialsError` (AWS) | Chaves AWS ausentes no `.env` | Verifique `AWS_ACCESS_KEY_ID` |
| `FileNotFoundError: pasta/X` | Pasta configurada não existe | Corrija o caminho em `BACKUP_FOLDERS` |

---

## 📄 Licença

MIT — use e adapte livremente.
