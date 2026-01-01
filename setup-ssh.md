# Настройка SSH для Timeweb Cloud

## Проблема
SSH аутентификация не работает: `ssh: unable to authenticate, attempted methods [none publickey]`

## Решение

### 1. На вашем локальном компьютере

```bash
# Создайте SSH ключ (если еще не создан)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Скопируйте публичный ключ
cat ~/.ssh/id_rsa.pub
```

### 2. На сервере Timeweb Cloud

```bash
# Подключитесь к серверу через веб-консоль или пароль
ssh root@YOUR_SERVER_IP

# Создайте директорию для SSH ключей
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавьте ваш публичный ключ
nano ~/.ssh/authorized_keys
# Вставьте содержимое id_rsa.pub

# Установите правильные права
chmod 600 ~/.ssh/authorized_keys
chown -R root:root ~/.ssh

# Проверьте настройки SSH
nano /etc/ssh/sshd_config
```

### 3. Настройки SSH сервера

Убедитесь, что в `/etc/ssh/sshd_config` есть:

```
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication yes  # временно для отладки
```

Перезапустите SSH:
```bash
systemctl restart sshd
```

### 4. Проверьте подключение

```bash
# С вашего локального компьютера
ssh -v root@YOUR_SERVER_IP
```

### 5. Добавьте приватный ключ в GitHub Secrets

```bash
# Скопируйте приватный ключ
cat ~/.ssh/id_rsa
```

В GitHub → Settings → Secrets → Actions добавьте:
- `TIMEWEB_SSH_KEY` = содержимое приватного ключа (включая `-----BEGIN` и `-----END`)

## Альтернативное решение

Если проблемы продолжаются, создайте отдельного пользователя:

```bash
# На сервере
useradd -m -s /bin/bash deploy
usermod -aG docker deploy
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh

# Добавьте ключ для пользователя deploy
nano /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# В GitHub Secrets измените:
# TIMEWEB_USERNAME=deploy
```