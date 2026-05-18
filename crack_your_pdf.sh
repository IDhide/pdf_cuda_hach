#!/bin/bash
# Специализированный скрипт для взлома вашего PDF

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  RC4 40-bit PDF Brute Force - Ваш файл                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Ваш хэш
HASH='$pdf$1*2*40*-3904*1*16*cd44cd452e3d4c8b2a0a328795c98573*32*1e7be03f31514ab677026017c847ada400000000000000000000000000000000*32*69b631e4f68f0f57ee19d7e0b177b80dbc36adab26c3ee4734af003c4d2c9e26'

# Парсинг
echo "Анализ хэша..."
echo "Формат: \$pdf\$V*R*bits*P*encryptMetadata*id_len*id*u_len*u*o_len*o"
echo ""

# Извлекаем поля
V=1
R=2
BITS=40
P=-3904
ENCRYPT_META=1
ID_LEN=16
FILE_ID="cd44cd452e3d4c8b2a0a328795c98573"
U_LEN=32
U_FIELD="1e7be03f31514ab677026017c847ada400000000000000000000000000000000"
O_LEN=32
O_FIELD="69b631e4f68f0f57ee19d7e0b177b80dbc36adab26c3ee4734af003c4d2c9e26"

echo "Параметры PDF:"
echo "  V (версия):           $V"
echo "  R (ревизия):          $R"
echo "  Длина ключа:          $BITS бит ($(($BITS / 8)) байт)"
echo "  P (permissions):      $P"
echo "  Encrypt metadata:     $ENCRYPT_META"
echo ""

echo "Данные документа:"
echo "  File ID ($ID_LEN байт):  $FILE_ID"
echo ""

echo "Поля шифрования:"
echo "  U-поле ($U_LEN байт):    $U_FIELD"
echo "  O-поле ($O_LEN байт):    $O_FIELD"
echo ""

# Проверка
if [ "$R" -eq 2 ] && [ "$BITS" -eq 40 ]; then
    echo "✅ Это PDF Revision 2 с 40-битным ключом!"
    echo "   Идеально подходит для брутфорса"
    echo ""
else
    echo "⚠️  Параметры: R=$R, bits=$BITS"
    if [ "$BITS" -gt 40 ]; then
        echo "❌ $BITS-битный ключ слишком длинный для брутфорса!"
        exit 1
    fi
fi

echo "═══════════════════════════════════════════════════════════════"
echo "ЗАПУСК БРУТФОРСА"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Проверяем наличие исполняемых файлов
if [ -f "./rc4_crack_cuda" ]; then
    echo "🚀 Запуск CUDA версии (быстро)..."
    echo ""
    echo "U-поле для брутфорса: $U_FIELD"
    echo ""
    echo "Команда:"
    echo "./rc4_crack_cuda $U_FIELD"
    echo ""
    echo "Оценка времени:"
    echo "  RTX 4090:    ~55 секунд"
    echo "  RTX 4070 Ti: ~90 секунд"
    echo "  RTX 3090:    ~110 секунд"
    echo ""
    read -p "Запустить? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./rc4_crack_cuda "$U_FIELD"
    fi
elif [ -f "./rc4_crack_cpu" ]; then
    echo "💻 Запуск CPU версии (медленно)..."
    echo ""
    echo "⚠️  ВНИМАНИЕ: CPU версия займёт ~25 дней на 16 ядрах!"
    echo ""
    echo "U-поле для брутфорса: $U_FIELD"
    echo ""
    echo "Команда:"
    echo "./rc4_crack_cpu $U_FIELD"
    echo ""
    read -p "Запустить? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./rc4_crack_cpu "$U_FIELD"
    fi
else
    echo "❌ Исполняемые файлы не найдены!"
    echo ""
    echo "Соберите сначала:"
    echo "  make cuda    # Для GPU версии"
    echo "  make cpu     # Для CPU версии"
    echo ""
    echo "Или запустите вручную:"
    echo ""
    echo "CUDA версия:"
    echo "  ./rc4_crack_cuda $U_FIELD"
    echo ""
    echo "CPU версия:"
    echo "  ./rc4_crack_cpu $U_FIELD"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Ваш PDF использует:"
echo "  • RC4 потоковый шифр"
echo "  • 40-битный ключ (очень слабо!)"
echo "  • Revision 2 (устаревший стандарт)"
echo ""
echo "Пространство ключей: 2^40 = 1,099,511,627,776 комбинаций"
echo ""
echo "После нахождения ключа, вы сможете расшифровать PDF."
echo ""
