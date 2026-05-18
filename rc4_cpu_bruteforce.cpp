/*
 * RC4 40-bit Key Brute Force - CPU Multi-threaded Version
 * Оптимизированная версия для систем без GPU
 * 
 * Компиляция: g++ -O3 -march=native -pthread rc4_cpu_bruteforce.cpp -o rc4_crack_cpu
 * Использование: ./rc4_crack_cpu <U_field_hex> [num_threads]
 */

#include <iostream>
#include <iomanip>
#include <thread>
#include <atomic>
#include <vector>
#include <cstring>
#include <chrono>
#include <sstream>

#define KEY_LENGTH 5
#define STATE_SIZE 256
#define U_FIELD_SIZE 32

// Padding string из PDF спецификации
const uint8_t PADDING[32] = {
    0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41,
    0x64, 0x00, 0x4E, 0x56, 0xFF, 0xFA, 0x01, 0x08,
    0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
    0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A
};

// Глобальные переменные для результата
std::atomic<bool> g_found(false);
uint8_t g_found_key[KEY_LENGTH] = {0};
std::atomic<uint64_t> g_checked_keys(0);

/*
 * RC4 KSA - оптимизированная версия
 */
inline void rc4_ksa(const uint8_t* key, uint8_t* S) {
    // Инициализация
    for (int i = 0; i < STATE_SIZE; i++) {
        S[i] = i;
    }
    
    // Перемешивание
    uint8_t j = 0;
    for (int i = 0; i < STATE_SIZE; i++) {
        j = j + S[i] + key[i % KEY_LENGTH];
        
        // Swap
        uint8_t temp = S[i];
        S[i] = S[j];
        S[j] = temp;
    }
}

/*
 * RC4 расшифрование (inline для максимальной скорости)
 */
inline void rc4_decrypt(const uint8_t* key, const uint8_t* input, 
                       uint8_t* output, int length) {
    uint8_t S[STATE_SIZE];
    
    // KSA
    rc4_ksa(key, S);
    
    // PRGA + XOR
    uint8_t i = 0, j = 0;
    for (int k = 0; k < length; k++) {
        i = i + 1;
        j = j + S[i];
        
        // Swap
        uint8_t temp = S[i];
        S[i] = S[j];
        S[j] = temp;
        
        // XOR
        output[k] = input[k] ^ S[(S[i] + S[j]) & 0xFF];
    }
}

/*
 * Быстрая проверка ключа
 */
inline bool verify_key_fast(const uint8_t* key, const uint8_t* u_field) {
    uint8_t decrypted[U_FIELD_SIZE];
    
    // Расшифровываем
    rc4_decrypt(key, u_field, decrypted, U_FIELD_SIZE);
    
    // Быстрая проверка первых 4 байт
    if (*(uint32_t*)decrypted != *(uint32_t*)PADDING) {
        return false;
    }
    
    // Полная проверка
    return memcmp(decrypted, PADDING, U_FIELD_SIZE) == 0;
}

/*
 * Рабочая функция для потока
 */
void worker_thread(uint64_t start_key, uint64_t end_key, 
                   const uint8_t* u_field, int thread_id) {
    uint8_t key[KEY_LENGTH];
    uint64_t local_checked = 0;
    
    for (uint64_t key_value = start_key; key_value < end_key && !g_found; key_value++) {
        // Формируем ключ (little-endian)
        key[0] = (key_value >> 0) & 0xFF;
        key[1] = (key_value >> 8) & 0xFF;
        key[2] = (key_value >> 16) & 0xFF;
        key[3] = (key_value >> 24) & 0xFF;
        key[4] = (key_value >> 32) & 0xFF;
        
        // Проверяем
        if (verify_key_fast(key, u_field)) {
            // Нашли!
            bool expected = false;
            if (g_found.compare_exchange_strong(expected, true)) {
                // Мы первые
                memcpy(g_found_key, key, KEY_LENGTH);
            }
            return;
        }
        
        local_checked++;
        
        // Обновляем счётчик каждые 100K ключей
        if (local_checked % 100000 == 0) {
            g_checked_keys += 100000;
            local_checked = 0;
        }
    }
    
    // Обновляем оставшиеся
    if (local_checked > 0) {
        g_checked_keys += local_checked;
    }
}

/*
 * Парсинг hex строки
 */
bool hex_to_bytes(const std::string& hex, uint8_t* bytes, int length) {
    if (hex.length() != length * 2) {
        return false;
    }
    
    for (int i = 0; i < length; i++) {
        std::string byte_str = hex.substr(i * 2, 2);
        bytes[i] = (uint8_t)strtol(byte_str.c_str(), nullptr, 16);
    }
    
    return true;
}

/*
 * Форматирование времени
 */
std::string format_time(double seconds) {
    if (seconds < 60) {
        return std::to_string((int)seconds) + " сек";
    } else if (seconds < 3600) {
        return std::to_string((int)(seconds / 60)) + " мин " + 
               std::to_string((int)seconds % 60) + " сек";
    } else {
        int hours = (int)(seconds / 3600);
        int mins = (int)((seconds - hours * 3600) / 60);
        return std::to_string(hours) + " ч " + std::to_string(mins) + " мин";
    }
}

/*
 * Поток для отображения прогресса
 */
