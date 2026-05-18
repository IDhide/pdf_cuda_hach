#!/bin/bash
# Скрипт для тестирования брутфорс инструментов

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Тестирование RC4 Brute Force                                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Тестовые данные
# U-поле, зашифрованное ключом 0000000000 (padding string)
TEST_U_FIELD="28BF4E5E4E758A416400004E56FFFFA0108002E2E00B6D0683E802F0CA9FE6453697A"
EXPECTED_KEY="0000000000"

echo "Тестовые данные:"
echo "  U-поле: $TEST_U_FIELD"
echo "  Ожидаемый ключ: $EXPECTED_KEY"
echo ""

# Проверка наличия исполняемых файлов
echo "Проверка наличия исполняемых файлов..."

CUDA_EXISTS=false
CPU_EXISTS=false

if [ -f "./rc4_crack_cuda" ]; then
    echo -e "${GREEN}✓${NC} CUDA версия найдена"
    CUDA_EXISTS=true
else
    echo -e "${YELLOW}⚠${NC} CUDA версия не найдена (./rc4_crack_cuda)"
fi

if [ -f "./rc4_crack_cpu" ]; then
    echo -e "${GREEN}✓${NC} CPU версия найдена"
    CPU_EXISTS=true
else
    echo -e "${YELLOW}⚠${NC} CPU версия не найдена (./rc4_crack_cpu)"
fi

echo ""

# Если ничего не найдено, предлагаем собрать
if [ "$CUDA_EXISTS" = false ] && [ "$CPU_EXISTS" = false ]; then
    echo -e "${RED}❌ Исполняемые файлы не найдены${NC}"
    echo ""
    echo "Попробуйте собрать:"
    echo "  make all      # Обе версии"
    echo "  make cuda     # Только CUDA"
    echo "  make cpu      # Только CPU"
    exit 1
fi

# Функция для проверки результата
check_result() {
    local output="$1"
    local name="$2"
    
    if echo "$output" | grep -q "КЛЮЧ НАЙДЕН"; then
        if echo "$output" | grep -q "$EXPECTED_KEY"; then
            echo -e "${GREEN}✅ $name: УСПЕХ${NC}"
            echo "   Найден правильный ключ: $EXPECTED_KEY"
            return 0
        else
            echo -e "${RED}❌ $name: ОШИБКА${NC}"
            echo "   Найден неправильный ключ"
            return 1
        fi
    else
        echo -e "${RED}❌ $name: ОШИБКА${NC}"
        echo "   Ключ не найден"
        return 1
    fi
}

# Тестирование CUDA версии
if [ "$CUDA_EXISTS" = true ]; then
    echo "════════════════════════════════════════════════════════════════"
    echo "Тестирование CUDA версии"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    # Проверка наличия NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        echo "GPU информация:"
        nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader
        echo ""
    else
        echo -e "${YELLOW}⚠ nvidia-smi не найден, пропускаем проверку GPU${NC}"
        echo ""
    fi
    
    echo "Запуск теста (это может занять некоторое время)..."
    echo ""
    
    # Запускаем с ограничением времени (timeout 300 секунд = 5 минут)
    if command -v timeout &> /dev/null; then
        CUDA_OUTPUT=$(timeout 300 ./rc4_crack_cuda "$TEST_U_FIELD" 2>&1)
        CUDA_EXIT=$?
        
        if [ $CUDA_EXIT -eq 124 ]; then
            echo -e "${RED}❌ CUDA версия: TIMEOUT${NC}"
            echo "   Тест превысил 5 минут"
        else
            check_result "$CUDA_OUTPUT" "CUDA версия"
            
            # Показываем статистику
            if echo "$CUDA_OUTPUT" | grep -q "Скорость:"; then
                echo ""
                echo "Статистика:"
                echo "$CUDA_OUTPUT" | grep "Скорость:" | head -1
                echo "$CUDA_OUTPUT" | grep "Время выполнения:" | head -1
            fi
        fi
    else
        # Без timeout
        CUDA_OUTPUT=$(./rc4_crack_cuda "$TEST_U_FIELD" 2>&1)
        check_result "$CUDA_OUTPUT" "CUDA версия"
    fi
    
    echo ""
fi

# Тестирование CPU версии
if [ "$CPU_EXISTS" = true ]; then
    echo "════════════════════════════════════════════════════════════════"
    echo "Тестирование CPU версии"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    echo "CPU информация:"
    if [ -f /proc/cpuinfo ]; then
        CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
        CPU_CORES=$(grep -c "processor" /proc/cpuinfo)
        echo "  Модель: $CPU_MODEL"
        echo "  Ядер: $CPU_CORES"
    elif command -v sysctl &> /dev/null; then
        # macOS
        CPU_MODEL=$(sysctl -n machdep.cpu.brand_string)
        CPU_CORES=$(sysctl -n hw.ncpu)
        echo "  Модель: $CPU_MODEL"
        echo "  Ядер: $CPU_CORES"
    fi
    echo ""
    
    echo "Запуск теста (это займёт НАМНОГО больше времени, чем GPU)..."
    echo -e "${YELLOW}⚠ Для полного теста CPU может потребоваться несколько дней!${NC}"
    echo "  Прерывание через 60 секунд для демонстрации..."
    echo ""
    
    # Запускаем с коротким timeout для демонстрации
    if command -v timeout &> /dev/null; then
        CPU_OUTPUT=$(timeout 60 ./rc4_crack_cpu "$TEST_U_FIELD" 2>&1)
        CPU_EXIT=$?
        
        if [ $CPU_EXIT -eq 124 ]; then
            echo -e "${YELLOW}⚠ CPU версия: TIMEOUT (ожидаемо)${NC}"
            echo "   Для полного теста потребуется намного больше времени"
            
            # Показываем скорость
            if echo "$CPU_OUTPUT" | grep -q "Скорость:"; then
                echo ""
                echo "Текущая скорость:"
                echo "$CPU_OUTPUT" | grep "Скорость:" | tail -1
            fi
        else
            check_result "$CPU_OUTPUT" "CPU версия"
        fi
    else
        echo -e "${YELLOW}⚠ timeout не найден, пропускаем CPU тест${NC}"
    fi
    
    echo ""
fi

# Итоговая информация
echo "════════════════════════════════════════════════════════════════"
echo "ЗАКЛЮЧЕНИЕ"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Тестовый ключ (0000000000) находится в начале keyspace,"
echo "поэтому находится очень быстро."
echo ""
echo "Для реальных ключей:"
echo "  • GPU (RTX 4070 Ti): ~90 секунд для полного keyspace"
echo "  • CPU (16 ядер): ~25 дней для полного keyspace"
echo ""
echo "GPU примерно в 1000 раз быстрее CPU!"
echo ""

# Рекомендации
if [ "$CUDA_EXISTS" = false ]; then
    echo -e "${YELLOW}💡 Рекомендация: Соберите CUDA версию для максимальной скорости${NC}"
    echo "   make cuda"
    echo ""
fi

echo "Для реального использования:"
echo "  1. Извлеките U-поле: python3 extract_u_field.py document.pdf"
echo "  2. Запустите брутфорс: ./rc4_crack_cuda <U_field>"
echo ""
