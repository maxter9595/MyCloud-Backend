# MyCloud API Documentation

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | User registration |
| POST | `/api/auth/login/` | User login |
| POST | `/api/auth/logout/` | User logout |
| GET | `/api/auth/users/me/` | Current user info |

## File Storage

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/storage/files/` | List user files |
| POST | `/api/storage/files/` | Upload file |
| GET | `/api/storage/files/{id}/` | File details |
| DELETE | `/api/storage/files/{id}/` | Delete file |
| GET | `/api/storage/files/{id}/download/` | Download file |
| PATCH | `/api/storage/files/{id}/share/` | Share file |

## Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/admin/create/` | Create admin user |
| GET | `/api/storage/files/?user_id={id}` | List files for any user (admin only) |


## Rate Limits (Ограничения запросов)

В API действуют следующие ограничения на частоту запросов:

### Общие ограничения
- **Анонимные пользователи**: 100 запросов в день
- **Авторизованные пользователи**: 1000 запросов в час

### Специальные ограничения
- **Регистрация новых пользователей**: 5 запросов в час с одного IP
- **Аутентификация**: 20 попыток входа в час с одного IP

### Лимиты хранилища
- **Максимальный размер файла**: 100MB
- **Максимальное хранилище**:
  - Обычные пользователи: 5GB
  - Администраторы: 10GB


## Deployment

### Docker
```bash
docker-compose up -d --build
