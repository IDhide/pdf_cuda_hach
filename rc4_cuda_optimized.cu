/*
 * RC4 40-bit CUDA Brute Force - МАКСИМАЛЬНО ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
 * 
 * Исправления:
 * 1. Убраны батчи с cudaMemcpy (было 100 синхронизаций!)
 * 2. Один запуск kernel на весь keyspace
 * 3. Atomic flag для раннего выхода
 * 4. Оптимизация под RTX 4070 Ti
 * 
 * Компиляция: nvcc -O3 -arch=sm_89 --use_fast_math -Xptxas -O3 rc4_cuda_optimized.cu -o rc4_crack
 */

#include <cuda_runtime.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define KEY_LENGTH 5
#define STATE_SIZE 256
#define U_FIELD_SIZE 32

// Результат
typedef struct {
    uint8_t key[KEY_LENGTH];
    uint64_t key_value;
    int found;
} Result;

// Padding string (constant memory)
__constant__ uint8_t d_padding[32] = {
    0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41,
    0x64, 0x00, 0x4E, 0x56, 0xFF, 0xFA, 0x01, 0x08,
    0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
    0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A
};

// U-поле (constant memory)
__constant__ uint8_t d_u_field[U_FIELD_SIZE];

// Atomic flag для раннего выхода
__device__ int d_found_flag = 0;

/*
 * ОПТИМИЗИРОВАННЫЙ KERNEL - БЕЗ БАТЧЕЙ
 * Каждый thread проверяет свой диапазон ключей
 */
__global__ void bruteforce_kernel_ultra_fast(uint64_t total_keys, Result* result) {
    // Глобальный индекс треда
    uint64_t tid = (uint64_t)blockIdx.x * blockDim.x + threadIdx.x;
    uint64_t total_threads = (uint64_t)gridDim.x * blockDim.x;
    
    // Локальные переменные
    uint8_t key[KEY_LENGTH];
    uint8_t S[STATE_SIZE];
    uint8_t decrypted[U_FIELD_SIZE];
    
    // Перебираем ключи с шагом total_threads
    for (uint64_t key_value = tid; key_value < total_keys; key_value += total_threads) {
        
        // Ранний выход если ключ уже найден
        if (d_found_flag) return;
        
        // Формируем ключ (little-endian)
        key[0] = (key_value >> 0) & 0xFF;
        key[1] = (key_value >> 8) & 0xFF;
        key[2] = (key_value >> 16) & 0xFF;
        key[3] = (key_value >> 24) & 0xFF;
        key[4] = (key_value >> 32) & 0xFF;
        
        // ===== INLINE RC4 для максимальной скорости =====
        
        // KSA - инициализация
        #pragma unroll 256
        for (int i = 0; i < STATE_SIZE; i++) {
            S[i] = i;
        }
        
        // KSA - перемешивание
        uint8_t j = 0;
        for (int i = 0; i < STATE_SIZE; i++) {
            j = j + S[i] + key[i % KEY_LENGTH];
            uint8_t temp = S[i];
            S[i] = S[j];
            S[j] = temp;
        }
        
        // PRGA + XOR (объединено для скорости)
        uint8_t pi = 0, pj = 0;
        #pragma unroll 8
        for (int i = 0; i < U_FIELD_SIZE; i++) {
            pi = pi + 1;
            pj = pj + S[pi];
            uint8_t temp = S[pi];
            S[pi] = S[pj];
            S[pj] = temp;
            decrypted[i] = d_u_field[i] ^ S[(S[pi] + S[pj]) & 0xFF];
        }
        
        // ===== БЫСТРАЯ ПРОВЕРКА =====
        
        // Сначала проверяем первые 4 байта (быстро)
        if (*(uint32_t*)decrypted != *(uint32_t*)d_padding) {
            continue;
        }
        
        // Полная проверка
        bool match = true;
        #pragma unroll
        for (int i = 4; i < U_FIELD_SIZE; i++) {
            if (decrypted[i] != d_padding[i]) {
                match = false;
                break;
            }
        }
        
        if (match) {
            // НАШЛИ КЛЮЧ!
            int old = atomicExch(&d_found_flag, 1);
            if (old == 0) {
                // Мы первые
                result->key_value = key_value;
                for (int i = 0; i < KEY_LENGTH; i++) {
                    result->key[i] = key[i];
                }
                result->found = 1;
            }
            return;
        }
    }
}

