import os
import requests

def send_telegram_message( chat_id: int, text: str) -> dict:
    """
    Отправляет сообщение через Telegram-бота.
    
    :param token: Токен Telegram-бота.
    :param chat_id: ID чата, в который нужно отправить сообщение.
    :param text: Текст сообщения.
    :return: Ответ Telegram API в формате JSON.
    """
    
    token = os.getenv("BOT_TOKEN")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def send_document_via_telegram(chat_id, file_path):
    """
    Отправляет документ в Telegram через бота.
    """
    token = os.getenv("BOT_TOKEN")
    
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    with open(file_path, 'rb') as file:
        response = requests.post(url, data={'chat_id': chat_id}, files={'document': file})
    if response.status_code != 200:
        print(f"Ошибка отправки сообщения: {response.text}")
    else:
        print(f"Сообщение успешно отправлено пользователю {chat_id}")