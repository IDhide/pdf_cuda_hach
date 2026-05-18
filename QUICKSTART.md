# Быстрый старт

## 🚀 Запуск демонстраций

### 1. Основная демонстрация RC4 и PDF Revision 2

```bash
python3 rc4_pdf_revision2.py
```

**Что вы увидите:**
- Пошаговая работа алгоритма KSA (Key Scheduling Algorithm)
- Процесс шифрования и расшифрования PDF контента
- Демонстрация атаки Known Plaintext Attack
- Анализ сложности брутфорса 40-битного ключа

### 2. Примеры использования

```bash
python3 rc4_examples.py
```

**Что вы увидите:**
- 7 практических примеров использования RC4
- Анализ keystream и XOR свойств
- Восстановление keystream через известный текст
- Тест производительности на разных объемах данных
- Визуализация изменения состояния S

### 3. Демонстрация брутфорс атаки

```bash
python3 brute_force_demo.py
```

**Что вы увидите:**
- Симуляция брутфорс атаки на 40-битный ключ
- Оценка времени взлома на разном оборудовании
- Сравнение с другими длинами ключей (56, 128, 256 бит)
- Демонстрация атаки по словарю паролей

## 📚 Использование в коде

### Базовое шифрование/расшифрование

```python
from rc4_pdf_revision2 import RC4

# 40-битный ключ (5 байт)
key = b'\x01\x23\x45\x67\x89'

# Шифрование
rc4_enc = RC4(key)
ciphertext = rc4_enc.encrypt(b"Secret message")

# Расшифрование
rc4_dec = RC4(key)
plaintext = rc4_dec.decrypt(ciphertext)

print(plaintext)  # b"Secret message"
```

### Эмуляция PDF Revision 2

```python
from rc4_pdf_revision2 import PDFRevision2Crypto

# Шифрование с паролем
password = "MyPassword123"
content = b"%PDF-1.4\nDocument content..."

encrypted, key = PDFRevision2Crypto.encrypt_pdf_content(content, password)
print(f"Ключ: {key.hex()}")

# Расшифрование
decrypted = PDFRevision2Crypto.decrypt_pdf_content(encrypted, password)
print(decrypted)
```

### Анализ KSA алгоритма

```python
from rc4_pdf_revision2 import RC4

key = b'\xAA\xBB\xCC\xDD\xEE'
rc4 = RC4(key)

# Получить состояние после KSA
S = rc4.ksa()

print(f"Первые 10 элементов S: {S[:10]}")
print(f"Все элементы уникальны: {len(set(S)) == 256}")
```

## 🔍 Ключевые концепции

### 1. Структура RC4

```
┌─────────────────────────────────────┐
│         RC4 АЛГОРИТМ                │
├─────────────────────────────────────┤
│                                     │
│  1. KSA (Key Scheduling)            │
│     ├─ Инициализация S[0..255]      │
│     └─ Перемешивание с ключом K     │
│                                     │
│  2. PRGA (Keystream Generation)     │
│     ├─ Генерация псевдослучайных    │
│     └─ байтов из состояния S        │
│                                     │
│  3. Шифрование                      │
│     └─ Plaintext XOR Keystream      │
│                                     │
└─────────────────────────────────────┘
```

### 2. Формула KSA

```
Инициализация:
  S[i] = i, для i = 0..255

Перемешивание:
  j = (j + S[i] + K[i mod L]) mod 256
  swap(S[i], S[j])
```

### 3. Формула PRGA

```
i = (i + 1) mod 256
j = (j + S[i]) mod 256
swap(S[i], S[j])
output = S[(S[i] + S[j]) mod 256]
```

## ⚠️ Уязвимости

### 1. Малая длина ключа

```
40 бит = 2^40 = 1,099,511,627,776 комбинаций

На GPU (1 млрд ключей/сек):
  Время взлома ≈ 18 минут

На кластере из 100 GPU:
  Время взлома ≈ 11 секунд
```

### 2. Known Plaintext Attack

```python
# Атакующий знает:
known_plain = b"%PDF-1.4"
known_cipher = encrypted[:8]

# Восстанавливает keystream:
keystream = known_plain XOR known_cipher

# Расшифровывает остальное:
other_plain = other_cipher XOR keystream
```

### 3. Повторное использование ключа

```python
C1 = P1 XOR Keystream
C2 = P2 XOR Keystream

# Атакующий вычисляет:
C1 XOR C2 = P1 XOR P2  # Keystream исключается!
```

## 📊 Сравнение длин ключей

| Длина | Алгоритм | Комбинаций | Время взлома (GPU) |
|-------|----------|------------|-------------------|
| 40 бит | PDF Rev 2 | 1.1 трлн | 18 минут |
| 56 бит | DES | 72 квдрлн | 2.3 года |
| 128 бит | AES-128 | 3.4×10³⁸ | 10²² лет |
| 256 бит | AES-256 | 1.2×10⁷⁷ | 10⁶⁰ лет |

## 🛡️ Безопасные альтернативы

### Используйте AES вместо RC4

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# AES-256 в режиме GCM (рекомендуется)
key = os.urandom(32)  # 256 бит
nonce = os.urandom(12)

cipher = Cipher(
    algorithms.AES(key),
    modes.GCM(nonce),
    backend=default_backend()
)

# Шифрование
encryptor = cipher.encryptor()
ciphertext = encryptor.update(plaintext) + encryptor.finalize()
tag = encryptor.tag

# Расшифрование
decryptor = Cipher(
    algorithms.AES(key),
    modes.GCM(nonce, tag),
    backend=default_backend()
).decryptor()

plaintext = decryptor.update(ciphertext) + decryptor.finalize()
```

## 📖 Дополнительные ресурсы

### Документация
- [README.md](README.md) - Полная документация проекта
- [rc4_pdf_revision2.py](rc4_pdf_revision2.py) - Исходный код с комментариями

### Научные статьи
- Fluhrer, Mantin, Shamir (2001) - "Weaknesses in the Key Scheduling Algorithm of RC4"
- AlFardan, Bernstein, et al. (2013) - "On the Security of RC4 in TLS"

### Стандарты
- PDF Reference 1.4 (Adobe Systems)
- RFC 7465 - Prohibiting RC4 Cipher Suites
- ISO 32000-2 (PDF 2.0)

## 🎯 Образовательные цели

Этот проект помогает понять:

1. ✅ Как работает потоковый шифр RC4
2. ✅ Почему 40-битные ключи небезопасны
3. ✅ Как проводятся криптографические атаки
4. ✅ Важность выбора правильных алгоритмов
5. ✅ Эволюцию стандартов безопасности

## ⚖️ Правовая информация

**ВАЖНО:** Этот код предназначен ТОЛЬКО для образовательных целей.

✅ **Разрешено:**
- Изучение криптографии
- Исследование безопасности
- Анализ устаревших систем
- Образовательные проекты

❌ **Запрещено:**
- Взлом защищенных систем без разрешения
- Использование в продакшн системах
- Нарушение законов о компьютерной безопасности

## 🤝 Вопросы и поддержка

Если у вас есть вопросы об образовательном использовании этого кода:

1. Прочитайте [README.md](README.md)
2. Изучите примеры в [rc4_examples.py](rc4_examples.py)
3. Запустите демонстрации для лучшего понимания

---

**Помните:** Понимание слабых алгоритмов - ключ к созданию безопасных систем! 🔐
