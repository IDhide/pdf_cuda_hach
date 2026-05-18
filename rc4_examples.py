#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Примеры использования RC4 и анализ безопасности PDF Revision 2
"""

from rc4_pdf_revision2 import RC4, PDFRevision2Crypto
import time


def example_basic_rc4():
    """
    Базовый пример использования RC4
    """
    print("ПРИМЕР 1: Базовое использование RC4")
    print("-" * 50)
    
    # 40-битный ключ (5 байт)
    key = b'\x01\x23\x45\x67\x89'
    plaintext = b"Hello, World!"
    
    print(f"Ключ: {key.hex().upper()}")
    print(f"Открытый текст: {plaintext.decode()}")
    
    # Шифрование
    rc4_encrypt = RC4(key)
    ciphertext = rc4_encrypt.encrypt(plaintext)
    print(f"Зашифровано: {ciphertext.hex().upper()}")
    
    # Расшифрование
    rc4_decrypt = RC4(key)
    decrypted = rc4_decrypt.decrypt(ciphertext)
    print(f"Расшифровано: {decrypted.decode()}")
    print(f"Успех: {plaintext == decrypted}\n")


def example_pdf_encryption():
    """
    Пример шифрования PDF контента
    """
    print("ПРИМЕР 2: Шифрование PDF контента")
    print("-" * 50)
    
    # Типичное содержимое PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj"""
    
    password = "MySecretPassword123"
    
    print(f"Пароль: {password}")
    print(f"Размер контента: {len(pdf_content)} байт")
    
    # Шифрование
    encrypted, key = PDFRevision2Crypto.encrypt_pdf_content(pdf_content, password)
    print(f"\nКлюч (40 бит): {key.hex().upper()}")
    print(f"Первые 32 байта зашифрованного контента:")
    print(f"{encrypted[:32].hex().upper()}")
    
    # Расшифрование
    decrypted = PDFRevision2Crypto.decrypt_pdf_content(encrypted, password)
    print(f"\nРасшифровка успешна: {pdf_content == decrypted}")
    
    # Попытка с неверным паролем
    wrong_decrypted = PDFRevision2Crypto.decrypt_pdf_content(encrypted, "WrongPassword")
    print(f"С неверным паролем: {pdf_content == wrong_decrypted}")
    print(f"Результат с неверным паролем (первые 20 байт): {wrong_decrypted[:20]}\n")


def example_keystream_analysis():
    """
    Анализ keystream и демонстрация XOR свойств
    """
    print("ПРИМЕР 3: Анализ keystream")
    print("-" * 50)
    
    key = b'\xAA\xBB\xCC\xDD\xEE'
    plaintext1 = b"Message One"
    plaintext2 = b"Message Two"
    
    # Шифруем оба сообщения одним ключом
    rc4_1 = RC4(key)
    ciphertext1 = rc4_1.encrypt(plaintext1)
    
    rc4_2 = RC4(key)
    ciphertext2 = rc4_2.encrypt(plaintext2)
    
    print(f"Открытый текст 1: {plaintext1.decode()}")
    print(f"Зашифрованный 1:  {ciphertext1.hex().upper()}")
    print(f"\nОткрытый текст 2: {plaintext2.decode()}")
    print(f"Зашифрованный 2:  {ciphertext2.hex().upper()}")
    
    # XOR двух зашифрованных текстов
    xor_result = bytes([c1 ^ c2 for c1, c2 in zip(ciphertext1, ciphertext2)])
    print(f"\nXOR зашифрованных: {xor_result.hex().upper()}")
    
    # Это эквивалентно XOR открытых текстов!
    xor_plain = bytes([p1 ^ p2 for p1, p2 in zip(plaintext1, plaintext2)])
    print(f"XOR открытых:      {xor_plain.hex().upper()}")
    print(f"\nСовпадают: {xor_result == xor_plain}")
    print("⚠️  Это демонстрирует опасность повторного использования ключа!\n")


def example_known_plaintext_recovery():
    """
    Восстановление keystream через известный открытый текст
    """
    print("ПРИМЕР 4: Восстановление keystream")
    print("-" * 50)
    
    # Секретный ключ (неизвестен атакующему)
    secret_key = b'\x12\x34\x56\x78\x9A'
    
    # Документ содержит известную структуру
    full_document = b"%PDF-1.4\nThis is secret content that attacker wants to read."
    known_part = b"%PDF-1.4"  # Атакующий знает этот фрагмент
    
    # Шифрование
    rc4 = RC4(secret_key)
    encrypted_doc = rc4.encrypt(full_document)
    
    print(f"Полный документ ({len(full_document)} байт):")
    print(f"{full_document[:50]}...")
    print(f"\nИзвестная часть: {known_part.decode()}")
    print(f"Зашифрованный документ (первые 32 байта):")
    print(f"{encrypted_doc[:32].hex().upper()}")
    
    # АТАКА: Восстановление keystream
    known_encrypted = encrypted_doc[:len(known_part)]
    recovered_keystream = bytes([p ^ c for p, c in zip(known_part, known_encrypted)])
    
    print(f"\n🔓 Восстановленный keystream (первые {len(known_part)} байт):")
    print(f"{recovered_keystream.hex().upper()}")
    
    # Теперь атакующий может расшифровать начало документа
    decrypted_part = bytes([c ^ k for c, k in zip(encrypted_doc[:len(recovered_keystream)], 
                                                    recovered_keystream)])
    print(f"\n🔓 Расшифрованная часть: {decrypted_part.decode()}")
    print("⚠️  Атакующий успешно восстановил известную часть!\n")


