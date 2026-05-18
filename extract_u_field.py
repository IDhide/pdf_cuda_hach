#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлечение U-поля из зашифрованного PDF для брутфорса
"""

import sys
import struct
import re


def extract_u_field_manual(pdf_path):
    """
    Извлечение U-поля вручную (без зависимостей)
    """
    print(f"Анализ PDF: {pdf_path}")
    print("-" * 70)
    
    with open(pdf_path, 'rb') as f:
        content = f.read()
    
    # Ищем объект Encrypt
    encrypt_pattern = rb'/Encrypt\s+(\d+)\s+(\d+)\s+R'
    match = re.search(encrypt_pattern, content)
    
    if not match:
        print("❌ Не найден объект /Encrypt")
        print("   PDF не зашифрован или использует нестандартный формат")
        return None
    
    encrypt_obj_num = int(match.group(1))
    print(f"✓ Найден объект Encrypt: {encrypt_obj_num} 0 R")
    
    # Ищем сам объект Encrypt
    obj_pattern = rb'%d\s+0\s+obj\s*<<(.*?)>>\s*endobj' % encrypt_obj_num
    match = re.search(obj_pattern, content, re.DOTALL)
    
    if not match:
        print(f"❌ Не найден объект {encrypt_obj_num} 0 obj")
        return None
    
    encrypt_dict = match.group(1)
    
    # Извлекаем параметры шифрования
    def extract_value(key, data):
        pattern = rb'/' + key.encode() + rb'\s*([^/\s>]+)'
        match = re.search(pattern, data)
        return match.group(1).strip() if match else None
    
    filter_val = extract_value('Filter', encrypt_dict)
    v_val = extract_value('V', encrypt_dict)
    r_val = extract_value('R', encrypt_dict)
    length_val = extract_value('Length', encrypt_dict)
    
    print(f"✓ Filter: {filter_val}")
    print(f"✓ V (версия): {v_val}")
    print(f"✓ R (ревизия): {r_val}")
    print(f"✓ Length: {length_val}")
    
    # Проверяем, что это Revision 2
    if r_val and int(r_val) != 2:
        print(f"\n⚠️  ВНИМАНИЕ: Это не Revision 2 (R={r_val.decode()})")
        print("   Этот инструмент оптимизирован для R=2 (40-битное шифрование)")
        print("   Для других ревизий может не работать")
    
    # Ищем U-поле
    u_pattern = rb'/U\s*<([0-9a-fA-F]+)>'
    match = re.search(u_pattern, encrypt_dict)
    
    if not match:
        # Попробуем найти в виде строки
        u_pattern = rb'/U\s*\(([^)]+)\)'
        match = re.search(u_pattern, encrypt_dict)
        if match:
            u_bytes = match.group(1)
            u_hex = u_bytes.hex()
        else:
            print("❌ Не найдено U-поле")
            return None
    else:
        u_hex = match.group(1).decode()
    
    # Ищем O-поле (для информации)
    o_pattern = rb'/O\s*<([0-9a-fA-F]+)>'
    match = re.search(o_pattern, encrypt_dict)
    o_hex = match.group(1).decode() if match else None
    
    # Ищем P-поле (permissions)
    p_pattern = rb'/P\s*(-?\d+)'
    match = re.search(p_pattern, encrypt_dict)
    p_val = int(match.group(1)) if match else None
    
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТ")
    print("=" * 70)
    
    print(f"\nU-поле (User password): {u_hex}")
    print(f"Длина: {len(u_hex) // 2} байт")
    
    if o_hex:
        print(f"\nO-поле (Owner password): {o_hex}")
        print(f"Длина: {len(o_hex) // 2} байт")
    
    if p_val is not None:
        print(f"\nP-поле (Permissions): {p_val}")
        print(f"Бинарно: {bin(p_val & 0xFFFFFFFF)}")
        
        # Расшифровка прав
        perms = []
        if p_val & 4: perms.append("Печать")
        if p_val & 8: perms.append("Изменение")
        if p_val & 16: perms.append("Копирование")
        if p_val & 32: perms.append("Аннотации")
        print(f"Разрешения: {', '.join(perms) if perms else 'Нет'}")
    
    print("\n" + "=" * 70)
    print("КОМАНДА ДЛЯ БРУТФОРСА")
    print("=" * 70)
    print(f"\nCUDA версия:")
    print(f"./rc4_crack_cuda {u_hex}")
    print(f"\nCPU версия:")
    print(f"./rc4_crack_cpu {u_hex}")
    
    return u_hex


def extract_u_field_pypdf2(pdf_path):
    """
    Извлечение U-поля используя PyPDF2
    """
    try:
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 не установлен")
        print("   Установите: pip install PyPDF2")
        return None
    
    print(f"Анализ PDF с PyPDF2: {pdf_path}")
    print("-" * 70)
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            
            if not pdf.is_encrypted:
                print("❌ PDF не зашифрован")
                return None
            
            print("✓ PDF зашифрован")
            
            # Получаем объект шифрования
            encrypt = pdf.trailer['/Encrypt']
            
            # Извлекаем параметры
            filter_val = encrypt.get('/Filter', 'N/A')
            v_val = encrypt.get('/V', 'N/A')
            r_val = encrypt.get('/R', 'N/A')
            length_val = encrypt.get('/Length', 'N/A')
            
            print(f"✓ Filter: {filter_val}")
            print(f"✓ V (версия): {v_val}")
            print(f"✓ R (ревизия): {r_val}")
            print(f"✓ Length: {length_val}")
            
            if r_val != 2:
                print(f"\n⚠️  ВНИМАНИЕ: Это не Revision 2 (R={r_val})")
            
            # Извлекаем U-поле
            u_field = encrypt.get('/U')
            if u_field:
                if isinstance(u_field, bytes):
                    u_hex = u_field.hex()
                else:
                    u_hex = u_field.encode().hex()
                
                print(f"\n✓ U-поле найдено: {u_hex}")
                print(f"  Длина: {len(u_hex) // 2} байт")
                
                # O-поле
                o_field = encrypt.get('/O')
                if o_field:
                    if isinstance(o_field, bytes):
                        o_hex = o_field.hex()
                    else:
                        o_hex = o_field.encode().hex()
                    print(f"\n✓ O-поле: {o_hex}")
                
                # Permissions
                p_val = encrypt.get('/P')
                if p_val:
                    print(f"\n✓ P-поле (Permissions): {p_val}")
                
                print("\n" + "=" * 70)
                print("КОМАНДА ДЛЯ БРУТФОРСА")
                print("=" * 70)
                print(f"\nCUDA версия:")
                print(f"./rc4_crack_cuda {u_hex}")
                print(f"\nCPU версия:")
                print(f"./rc4_crack_cpu {u_hex}")
                
                return u_hex
            else:
                print("❌ U-поле не найдено")
                return None
                
    except Exception as e:
        print(f"❌ Ошибка при чтении PDF: {e}")
        return None


def main():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Извлечение U-поля из зашифрованного PDF                      ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    if len(sys.argv) < 2:
        print("Использование: python3 extract_u_field.py <encrypted.pdf>")
        print("\nПример:")
        print("  python3 extract_u_field.py document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Пробуем сначала с PyPDF2
    u_hex = extract_u_field_pypdf2(pdf_path)
    
    # Если не получилось, пробуем вручную
    if not u_hex:
        print("\n" + "=" * 70)
        print("Пробуем ручное извлечение...")
        print("=" * 70 + "\n")
        u_hex = extract_u_field_manual(pdf_path)
    
    if u_hex:
        print("\n✅ Успешно извлечено U-поле!")
        
        # Сохраняем в файл
        output_file = "u_field.txt"
        with open(output_file, 'w') as f:
            f.write(u_hex)
        print(f"\n💾 U-поле сохранено в файл: {output_file}")
        
        # Проверка длины
        if len(u_hex) != 64:  # 32 байта = 64 hex символа
            print(f"\n⚠️  ВНИМАНИЕ: Нестандартная длина U-поля: {len(u_hex) // 2} байт")
            print("   Ожидается 32 байта для PDF Revision 2")
    else:
        print("\n❌ Не удалось извлечь U-поле")
        sys.exit(1)


if __name__ == "__main__":
    main()