/*
 * Парсинг hex строки
 */
void hex_to_bytes(const char* hex, uint8_t* bytes, int length) {
    for (int i = 0; i < length; i++) {
        sscanf(hex + 2*i, "%2hhx", &bytes[i]);
    }
}

int main(int argc, char** argv) {
    printf("╔════════════════════════════════════════════════════════════════╗\n");
    printf("║  RC4 40-bit CUDA Brute Force - ULTRA OPTIMIZED                ║\n");
    printf("║  Без батчей, максимальная скорость                            ║\n");
    printf("╚════════════════════════════════════════════════════════════════╝\n\n");
    
    if (argc < 2) {
        printf("Использование: %s <U_field_hex>\n", argv[0]);
        printf("\nДля вашего PDF:\n");
        printf("  %s 1e7be03f31514ab677026017c847ada400000000000000000000000000000000\n", argv[0]);
        return 1;
    }
    
    // Парсинг U-поля
    uint8_t h_u_field[U_FIELD_SIZE];
    if (strlen(argv[1]) != U_FIELD_SIZE * 2) {
        printf("❌ U-поле должно быть %d hex символов (%d байт)\n", 
               U_FIELD_SIZE * 2, U_FIELD_SIZE);
        return 1;
    }
    hex_to_bytes(argv[1], h_u_field, U_FIELD_SIZE);
    
    printf("U-поле: ");
    for (int i = 0; i < U_FIELD_SIZE; i++) {
        printf("%02X", h_u_field[i]);
    }
    printf("\n\n");
    
    // GPU информация
    int device;
    cudaGetDevice(&device);
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, device);
    
    printf("GPU: %s\n", prop.name);
    printf("Compute Capability: %d.%d\n", prop.major, prop.minor);
    printf("Multiprocessors: %d\n", prop.multiProcessorCount);
    printf("Max Threads per SM: %d\n", prop.maxThreadsPerMultiProcessor);
    printf("Global Memory: %.2f GB\n\n", prop.totalGlobalMem / 1e9);
    
    // Копируем U-поле в constant memory
    cudaMemcpyToSymbol(d_u_field, h_u_field, U_FIELD_SIZE);
    
    // Выделяем память для результата
    Result* d_result;
    Result h_result = {0};
    cudaMalloc(&d_result, sizeof(Result));
    cudaMemcpy(d_result, &h_result, sizeof(Result), cudaMemcpyHostToDevice);
    
    // ===== ОПТИМАЛЬНЫЕ ПАРАМЕТРЫ ДЛЯ RTX 4070 Ti =====
    const int threads_per_block = 256;  // Оптимально для большинства GPU
    const int blocks = prop.multiProcessorCount * 16;  // 16 блоков на SM для максимальной загрузки
    const uint64_t total_threads = (uint64_t)blocks * threads_per_block;
    const uint64_t total_keys = (1ULL << 40);
    
    printf("Параметры запуска:\n");
    printf("  Пространство ключей: 2^40 = %llu (%.2f триллионов)\n", 
           total_keys, total_keys / 1e12);
    printf("  Блоков: %d\n", blocks);
    printf("  Тредов на блок: %d\n", threads_per_block);
    printf("  Всего тредов: %llu\n", total_threads);
    printf("  Ключей на тред: ~%llu\n\n", total_keys / total_threads);
    
    printf("🚀 Запуск брутфорса (БЕЗ БАТЧЕЙ - один запуск)...\n\n");
    
    // Засекаем время
    cudaEvent_t start_event, stop_event;
    cudaEventCreate(&start_event);
    cudaEventCreate(&stop_event);
    
    cudaEventRecord(start_event);
    
    // ===== ОДИН ЗАПУСК KERNEL НА ВЕСЬ KEYSPACE =====
    bruteforce_kernel_ultra_fast<<<blocks, threads_per_block>>>(total_keys, d_result);
    
    cudaEventRecord(stop_event);
    cudaEventSynchronize(stop_event);
    
    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start_event, stop_event);
    double elapsed = milliseconds / 1000.0;
    
    // Получаем результат
    cudaMemcpy(&h_result, d_result, sizeof(Result), cudaMemcpyDeviceToHost);
    
    printf("\n");
    
    if (h_result.found) {
        printf("╔════════════════════════════════════════════════════════════════╗\n");
        printf("║  ✅ КЛЮЧ НАЙДЕН!                                              ║\n");
        printf("╚════════════════════════════════════════════════════════════════╝\n\n");
        
        printf("Ключ (hex): ");
        for (int i = 0; i < KEY_LENGTH; i++) {
            printf("%02X", h_result.key[i]);
        }
        printf("\n");
        
        printf("Ключ (dec): %llu\n", h_result.key_value);
        
        // Проверка на CPU
        uint8_t S[STATE_SIZE];
        uint8_t decrypted[U_FIELD_SIZE];
        
        for (int i = 0; i < STATE_SIZE; i++) S[i] = i;
        uint8_t j = 0;
        for (int i = 0; i < STATE_SIZE; i++) {
            j = j + S[i] + h_result.key[i % KEY_LENGTH];
            uint8_t temp = S[i];
            S[i] = S[j];
            S[j] = temp;
        }
        
        uint8_t pi = 0, pj = 0;
        for (int i = 0; i < U_FIELD_SIZE; i++) {
            pi = pi + 1;
            pj = pj + S[pi];
            uint8_t temp = S[pi];
            S[pi] = S[pj];
            S[pj] = temp;
            decrypted[i] = h_u_field[i] ^ S[(S[pi] + S[pj]) & 0xFF];
        }
        
        printf("\nРасшифрованное U-поле: ");
        for (int i = 0; i < U_FIELD_SIZE; i++) {
            printf("%02X", decrypted[i]);
        }
        printf("\n");
    } else {
        printf("❌ Ключ не найден\n");
    }
    
    printf("\n═══════════════════════════════════════════════════════════════\n");
    printf("СТАТИСТИКА\n");
    printf("═══════════════════════════════════════════════════════════════\n\n");
    
    printf("Время выполнения: %.2f секунд\n", elapsed);
    printf("Проверено ключей: %llu\n", total_keys);
    printf("Скорость: %.2f GK/s (гигаключей в секунду)\n", 
           total_keys / elapsed / 1e9);
    printf("Скорость: %.2f MK/s (мегаключей в секунду)\n", 
           total_keys / elapsed / 1e6);
    
    // Сравнение с ожидаемой скоростью
    double expected_speed_gks = 12.0;  // GK/s для RTX 4070 Ti
    double actual_speed_gks = total_keys / elapsed / 1e9;
    double efficiency = (actual_speed_gks / expected_speed_gks) * 100.0;
    
    printf("\nЭффективность: %.1f%% от ожидаемой (%.1f GK/s)\n", 
           efficiency, expected_speed_gks);
    
    if (efficiency < 80.0) {
        printf("\n⚠️  Производительность ниже ожидаемой!\n");
        printf("Возможные причины:\n");
        printf("  • GPU перегревается (проверьте nvidia-smi)\n");
        printf("  • Power limit ограничен\n");
        printf("  • Другие процессы используют GPU\n");
        printf("  • Неоптимальная архитектура (-arch=sm_XX)\n");
    } else if (efficiency >= 100.0) {
        printf("\n🎉 Отличная производительность!\n");
    }
    
    // Очистка
    cudaFree(d_result);
    cudaEventDestroy(start_event);
    cudaEventDestroy(stop_event);
    
    return h_result.found ? 0 : 1;
}
