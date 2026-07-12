## 1. Настройка сервера (Ubuntu)

```bash
ssh root@<IP-твоего-сервера>
```

### 1.1 Docker

```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version   # проверка
```

### 1.2 Папка проекта

```bash
mkdir -p /opt/time-capsule
```

Если запускаем не под root:
```bash
sudo mkdir -p /opt/time-capsule
sudo chown $USER:$USER /opt/time-capsule
```

### 1.3 SSH-ключ для GitHub Actions

Генерируем ключ:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github-deploy -C "github-deploy"
```

Копируем публичный ключ на сервер:

На пк:

```bash
cat ~/.ssh/github-deploy.pub
# → скопировать вывод
```

На **сервере**:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "< публичный ключ>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### 1.4 Открыть порты (если есть UFW)

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (для Caddy)
ufw allow 443/tcp   # HTTPS (для Caddy)
```

---

## 2. Настройка GitHub Secrets

На странице репозитория → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Описание | Пример значения |
|--------|----------|----------------|
| `SERVER_HOST` | IP прод сервера | `91.234.56.78` |
| `SERVER_USER` | Пользователь для SSH | `root` |
| `SSH_PRIVATE_KEY` | Приватный ключ (весь файл) |  |
| `SERVER_ENV` | Содержимое .env файла для продакшена | (см. ниже) |
| `CADDYFILE` | Содержимое Caddyfile с доменом | (см. ниже) |

### 2.1 Содержимое `SERVER_ENV`

```
DB_NAME=api
DB_USER=api
DB_PASSWORD=сгенерируй_openssl_rand_-base64_24
DB_HOST=db
DB_PORT=5432
SECRET_KEY=сгенерируй_openssl_rand_-base64_32
ROOT_PATH=
```

> **Важно:**
> - `DB_HOST=db` — это имя сервиса в Docker Compose, не IP
> - `SECRET_KEY` должен быть минимум 32 символа
> - Пароль и ключ генерируем командами:
>   ```bash
>   openssl rand -base64 24   # для DB_PASSWORD
>   openssl rand -base64 32   # для SECRET_KEY
>   ```

### 2.2 Содержимое `CADDYFILE`

```
api.твой-домен.ru {
    reverse_proxy web:8000
}
```

> **Важно:** Caddyfile с точным синтаксисом. Если домен не указан — Caddy не запустится.

---

## 3. Домен

| Тип | Имя | Значение |
|-----|-----|---------|
| A | `api` (поддомен) | IP сервера |

Caddy сам получит SSL-сертификат от Let's Encrypt при первом запросе. Ничего дополнительно настраивать не нужно.

---

## 4. Первый деплой

```bash
git add .
git commit -m "feat: production deployment setup"
git push origin master
```

`https://api.домен.ru/docs`

Логи на сервере:

```bash
ssh root@<IP>
cd /opt/time-capsule
docker compose -f docker-compose.prod.yml logs
```

---

## 5. Обновление

Пуш в `master`:

```bash
git add .
git commit -m "fix: что-то починил"
git push origin master
```

---

## 6. Полезные команды на сервере

```bash
# Cтатус контейнеров
docker compose -f /opt/time-capsule/docker-compose.prod.yml ps

# Логи всех сервисов
docker compose -f /opt/time-capsule/docker-compose.prod.yml logs

# Логи только API
docker compose -f /opt/time-capsule/docker-compose.prod.yml logs web

# Перезапустить всё
docker compose -f /opt/time-capsule/docker-compose.prod.yml restart

# Остановить всё
docker compose -f /opt/time-capsule/docker-compose.prod.yml down

# Подключиться к контейнеру
docker compose -f /opt/time-capsule/docker-compose.prod.yml exec web bash
```