def example_weak_key_patterns():
    """
    Демонстрация слабых паттернов ключей
    """
    print("ПРИМЕР 5: Слабые паттерны ключей")
    print("-" * 50)
    
    weak_keys = [
        (b'\x00\x00\x00\x00\x00', "Нулевой ключ"),
        (b'\xFF\xFF\xFF\xFF\xFF', "Все единицы"),
        (b'\x01\x02\x03\x04\x05', "Последовательный"),
        (b'\xAA\xAA\xAA\xAA\xAA', "Повторяющийся паттерн"),
    ]
    
    plaintext = b"Test message"
    
    print(f"Открытый текст: {plaintext.decode()}\n")
    
    for key, description in weak_keys:
        rc4 = RC4(key)
        encrypted = rc4.encrypt(plaintext)
        print(f"{description:25} | Ключ: {key.hex().upper()} | "
              f"Зашифровано: {encrypted.hex().upper()}")
    
    print("\n⚠️  Слабые ключи создают предсказуемые паттерны!\n")


def example_performance_test():
    """
    Тест производительности RC4
    """
    print("ПРИМЕР 6: Тест производительности")
    print("-" * 50)
    
    key = b'\x01\x23\x45\x67\x89'
    
    # Тест на разных размерах данных
    sizes = [1024, 10240, 102400, 1024000]  # 1KB, 10KB, 100KB, 1MB
    
    print(f"{'Размер':>10} | {'Время (мс)':>12} | {'Скорость (MB/s)':>15}")
    print("-" * 50)
    
    for size in sizes:
        data = b'X' * size
        
        start = time.time()
        rc4 = RC4(key)
        encrypted = rc4.encrypt(data)
        end = time.time()
        
        elapsed_ms = (end - start) * 1000
        speed_mbps = (size / (1024 * 1024)) / (end - start) if end > start else 0
        
        size_str = f"{size // 1024}KB" if size < 1024000 else f"{size // 1024000}MB"
        print(f"{size_str:>10} | {elapsed_ms:>12.2f} | {speed_mbps:>15.2f}")
    
    print()


def example_state_visualization():
    """
    Визуализация изменения состояния S
    """
    print("ПРИМЕР 7: Визуализация состояния S")
    print("-" * 50)
    
    key = b'\x01\x23\x45\x67\x89'
    rc4 = RC4(key)
    
    # Начальное состояние
    S_initial = list(range(256))
    print("Начальное состояние S (первые 20 элементов):")
    print(S_initial[:20])
    
    # После KSA
    S_after_ksa = rc4.ksa()
    print("\nПосле KSA (первые 20 элементов):")
    print(S_after_ksa[:20])
    
    # Статистика изменений
    changes = sum(1 for i in range(256) if S_initial[i] != S_after_ksa[i])
    print(f"\nИзменено элементов: {changes} из 256 ({changes/256*100:.1f}%)")
    
    # Проверка перестановки
    is_permutation = sorted(S_after_ksa) == list(range(256))
    print(f"Является перестановкой: {is_permutation}\n")


if __name__ == "__main__":
    print("=" * 70)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ RC4 И АНАЛИЗ БЕЗОПАСНОСТИ")
    print("=" * 70)
    print()
    
    example_basic_rc4()
    example_pdf_encryption()
    example_keystream_analysis()
    example_known_plaintext_recovery()
    example_weak_key_patterns()
    example_performance_test()
    example_state_visualization()
    
    print("=" * 70)
    print("ВАЖНЫЕ ВЫВОДЫ")
    print("=" * 70)
    print("""
1. RC4 - это потоковый шифр, где шифрование = расшифрование
2. 40-битные ключи слишком слабы для современных угроз
3. Повторное использование ключа раскрывает информацию
4. Известный открытый текст позволяет восстановить keystream
5. PDF структуры предсказуемы, что делает атаки проще

НИКОГДА не используйте RC4 с 40-битными ключами в продакшене!
    """)
