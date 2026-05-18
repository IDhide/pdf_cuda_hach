#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Реализация алгоритма RC4 для PDF Revision 2 (40-битное шифрование)

Этот код демонстрирует теоретические механизмы RC4, используемые в устаревших
спецификациях PDF 1.4 с Revision 2 шифрованием.

ВНИМАНИЕ: Этот алгоритм устарел и небезопасен! Используется только в образовательных целях.
"""

import hashlib
from typing import List, Tuple


class RC4:
    """
    Реализация потокового шифра RC4
    
    Состоит из двух основных этапов:
    1. KSA (Key Scheduling Algorithm) - алгоритм ключевого расписания
    2. PRGA (Pseudo-Random Generation Algorithm) - генератор псевдослучайной последовательности
    """
    
    def __init__(self, key: bytes):
        """
        Инициализация RC4 с заданным ключом
        
        Args:
            key: Секретный ключ (для PDF Revision 2 обычно 5 байт = 40 бит)
        """
        self.key = key
        self.key_length = len(key)
        self.S = list(range(256))  # Вектор состояния (256 байт)
        
    def ksa(self) -> List[int]:
        """
        Key Scheduling Algorithm (KSA)
        
        Инициализирует внутреннее состояние шифра путем перемешивания
        массива S с использованием байтов секретного ключа.
        
        Алгоритм:
        1. Инициализация S[i] = i для i от 0 до 255
        2. Перемешивание: j = (j + S[i] + K[i mod L]) mod 256
        3. Обмен S[i] и S[j]
        
        Returns:
            Перемешанный массив состояния S
        """
        S = self.S.copy()
        j = 0
        
        # Перемешивание массива состояния
        for i in range(256):
            # Формула: j = (j + S[i] + K[i mod L]) mod 256
            j = (j + S[i] + self.key[i % self.key_length]) % 256
            
            # Обмен значений S[i] и S[j]
            S[i], S[j] = S[j], S[i]
            
        return S
    
    def prga(self, S: List[int], length: int) -> bytes:
        """
        Pseudo-Random Generation Algorithm (PRGA)
        
        Генерирует псевдослучайную последовательность байтов (keystream),
        которая используется для XOR с открытым текстом.
        
        Args:
            S: Перемешанный массив состояния из KSA
            length: Длина требуемой последовательности
            
        Returns:
            Псевдослучайная последовательность байтов
        """
        i = 0
        j = 0
        keystream = []
        
        for _ in range(length):
            # Обновление индексов
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            
            # Обмен значений
            S[i], S[j] = S[j], S[i]
            
            # Генерация байта keystream
            K = S[(S[i] + S[j]) % 256]
            keystream.append(K)
            
        return bytes(keystream)
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Шифрование данных с использованием RC4
        
        Args:
            plaintext: Открытый текст
            
        Returns:
            Зашифрованный текст
        """
        # Инициализация состояния (KSA)
        S = self.ksa()
        
        # Генерация keystream (PRGA)
        keystream = self.prga(S, len(plaintext))
        
        # XOR открытого текста с keystream
        ciphertext = bytes([p ^ k for p, k in zip(plaintext, keystream)])
        
        return ciphertext
    
    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Расшифрование данных с использованием RC4
        
        Благодаря свойству XOR, расшифрование идентично шифрованию
        
        Args:
            ciphertext: Зашифрованный текст
            
        Returns:
            Открытый текст
        """
        return self.encrypt(ciphertext)  # RC4 симметричен


class PDFRevision2Crypto:
    """
    Эмуляция криптографической схемы PDF Revision 2
    
    Демонстрирует слабости 40-битного шифрования:
    - Малая длина ключа (5 байт)
    - Уязвимость к атакам на основе известного открытого текста
    """
    
    @staticmethod
    def derive_encryption_key(password: str, salt: bytes = b'') -> bytes:
        """
        Генерация ключа шифрования из пароля (упрощенная версия)
        
        В реальном PDF используется более сложная схема с использованием
        MD5 хэша, ID документа, и других параметров.
        
        Args:
            password: Пароль пользователя
            salt: Соль (опционально)
            
        Returns:
            40-битный ключ (5 байт)
        """
        # Хэширование пароля с солью
        hash_input = password.encode('utf-8') + salt
        hash_result = hashlib.md5(hash_input).digest()
        
        # Усечение до 40 бит (5 байт) для эмуляции PDF Revision 2
        key_40bit = hash_result[:5]
        
        return key_40bit
    
    @staticmethod
    def encrypt_pdf_content(content: bytes, password: str) -> Tuple[bytes, bytes]:
        """
        Шифрование содержимого PDF
        
        Args:
            content: Содержимое для шифрования
            password: Пароль
            
        Returns:
            Кортеж (зашифрованное содержимое, использованный ключ)
        """
        # Генерация ключа из пароля
        key = PDFRevision2Crypto.derive_encryption_key(password)
        
        # Шифрование с использованием RC4
        rc4 = RC4(key)
        encrypted = rc4.encrypt(content)
        
        return encrypted, key
    
    @staticmethod
    def decrypt_pdf_content(encrypted: bytes, password: str) -> bytes:
        """
        Расшифрование содержимого PDF
        
        Args:
            encrypted: Зашифрованное содержимое
            password: Пароль
            
        Returns:
            Расшифрованное содержимое
        """
        # Генерация ключа из пароля
        key = PDFRevision2Crypto.derive_encryption_key(password)
        
        # Расшифрование с использованием RC4
        rc4 = RC4(key)
        decrypted = rc4.decrypt(encrypted)
        
        return decrypted


def demonstrate_ksa_step_by_step():
    """
    Пошаговая демонстрация работы KSA алгоритма
    """
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Key Scheduling Algorithm (KSA)")
    print("=" * 70)
    
    # Пример 40-битного ключа
    key = b'\x01\x23\x45\x67\x89'  # 5 байт = 40 бит
    print(f"\nСекретный ключ K: {key.hex().upper()}")
    print(f"Длина ключа L: {len(key)} байт ({len(key) * 8} бит)")
    
    # Инициализация
    S = list(range(256))
    print(f"\nНачальное состояние S[0:10]: {S[:10]}")
    
    # Перемешивание (показываем первые 10 итераций)
    j = 0
    print("\nПервые 10 итераций перемешивания:")
    print(f"{'i':>3} | {'S[i]':>5} | {'K[i%L]':>7} | {'j':>5} | Обмен")
    print("-" * 50)
    
    for i in range(10):
        old_j = j
        j = (j + S[i] + key[i % len(key)]) % 256
        print(f"{i:3} | {S[i]:5} | {key[i % len(key)]:7} | {j:5} | S[{i}] <-> S[{j}]")
        S[i], S[j] = S[j], S[i]
    
    # Завершаем оставшиеся итерации
    for i in range(10, 256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    
    print(f"\nКонечное состояние S[0:10]: {S[:10]}")
    print("(Массив полностью перемешан)")


def demonstrate_encryption():
    """
    Демонстрация полного цикла шифрования/расшифрования
    """
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ: Шифрование и расшифрование PDF Revision 2")
    print("=" * 70)
    
    # Исходные данные
    password = "secret123"
    plaintext = b"This is a confidential PDF document content."
    
    print(f"\nПароль: {password}")
    print(f"Открытый текст: {plaintext.decode()}")
    print(f"Длина: {len(plaintext)} байт")
    
    # Шифрование
    encrypted, key = PDFRevision2Crypto.encrypt_pdf_content(plaintext, password)
    print(f"\n40-битный ключ: {key.hex().upper()}")
    print(f"Зашифрованный текст (hex): {encrypted.hex().upper()}")
    
    # Расшифрование
    decrypted = PDFRevision2Crypto.decrypt_pdf_content(encrypted, password)
    print(f"\nРасшифрованный текст: {decrypted.decode()}")
    print(f"Совпадение: {plaintext == decrypted}")


def demonstrate_known_plaintext_attack():
    """
    Демонстрация уязвимости к атаке на основе известного открытого текста
    """
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ: Уязвимость к Known Plaintext Attack")
    print("=" * 70)
    
    print("\nПредположим, атакующий знает:")
    print("1. Фрагмент открытого текста (например, стандартный PDF заголовок)")
    print("2. Соответствующий зашифрованный текст")
    
    # Известный фрагмент (типичный для PDF)
    known_plaintext = b"%PDF-1.4"
    password = "secret123"
    
    # Шифруем
    key = PDFRevision2Crypto.derive_encryption_key(password)
    rc4 = RC4(key)
    encrypted = rc4.encrypt(known_plaintext)
    
    print(f"\nИзвестный открытый текст: {known_plaintext}")
    print(f"Зашифрованный текст: {encrypted.hex().upper()}")
    
    # Атакующий может восстановить keystream
    keystream = bytes([p ^ c for p, c in zip(known_plaintext, encrypted)])
    print(f"Восстановленный keystream: {keystream.hex().upper()}")
    
    print("\nС восстановленным keystream атакующий может:")
    print("- Расшифровать другие части документа")
    print("- Модифицировать зашифрованный контент")
    print("- Провести дифференциальный криптоанализ")
    
    print("\n⚠️  ВЫВОД: 40-битное шифрование RC4 в PDF Revision 2 НЕБЕЗОПАСНО!")


def brute_force_40bit_demo():
    """
    Демонстрация теоретической возможности брутфорса 40-битного ключа
    """
    print("\n" + "=" * 70)
    print("АНАЛИЗ: Сложность брутфорса 40-битного ключа")
    print("=" * 70)
    
    key_space = 2 ** 40
    print(f"\nПространство ключей: 2^40 = {key_space:,} возможных ключей")
    print(f"Это примерно: {key_space / 1e12:.2f} триллионов комбинаций")
    
    # Оценка времени взлома
    keys_per_second = 1_000_000_000  # 1 миллиард ключей в секунду (современное оборудование)
    seconds = key_space / keys_per_second
    hours = seconds / 3600
    days = hours / 24
    
    print(f"\nПри скорости {keys_per_second:,} ключей/сек:")
    print(f"- Время взлома: {seconds:,.0f} секунд")
    print(f"- Это примерно: {hours:.1f} часов или {days:.2f} дней")
    
    print("\n⚠️  С современным оборудованием 40-битный ключ взламывается за часы!")
    print("⚠️  Для сравнения: 128-битный ключ потребует миллиарды лет")


if __name__ == "__main__":
    # Запуск всех демонстраций
    demonstrate_ksa_step_by_step()
    demonstrate_encryption()
    demonstrate_known_plaintext_attack()
    brute_force_40bit_demo()
    
    print("\n" + "=" * 70)
    print("ЗАКЛЮЧЕНИЕ")
    print("=" * 70)
    print("""
PDF Revision 2 с 40-битным RC4 шифрованием имеет критические слабости:

1. МАЛАЯ ДЛИНА КЛЮЧА (40 бит)
   - Пространство ключей слишком мало для современных вычислительных мощностей
   - Брутфорс возможен за часы/дни

2. УЯЗВИМОСТЬ К KNOWN PLAINTEXT ATTACK
   - PDF файлы содержат предсказуемые структуры (%PDF-, /Type, /Length)
   - Атакующий может восстановить keystream
   - Возможна модификация зашифрованного контента

3. СЛАБОСТИ RC4
   - Статистические смещения в keystream
   - Уязвимость к атакам на основе связанных ключей
   - Предсказуемость первых байтов выхода

РЕКОМЕНДАЦИИ:
✓ Используйте современные стандарты (AES-256)
✓ Избегайте PDF файлов с Revision 2 шифрованием
✓ Обновите старые защищенные PDF на новые стандарты
✓ Используйте ключи длиной минимум 128 бит

Этот код предназначен ТОЛЬКО для образовательных целей!
    """)
