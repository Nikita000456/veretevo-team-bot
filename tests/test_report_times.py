#!/usr/bin/env python3
"""
Тестовый скрипт для проверки времени отправки отчетов
"""

import datetime
import pytz

def test_report_times():
    """Проверка времени отправки отчетов"""
    
    # Создаем московский часовой пояс
    moscow_tz = pytz.timezone('Europe/Moscow')
    utc_tz = pytz.timezone('UTC')
    
    # Текущее время
    now_utc = datetime.datetime.now(utc_tz)
    now_moscow = now_utc.astimezone(moscow_tz)
    
    print(f"🕐 Текущее время:")
    print(f"   UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   MSK: {now_moscow.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Время утреннего отчета
    morning_moscow = datetime.time(hour=7, minute=30)
    morning_dt_moscow = moscow_tz.localize(datetime.datetime.combine(now_moscow.date(), morning_moscow))
    morning_dt_utc = morning_dt_moscow.astimezone(utc_tz)
    
    print(f"\n🌅 Утренний отчет:")
    print(f"   MSK: {morning_dt_moscow.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   UTC: {morning_dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Время вечернего отчета
    evening_moscow = datetime.time(hour=18, minute=0)
    evening_dt_moscow = moscow_tz.localize(datetime.datetime.combine(now_moscow.date(), evening_moscow))
    evening_dt_utc = evening_dt_moscow.astimezone(utc_tz)
    
    print(f"\n🌆 Вечерний отчет:")
    print(f"   MSK: {evening_dt_moscow.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   UTC: {evening_dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Проверяем, когда будет следующий отчет
    if now_moscow.time() < morning_moscow:
        next_report = morning_dt_moscow
        report_type = "утренний"
    elif now_moscow.time() < evening_moscow:
        next_report = evening_dt_moscow
        report_type = "вечерний"
    else:
        # Следующий утренний отчет завтра
        tomorrow = now_moscow.date() + datetime.timedelta(days=1)
        next_report = moscow_tz.localize(datetime.datetime.combine(tomorrow, morning_moscow))
        report_type = "утренний (завтра)"
    
    time_until = next_report - now_moscow
    hours, remainder = divmod(time_until.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print(f"\n⏰ Следующий отчет:")
    print(f"   Тип: {report_type}")
    print(f"   Время: {next_report.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   Через: {time_until.days}д {hours}ч {minutes}м {seconds}с")

if __name__ == "__main__":
    test_report_times() 