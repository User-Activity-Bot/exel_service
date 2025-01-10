import datetime
import pandas as pd
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from scally_client import ZMQClient

def gen_exel(username : str = None):
    if not username:
        raise "Username is required"
    
    creation_date_start = datetime.datetime.now().replace(hour=4, minute=0, second=0, microsecond=0)

    # Получение данных
    data = ZMQClient().get_document(username=username, creation_date_start=creation_date_start).get('documents')

    # Очистка данных - удаляем повторяющиеся статусы
    cleaned_data = [data[0]]  # Первую запись оставляем всегда
    for i in range(1, len(data)):
        if data[i]["status"] != data[i - 1]["status"]:
            cleaned_data.append(data[i])

    # Упорядочиваем данные по времени
    cleaned_data.sort(key=lambda x: datetime.datetime.fromisoformat(x["creation_date"]))

    # Формирование промежутков активности
    activity_summary = []
    hour_durations = defaultdict(datetime.timedelta)
    current_status = cleaned_data[0]["status"]
    start_time = datetime.datetime.fromisoformat(cleaned_data[0]["creation_date"])

    for i in range(1, len(cleaned_data) - 1):  # Убираем последнюю запись из цикла
        record = cleaned_data[i]
        timestamp = datetime.datetime.fromisoformat(record["creation_date"])

        if record["status"] != current_status:
            # Проверяем корректность временных промежутков
            if timestamp >= start_time:
                duration = timestamp - start_time
                activity_summary.append({
                    "Активность": f"Был в сети {start_time.strftime('%H:%M')} - {timestamp.strftime('%H:%M')}",
                    "Длительность сеанса (ч/м/с)": str(duration).split(".")[0]  # Убираем микросекунды
                })

                # Подсчёт времени по часам
                current_hour = start_time.hour
                while start_time < timestamp:
                    next_hour = (start_time + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                    if next_hour > timestamp:
                        next_hour = timestamp
                    hour_durations[current_hour] += (next_hour - start_time)
                    start_time = next_hour
                    current_hour = start_time.hour
            else:
                print(f"Ошибка времени: {start_time} > {timestamp}")

            # Обновляем текущий статус и время начала
            current_status = record["status"]
            start_time = timestamp

    # Определение самого посещаемого часа и времени, проведённого за этот час
    most_active_hour, max_duration = max(hour_durations.items(), key=lambda x: x[1], default=(None, datetime.timedelta(0)))
    most_active_hour_label = f"{most_active_hour}:00 - {most_active_hour + 1}:00" if most_active_hour is not None else "Нет данных"
    most_active_hour_duration = str(max_duration).split(".")[0]

    # Добавляем информацию о самом посещаемом часе
    for entry in activity_summary:
        entry["Самый посещаемый час"] = most_active_hour_label
        entry["Время за час"] = most_active_hour_duration

    # Сохраняем результат в Excel
    output_file = f"{username}.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Добавляем заголовок и дату создания
        summary_df = pd.DataFrame(activity_summary)
        summary_df.to_excel(writer, index=False, startrow=4, sheet_name="Отчёт об активности")

        workbook = writer.book
        worksheet = writer.sheets["Отчёт об активности"]

        # Добавляем заголовок
        worksheet["A1"] = "Отчёт по пользователю"
        worksheet["B1"] = username
        worksheet["A2"] = "Дата создания:"
        worksheet["B2"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        worksheet["A3"] = "Самый посещаемый час:"
        worksheet["B3"] = most_active_hour_label
        worksheet["A4"] = "Время за этот час:"
        worksheet["B4"] = most_active_hour_duration

        # Устанавливаем ширину колонок
        for col in range(1, len(summary_df.columns) + 1):
            col_letter = get_column_letter(col)
            worksheet.column_dimensions[col_letter].width = 30

    print(f"Отчёт сохранен в файл: {output_file}")
