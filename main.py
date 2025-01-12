import os
import time
import datetime
import psycopg2
import psycopg2.extras

from dotenv import load_dotenv, find_dotenv

from utils import get_user_status, gen_exel, is_midnight
from sending_alerts import send_document_via_telegram

load_dotenv(find_dotenv())

DB_NAME = os.getenv('NAME')
DB_USER = os.getenv('USER')
DB_PASSWORD = os.getenv('PASSWORD')
DB_HOST = os.getenv('HOST')
DB_PORT = os.getenv('PORT')

def main():
    """
    Функция коннектится к базе PostgreSQL и делает выборку:
    - track_id, plan, status из таблицы actions_action
    - status из связанной payment_payment
    - user_id (кастомное поле) из таблицы user_activity_user
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        query = """
            SELECT 
                a.track_id,
                a.plan,
                a.status AS action_status,
                p.status AS payment_status,
                u.user_id AS custom_user_id
            FROM actions_action a
            LEFT JOIN payment_payment p ON a.payment_id = p.id
            LEFT JOIN users_user u ON a.user_id = u.id;
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        for row in rows:
            chat_id = row.get("custom_user_id")
            track_id = row.get("track_id")
            plan = row['plan']
            action_status = row['action_status']
            payment_status = row['payment_status']
            
            if plan == "full_data" and payment_status == "success" and action_status == "active":
                table_path = gen_exel(track_id)

                send_document_via_telegram(chat_id, table_path)
                print(f"Таблица {table_path} отправлена пользователю {chat_id}")

            
    except psycopg2.Error as e:
        print("Ошибка при работе с PostgreSQL:", e)
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

main()

while True:
    if is_midnight():
        pass