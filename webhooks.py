import hashlib
import hmac

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def github_webhook(request):
    """Обработчик webhook от GitHub с проверкой подписи"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    # Получаем подпись из заголовка
    signature = request.META.get('HTTP_X_HUB_SIGNATURE_256')
    if not signature:
        return HttpResponseForbidden('Signature header missing')

    # Создаем HMAC подпись
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    expected_signature = 'sha256=' + hmac.new(
        secret, 
        request.body, 
        hashlib.sha256
    ).hexdigest()

    # Сравниваем подписи
    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponseForbidden('Invalid signature')

    # Здесь логика деплоя
    try:
        # Пример: обновление кода и перезапуск
        import subprocess
        subprocess.run(['git', 'pull'])
        subprocess.run(['docker-compose', 'up', '-d', '--build'])
        return HttpResponse('Deployment successful')
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)
