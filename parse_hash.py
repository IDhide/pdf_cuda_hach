#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсинг хэша PDF из формата John the Ripper
"""

import sys

def parse_pdf_hash(hash_string):
    """
    Парсинг хэша в формате John the Ripper:
    $pdf$V*R*bits*P*encryptMetadata*id_len*id*u_len*u*o_len*o
    """
    parts = hash_string.strip().split('*')
    
    if not parts[0].startswith('$pdf$'):
        print("❌ Неверный формат хэша")
        return None
    
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Анализ PDF хэша                                              ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    # Парсинг полей (формат John the Ripper)
    V = int(parts[1])  # Версия алгоритма
    R = int(parts[2])  # Ревизия
    bits = int(parts[3])  # Длина ключа в битах
    P = int(parts[4])  # Permissions
    encrypt_metadata = int(parts[5])  # Шифровать ли метаданные
    id_len = int(parts[6])  # Длина ID
    file_id = parts[7]  # ID документа (hex)
    u_len = int(parts[8])  # Длина U-поля
    u_field = parts[9]  # U-поле (User password)
    o_len = int(parts[10])  # Длина O-поля
    o_field = parts[11]  # O-поле (Owner password)
    
    print(f"Параметры шифрования:")
    print(f"  V (версия):           {V}")
    print(f"  R (ревизия):          {R}")
    print(f"  Длина ключа:          {bits} бит ({bits // 8} байт)")
    print(f"  P (permissions):      {P}")
    print(f"  Encrypt metadata:     {encrypt_metadata}")
    print()
    
    print(f"Данные документа:")
    print(f"  File ID ({id_len} байт):  {file_id}")
    print()
    
    print(f"Поля шифрования:")
    print(f"  U-поле ({u_len} байт):    {u_field}")
    print(f"  O-поле ({o_len} байт):    {o_field}")
    print()
    
    # Проверка на Revision 2
    if R == 2 and bits == 40:
        print("✅ Это PDF Revision 2 с 40-битным ключом!")
        print("   Идеально подходит для нашего брутфорса")
        print()
    elif R == 3 and bits == 40:
        print("⚠️  Это PDF Revision 3 с 40-битным ключом")
        print("   Алгоритм похож на Revision 2, должно работать")
        print()
    else:
        print(f"⚠️  Это PDF Revision {R} с {bits}-битным ключом")
        print("   Наш инструмент оптимизирован для Revision 2 (40 бит)")
        if bits > 40:
            print(f"   ❌ {bits}-битный ключ слишком длинный для брутфорса!")
            print(f"   Пространство ключей: 2^{bits} = {2**bits:,}")
            return None
        print()
    
    return {
        'V': V,
        'R': R,
        'bits': bits,
        'P': P,
        'encrypt_metadata': encrypt_metadata,
        'file_id': file_id,
        'u_field': u_field,
        'o_field': o_field
    }

def main():
    if len(sys.argv) < 2:
        print("Использование: python3 parse_hash.py <hash_string>")
        print("Или: python3 parse_hash.py hash.txt")
        sys.exit(1)
    
    hash_input = sys.argv[1]
    
    # Если это файл, читаем из него
    if hash_input.endswith('.txt'):
        try:
            with open(hash_input, 'r') as f:
                hash_string = f.read().strip()
        except FileNotFoundError:
            print(f"❌ Файл не найден: {hash_input}")
            sys.exit(1)
    else:
        hash_string = hash_input
    
    # Парсим
    data = parse_pdf_hash(hash_string)
    
    if data:
        print("═" * 70)
        print("КОМАНДА ДЛЯ БРУТФОРСА")
        print("═" * 70)
        print()
        print("CUDA версия (быстрая):")
        print(f"./rc4_crack_cuda {data['u_field']}")
        print()
        print("CPU версия (медленная):")
        print(f"./rc4_crack_cpu {data['u_field']}")
        print()
        
        # Оценка времени
        if data['bits'] == 40:
            print("Оценка времени взлома:")
            print("  RTX 4090:    ~55 секунд")
            print("  RTX 4070 Ti: ~90 секунд")
            print("  RTX 3090:    ~110 секунд")
            print("  RTX 3080:    ~137 секунд")
            print("  CPU 16 ядер: ~25 дней")
        
        print()

if __name__ == "__main__":
    main()
