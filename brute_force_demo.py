#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация брутфорс атаки на 40-битное RC4 шифрование
"""

from rc4_pdf_revision2 import RC4
import time
import random


def simulate_brute_force_attack(target_ciphertext: bytes, 
                                known_plaintext: bytes,
                                actual_key: bytes = None,
                                max_attempts: int = 1000000) -> tuple:
    """
    Симуляция брутфорс атаки на 40-битный ключ
    
    Args:
        target_ciphertext: Зашифрованный текст
        known_plaintext: Известный фрагмент открытого текста
        actual_key: Реальный ключ (для демонстрации)
        max_attempts: Максимальное количество попыток
        
    Returns:
        (найденный_ключ, количество_попыток, время)
    """
    print("🔍 НАЧАЛО БРУТФОРС АТАКИ")
    print("=" * 70)
    print(f"Целевой зашифрованный текст: {target_ciphertext.hex().upper()}")
    print(f"Известный открытый текст: {known_plaintext}")
    print(f"Длина ключа: 5 байт (40 бит)")
    print(f"Пространство поиска: 2^40 = {2**40:,} ключей")
    print(f"Ограничение попыток: {max_attempts:,}")
    
    if actual_key:
        print(f"Реальный ключ (для проверки): {actual_key.hex().upper()}")
    
    print("\nПоиск ключа...")
    print("-" * 70)
    
    start_time = time.time()
    attempts = 0
    found_key = None
    
    # Для демонстрации: проверяем случайные ключи и реальный ключ
    # В реальной атаке перебирались бы все 2^40 комбинаций
    
    # Добавляем реальный ключ в список для гарантированного нахождения
    keys_to_try = []
    
    # Генерируем случайные ключи для демонстрации
    for _ in range(min(max_attempts - 1, 999999)):
        random_key = bytes([random.randint(0, 255) for _ in range(5)])
        keys_to_try.append(random_key)
    
    # Добавляем реальный ключ в случайную позицию
    if actual_key:
        insert_pos = random.randint(0, len(keys_to_try))
        keys_to_try.insert(insert_pos, actual_key)
    
    # Перебор ключей
    for i, test_key in enumerate(keys_to_try):
        attempts += 1
        
        # Пробуем расшифровать
        rc4 = RC4(test_key)
        decrypted = rc4.decrypt(target_ciphertext[:len(known_plaintext)])
        
        # Проверяем совпадение
        if decrypted == known_plaintext:
            found_key = test_key
            break
        
        # Прогресс каждые 100000 попыток
        if attempts % 100000 == 0:
            elapsed = time.time() - start_time
            speed = attempts / elapsed
            print(f"Попытка {attempts:>10,} | "
                  f"Скорость: {speed:>10,.0f} ключей/сек | "
                  f"Время: {elapsed:>6.2f}с")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("-" * 70)
    
    if found_key:
        print(f"✅ КЛЮЧ НАЙДЕН!")
        print(f"Найденный ключ: {found_key.hex().upper()}")
        print(f"Попыток: {attempts:,}")
        print(f"Время: {elapsed_time:.4f} секунд")
        print(f"Скорость: {attempts/elapsed_time:,.0f} ключей/сек")
        
        # Проверка
        rc4 = RC4(found_key)
        full_decrypted = rc4.decrypt(target_ciphertext)
        print(f"\nПолный расшифрованный текст: {full_decrypted}")
    else:
        print(f"❌ Ключ не найден за {attempts:,} попыток")
        print(f"Время: {elapsed_time:.4f} секунд")
    
    return found_key, attempts, elapsed_time


def estimate_real_brute_force():
    """
    Оценка времени реального брутфорса
    """
    print("\n" + "=" * 70)
    print("ОЦЕНКА ВРЕМЕНИ РЕАЛЬНОГО БРУТФОРСА")
    print("=" * 70)
    
    # Измеряем скорость проверки одного ключа
    test_key = b'\x01\x23\x45\x67\x89'
    test_data = b"Test data for speed measurement"
    
    iterations = 10000
    start = time.time()
    
    for _ in range(iterations):
        rc4 = RC4(test_key)
        rc4.encrypt(test_data)
    
    end = time.time()
    elapsed = end - start
    
    keys_per_second = iterations / elapsed
    
    print(f"\nИзмеренная скорость: {keys_per_second:,.0f} ключей/сек")
    print(f"(на одном ядре процессора)")
    
    # Расчеты для разных сценариев
    total_keys = 2 ** 40
    
    scenarios = [
        ("Одно ядро CPU", keys_per_second, 1),
        ("8 ядер CPU", keys_per_second, 8),
        ("GPU (оценка)", 1_000_000_000, 1),
        ("Кластер из 100 GPU", 1_000_000_000, 100),
    ]
    
    print("\n" + "-" * 70)
    print(f"{'Сценарий':<25} | {'Скорость':>15} | {'Время взлома':>20}")
    print("-" * 70)
    
    for scenario_name, speed, multiplier in scenarios:
        total_speed = speed * multiplier
        seconds = total_keys / total_speed
        
        if seconds < 60:
            time_str = f"{seconds:.1f} секунд"
        elif seconds < 3600:
            time_str = f"{seconds/60:.1f} минут"
        elif seconds < 86400:
            time_str = f"{seconds/3600:.1f} часов"
        else:
            time_str = f"{seconds/86400:.1f} дней"
        
        print(f"{scenario_name:<25} | {total_speed:>15,.0f} | {time_str:>20}")
    
    print("-" * 70)
    
    # Сравнение с более длинными ключами
    print("\nСРАВНЕНИЕ С ДРУГИМИ ДЛИНАМИ КЛЮЧЕЙ:")
    print("-" * 70)
    
    gpu_speed = 1_000_000_000  # 1 млрд ключей/сек
    
    key_lengths = [
        (40, "PDF Revision 2"),
        (56, "DES"),
        (128, "AES-128"),
        (256, "AES-256"),
    ]
    
    print(f"{'Длина ключа':<15} | {'Алгоритм':<20} | {'Время взлома (GPU)':>25}")
    print("-" * 70)
    
    for bits, name in key_lengths:
        keys = 2 ** bits
        seconds = keys / gpu_speed
        
        if seconds < 60:
            time_str = f"{seconds:.2e} секунд"
        elif seconds < 3600:
            time_str = f"{seconds/60:.2e} минут"
        elif seconds < 86400:
            time_str = f"{seconds/3600:.2e} часов"
        elif seconds < 31536000:
            time_str = f"{seconds/86400:.2e} дней"
        else:
            years = seconds / 31536000
            if years > 1e15:
                time_str = f"{years:.2e} лет (невозможно)"
            else:
                time_str = f"{years:.2e} лет"
        
        print(f"{bits} бит{' '*(11-len(str(bits)))} | {name:<20} | {time_str:>25}")
    
    print("-" * 70)


def demonstrate_dictionary_attack():
    """
    Демонстрация атаки по словарю (более реалистичная)
    """
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ: Атака по словарю паролей")
    print("=" * 70)
    
    # Реальный пароль
    real_password = "password123"
    
    # Словарь популярных паролей
    password_dictionary = [
        "123456", "password", "12345678", "qwerty", "123456789",
        "12345", "1234", "111111", "1234567", "dragon",
        "123123", "baseball", "iloveyou", "trustno1", "1234567890",
        "sunshine", "master", "welcome", "shadow", "ashley",
        "football", "jesus", "michael", "ninja", "mustang",
        "password123",  # Наш пароль здесь
    ]
    
    # Создаем зашифрованный документ
    from rc4_pdf_revision2 import PDFRevision2Crypto
    
    document = b"%PDF-1.4\nSecret document content"
    encrypted, _ = PDFRevision2Crypto.encrypt_pdf_content(document, real_password)
    
    print(f"Зашифрованный документ (первые 32 байта):")
    print(f"{encrypted[:32].hex().upper()}")
    print(f"\nРазмер словаря: {len(password_dictionary)} паролей")
    print(f"Реальный пароль: '{real_password}'")
    print("\nПоиск пароля...")
    print("-" * 70)
    
    start_time = time.time()
    
    for i, password in enumerate(password_dictionary, 1):
        # Пробуем расшифровать
        try:
            decrypted = PDFRevision2Crypto.decrypt_pdf_content(encrypted, password)
            
            # Проверяем, начинается ли с PDF заголовка
            if decrypted.startswith(b"%PDF"):
                end_time = time.time()
                print(f"✅ ПАРОЛЬ НАЙДЕН: '{password}'")
                print(f"Попыток: {i}")
                print(f"Время: {end_time - start_time:.4f} секунд")
                print(f"\nРасшифрованный документ:")
                print(decrypted.decode())
                break
        except:
            pass
        
        if i % 5 == 0:
            print(f"Проверено паролей: {i}/{len(password_dictionary)}")
    
    print("-" * 70)
    print("\n⚠️  Атака по словарю намного эффективнее полного брутфорса!")
    print("⚠️  Используйте сложные, уникальные пароли!")


if __name__ == "__main__":
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ БРУТФОРС АТАКИ НА RC4 (40 БИТ)")
    print("=" * 70)
    
    # Подготовка данных для атаки
    real_key = b'\x01\x23\x45\x67\x89'
    plaintext = b"This is a secret message!"
    
    # Шифрование
    rc4 = RC4(real_key)
    ciphertext = rc4.encrypt(plaintext)
    
    # Симуляция брутфорс атаки
    # (ограничиваем количество попыток для быстрой демонстрации)
    simulate_brute_force_attack(
        ciphertext, 
        plaintext[:10],  # Известны первые 10 байт
        actual_key=real_key,
        max_attempts=1000000
    )
    
    # Оценка реального времени
    estimate_real_brute_force()
    
    # Атака по словарю
    demonstrate_dictionary_attack()
    
    print("\n" + "=" * 70)
    print("ВЫВОДЫ")
    print("=" * 70)
    print("""
1. 40-битные ключи могут быть взломаны за часы на современном оборудовании
2. С GPU или специализированным оборудованием - за минуты
3. Атаки по словарю еще эффективнее для слабых паролей
4. 128-битные ключи практически невозможно взломать брутфорсом
5. Длина ключа критически важна для безопасности

НИКОГДА не используйте 40-битное шифрование для защиты данных!
    """)