void progress_thread(uint64_t total_keys, 
                    std::chrono::steady_clock::time_point start_time) {
    while (!g_found) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        uint64_t checked = g_checked_keys.load();
        auto now = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(now - start_time).count();
        
        if (elapsed > 0) {
            double percent = (double)checked / total_keys * 100.0;
            double speed = checked / elapsed / 1e6;  // Мегаключей в секунду
            double eta = (total_keys - checked) / (checked / elapsed);
            
            std::cout << "\r[" << std::fixed << std::setprecision(2) << percent 
                      << "%] Проверено: " << checked << " / " << total_keys 
                      << " | Скорость: " << std::setprecision(2) << speed 
                      << " MK/s | Осталось: " << format_time(eta) << "     ";
            std::cout.flush();
        }
    }
}

int main(int argc, char** argv) {
    std::cout << "╔════════════════════════════════════════════════════════════════╗\n";
    std::cout << "║  RC4 40-bit Brute Force - CPU Multi-threaded                  ║\n";
    std::cout << "╚════════════════════════════════════════════════════════════════╝\n\n";
    
    // Проверка аргументов
    if (argc < 2) {
        std::cout << "Использование: " << argv[0] << " <U_field_hex> [num_threads]\n";
        std::cout << "Пример: " << argv[0] 
                  << " 1e7be03f4c9e8c6a2d5f1b3a7e9c4d2f8a6b5c3e1f0d9e8a7b6c5d4e3f2a1b\n";
        return 1;
    }
    
    // Парсинг U-поля
    uint8_t u_field[U_FIELD_SIZE];
    if (!hex_to_bytes(argv[1], u_field, U_FIELD_SIZE)) {
        std::cerr << "Ошибка: U-поле должно быть " << U_FIELD_SIZE * 2 
                  << " hex символов (" << U_FIELD_SIZE << " байт)\n";
        return 1;
    }
    
    std::cout << "U-поле: ";
    for (int i = 0; i < U_FIELD_SIZE; i++) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') 
                  << (int)u_field[i];
    }
    std::cout << std::dec << "\n\n";
    
    // Количество потоков
    int num_threads = std::thread::hardware_concurrency();
    if (argc >= 3) {
        num_threads = atoi(argv[2]);
    }
    
    std::cout << "CPU: " << num_threads << " потоков\n\n";
    
    // Параметры
    const uint64_t total_keys = (1ULL << 40);  // 2^40
    const uint64_t keys_per_thread = total_keys / num_threads;
    
    std::cout << "Параметры брутфорса:\n";
    std::cout << "  Пространство ключей: 2^40 = " << total_keys 
              << " (" << std::fixed << std::setprecision(2) 
              << total_keys / 1e12 << " триллионов)\n";
    std::cout << "  Потоков: " << num_threads << "\n";
    std::cout << "  Ключей на поток: " << keys_per_thread << "\n\n";
    
    std::cout << "Начинаем брутфорс...\n\n";
    
    // Запуск
    auto start_time = std::chrono::steady_clock::now();
    
    // Создаём рабочие потоки
    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; i++) {
        uint64_t start_key = i * keys_per_thread;
        uint64_t end_key = (i == num_threads - 1) ? total_keys : (i + 1) * keys_per_thread;
        
        threads.emplace_back(worker_thread, start_key, end_key, u_field, i);
    }
    
    // Поток прогресса
    std::thread progress(progress_thread, total_keys, start_time);
    
    // Ждём завершения
    for (auto& t : threads) {
        t.join();
    }
    
    g_found = true;  // Останавливаем поток прогресса
    progress.join();
    
    auto end_time = std::chrono::steady_clock::now();
    double elapsed = std::chrono::duration<double>(end_time - start_time).count();
    
    std::cout << "\n\n";
    
    // Результат
    if (g_found && g_found_key[0] != 0) {
        std::cout << "╔════════════════════════════════════════════════════════════════╗\n";
        std::cout << "║  ✅ КЛЮЧ НАЙДЕН!                                              ║\n";
        std::cout << "╚════════════════════════════════════════════════════════════════╝\n\n";
        
        std::cout << "Ключ (hex): ";
        for (int i = 0; i < KEY_LENGTH; i++) {
            std::cout << std::hex << std::setw(2) << std::setfill('0') 
                      << (int)g_found_key[i];
        }
        std::cout << std::dec << "\n";
        
        uint64_t key_value = 0;
        for (int i = 0; i < KEY_LENGTH; i++) {
            key_value |= ((uint64_t)g_found_key[i]) << (i * 8);
        }
        std::cout << "Ключ (dec): " << key_value << "\n";
        
        // Проверка
        uint8_t decrypted[U_FIELD_SIZE];
        rc4_decrypt(g_found_key, u_field, decrypted, U_FIELD_SIZE);
        
        std::cout << "\nРасшифрованное U-поле: ";
        for (int i = 0; i < U_FIELD_SIZE; i++) {
            std::cout << std::hex << std::setw(2) << std::setfill('0') 
                      << (int)decrypted[i];
        }
        std::cout << std::dec << "\n";
    } else {
        std::cout << "❌ Ключ не найден\n";
    }
    
    uint64_t checked = g_checked_keys.load();
    std::cout << "\nСтатистика:\n";
    std::cout << "  Время выполнения: " << format_time(elapsed) << "\n";
    std::cout << "  Проверено ключей: " << checked << "\n";
    std::cout << "  Скорость: " << std::fixed << std::setprecision(2) 
              << checked / elapsed / 1e6 << " MK/s (мегаключей в секунду)\n";
    
    return g_found ? 0 : 1;
}
