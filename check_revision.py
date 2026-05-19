#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка ревизии PDF и алгоритма
"""

import hashlib

# Ваш хэш
hash_str = "$pdf$1*2*40*-3904*1*16*cd44cd452e3d4c8b2a0a328795c98573*32*1e7be03f31514ab677026017c847ada400000000000000000000000000000000*32*69b631e4f68f0f57ee19d7e0b177b80dbc36adab26c3ee4734af003c4d2c9e26"

parts = hash_str.split('*')

V = int(parts[1])  # Версия
R = int(parts[2])  # Ревизия  
bits = int(parts[3])  # Длина ключа
P = int(parts[4])  # Permissions
file_id = parts[7] if len(parts) > 7 else "N/A"
u_field = parts[9] if len(parts) > 9 else "N/A"
o_field = parts[11] if len(parts) > 11 else "N/A"

print("╔════════════════════════════════════════════════════════════════╗")
print("║  Анализ вашего PDF                                            ║")
print("╚════════════════════════════════════════════════════════════════╝")
print()
print(f"V (версия):     {V}")
print(f"R (ревизия):    {R}")
print(f"Длина ключа:    {bits} бит ({bits // 8} байт)")
print(f"P (permissions): {P}")
print()
print(f"File ID:  {file_id}")
print(f"U-поле:   {u_field}")
print(f"O-поле:   {o_field}")
print()

# Анализ
print("═" * 70)
print("АНАЛИЗ")
print("═" * 70)
print()

if R == 2:
    print("✅ Revision 2 - наш CUDA код работает напрямую!")
    print()
    print("Алгоритм проверки:")
    print("  1. RC4(key, U-поле) → decrypted")
    print("  2. Сравнить decrypted с padding string")
    print("  3. Если совпадает → ключ найден")
    
elif R == 3:
    print("⚠️  Revision 3 - алгоритм ОТЛИЧАЕТСЯ от R=2!")
    print()
    print("Разница в алгоритмах:")
    print()
    print("R=2 (простой):")
    print("  1. RC4(key, U-поле) → decrypted")
    print("  2. Сравнить с padding")
    print()
    print("R=3 (сложнее):")
    print("  1. RC4(key, U-поле) → decrypted")
    print("  2. MD5(decrypted + file_id) → hash")
    print("  3. Сравнить hash с padding")
    print()
    print("❌ Наш текущий CUDA код НЕ БУДЕТ РАБОТАТЬ для R=3!")
    print("   Нужна модификация кода.")
    
else:
    print(f"⚠️  Revision {R} - неизвестная ревизия")

print()
print("═" * 70)
print("РЕКОМЕНДАЦИИ")
print("═" * 70)
print()

if R == 3:
    print("Для вашего файла (R=3) нужно:")
    print()
    print("1. Модифицировать CUDA код для поддержки R=3")
    print("2. Добавить MD5 хэширование в проверку")
    print("3. Использовать file_id в вычислениях")
    print()
    print("Я могу создать модифицированную версию!")
    print()
    print("Или попробуйте существующие инструменты:")
    print("  • john --format=pdf hash.txt")
    print("  • hashcat -m 10500 hash.txt")
    print()
    print("Но они будут перебирать ПАРОЛИ, а не ключи напрямую,")
    print("что намного медленнее (нужно MD5 для каждого пароля).")
    
elif R == 2:
    print("Ваш файл (R=2) полностью поддерживается!")
    print()
    print("Запустите:")
    print(f"  ./rc4_crack_cuda {u_field}")
    print()
    print("Время на RTX 4070 Ti: ~90 секунд")

print()
print("═" * 70)
print("ВОПРОС")
print("═" * 70)
print()
print("Хотите, чтобы я создал модифицированную версию для R=3?")
print("Это будет медленнее (нужен MD5), но всё равно быстрее")
print("чем перебор паролей.")
print()
