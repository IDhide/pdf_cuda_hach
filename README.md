# RC4 в PDF Revision 2: Теоретические механизмы и уязвимости

Образовательная реализация алгоритма RC4, используемого в устаревших спецификациях PDF 1.4 с Revision 2 шифрованием (40-битные ключи).

## ⚠️ ПРЕДУПРЕЖДЕНИЕ

**Этот код предназначен ТОЛЬКО для образовательных целей!**

40-битное RC4 шифрование является устаревшим и небезопасным. Не используйте его для защиты реальных данных.

## 📋 Содержание

- [Теоретические основы](#теоретические-основы)
- [Структура проекта](#структура-проекта)
- [Использование](#использование)
- [Уязвимости](#уязвимости)
- [Примеры](#примеры)

## 🔬 Теоретические основы

### Алгоритм RC4

RC4 (Rivest Cipher 4) - это потоковый шифр, состоящий из двух основных компонентов:

#### 1. KSA (Key Scheduling Algorithm)

Алгоритм ключевого расписания инициализирует внутреннее состояние шифра:

```
Инициализация:
  for i = 0 to 255:
    S[i] = i

Перемешивание:
  j = 0
  for i = 0 to 255:
    j = (j + S[i] + K[i mod L]) mod 256
    swap(S[i], S[j])
```

Где:
- **S** - вектор состояния (256 байт)
- **K** - секретный ключ
- **L** - длина ключа (для PDF Revision 2: L = 5 байт = 40 бит)

#### 2. PRGA (Pseudo-Random Generation Algorithm)

Генератор псевдослучайной последовательности (keystream):

```
i = 0, j = 0
while generating:
  i = (i + 1) mod 256
  j = (j + S[i]) mod 256
  swap(S[i], S[j])
  K = S[(S[i] + S[j]) mod 256]
  output K
```

#### 3. Шифрование/Расшифрование

```
Ciphertext = Plaintext XOR Keystream
Plaintext = Ciphertext XOR Keystream
```

### PDF Revision 2 Шифрование

В PDF 1.4 с Revision 2:
- Используется RC4 с 40-битным ключом (5 байт)
- Ключ генерируется из пароля через MD5 хэш
- Применяется к содержимому потоков и строк

## 📁 Структура проекта

```
.
├── rc4_pdf_revision2.py    # Основная реализация RC4 и PDF Revision 2
├── rc4_examples.py          # Примеры использования и анализ
└── README.md                # Документация
```

## 🚀 Использование

### Базовое использование RC4

```python
from rc4_pdf_revision2 import RC4

# Создание экземпляра с 40-битным ключом
key = b'\x01\x23\x45\x67\x89'  # 5 байт
rc4 = RC4(key)

# Шифрование
plaintext = b"Secret message"
ciphertext = rc4.encrypt(plaintext)

# Расшифрование
rc4_decrypt = RC4(key)
decrypted = rc4_decrypt.decrypt(ciphertext)
```

### Эмуляция PDF Revision 2

```python
from rc4_pdf_revision2 import PDFRevision2Crypto

# Шифрование PDF контента
pdf_content = b"%PDF-1.4\n..."
password = "MyPassword"

encrypted, key = PDFRevision2Crypto.encrypt_pdf_content(pdf_content, password)

# Расшифрование
decrypted = PDFRevision2Crypto.decrypt_pdf_content(encrypted, password)
```

### Запуск демонстраций

```bash
# Полная демонстрация с анализом
python3 rc4_pdf_revision2.py

# Примеры использования
python3 rc4_examples.py
```

## 🔓 Уязвимости

### 1. Малая длина ключа (40 бит)

**Проблема:** Пространство ключей = 2^40 ≈ 1.1 триллиона комбинаций

**Последствия:**
- Брутфорс возможен за часы/дни на современном оборудовании
- При скорости 1 млрд ключей/сек: ~18 минут до взлома

```python
Пространство ключей: 2^40 = 1,099,511,627,776
Время взлома (1 GHz): ~1,100 секунд ≈ 18 минут
```

### 2. Known Plaintext Attack (Атака на основе известного открытого текста)

**Проблема:** PDF файлы содержат предсказуемые структуры

Известные паттерны в PDF:
```
%PDF-1.4
/Type /Catalog
/Length
/Filter
```

**Атака:**
```python
# Атакующий знает фрагмент открытого текста
known_plaintext = b"%PDF-1.4"
known_ciphertext = encrypted[:8]

# Восстановление keystream
keystream = known_plaintext XOR known_ciphertext

# Расшифрование других частей
other_plaintext = other_ciphertext XOR keystream
```

### 3. Слабости самого RC4

- **Статистические смещения** в первых байтах keystream
- **Уязвимость к атакам на связанных ключах**
- **Предсказуемые паттерны** при слабых ключах

### 4. Повторное использование ключа

```python
C1 = P1 XOR Keystream
C2 = P2 XOR Keystream

C1 XOR C2 = P1 XOR P2  # Keystream исключается!
```

Атакующий получает XOR открытых текстов без знания ключа.

## 📊 Примеры

### Пример 1: Пошаговая демонстрация KSA

```python
def demonstrate_ksa_step_by_step():
    key = b'\x01\x23\x45\x67\x89'
    S = list(range(256))
    j = 0
    
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    
    return S
```

### Пример 2: Восстановление keystream

```python
# Известный фрагмент
known_plain = b"%PDF-1.4"
encrypted_doc = rc4.encrypt(full_document)

# Восстановление
keystream = bytes([p ^ c for p, c in zip(known_plain, encrypted_doc[:8])])

# Использование для расшифрования
decrypted = bytes([c ^ k for c, k in zip(encrypted_doc[:8], keystream)])
```

### Пример 3: Анализ производительности

```bash
Размер     | Время (мс)   | Скорость (MB/s)
--------------------------------------------------
      1KB  |         0.15 |           6.67
     10KB  |         1.23 |           8.13
    100KB  |        12.45 |           8.03
      1MB  |       124.56 |           8.03
```

## 🛡️ Рекомендации по безопасности

### ❌ НЕ используйте:
- RC4 с любой длиной ключа
- 40-битные ключи для любого алгоритма
- PDF Revision 2 шифрование

### ✅ Используйте вместо этого:
- **AES-256** в режиме GCM или CBC
- **Минимум 128-битные ключи** (лучше 256-бит)
- **Современные PDF стандарты** (Revision 6, AES-256)
- **Проверенные библиотеки** (cryptography, PyCryptodome)

### Пример безопасной альтернативы:

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# AES-256 вместо RC4
key = os.urandom(32)  # 256 бит
iv = os.urandom(16)

cipher = Cipher(
    algorithms.AES(key),
    modes.CBC(iv),
    backend=default_backend()
)

encryptor = cipher.encryptor()
ciphertext = encryptor.update(plaintext) + encryptor.finalize()
```

## 📚 Дополнительные ресурсы

### Научные статьи:
- Fluhrer, Mantin, Shamir (2001) - "Weaknesses in the Key Scheduling Algorithm of RC4"
- AlFardan, Bernstein, et al. (2013) - "On the Security of RC4 in TLS"

### Стандарты:
- PDF Reference 1.4 (Adobe Systems)
- RFC 7465 - Prohibiting RC4 Cipher Suites
- ISO 32000-2 (PDF 2.0)

### Инструменты для анализа:
- `qpdf` - анализ и модификация PDF
- `pdfcrack` - взлом PDF паролей
- `john` - John the Ripper с поддержкой PDF

## 🎓 Образовательные цели

Этот проект демонстрирует:

1. **Внутреннее устройство RC4** - KSA и PRGA алгоритмы
2. **Криптографические уязвимости** - практические атаки
3. **Историческую эволюцию** - почему старые стандарты устарели
4. **Важность длины ключа** - разница между 40 и 256 битами
5. **Практику безопасности** - что использовать вместо RC4

## ⚖️ Лицензия и ответственность

Этот код предоставляется "как есть" исключительно для образовательных целей.

**Автор не несет ответственности за:**
- Использование кода для незаконных целей
- Применение в продакшн системах
- Любой ущерб от использования этого кода

**Легальное использование:**
- ✅ Обучение криптографии
- ✅ Исследование безопасности
- ✅ Анализ устаревших систем
- ❌ Взлом защищенных систем без разрешения
- ❌ Защита реальных данных

## 🤝 Вклад

Этот проект создан в образовательных целях. Предложения по улучшению документации и примеров приветствуются.

## 📞 Контакты

Для вопросов об образовательном использовании криптографии и безопасности PDF.

---

**Помните:** Понимание слабых алгоритмов помогает создавать более безопасные системы! 🔐
