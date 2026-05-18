/*
 * RC4 40-bit Key Brute Force with CUDA
 * Оптимизированная версия для взлома PDF Revision 2
 * 
 * Компиляция: nvcc -O3 -arch=sm_86 rc4_cuda_bruteforce.cu -o rc4_crack
 * Использование: ./rc4_crack <U_field_hex>
 * 
 * Для RTX 4070 Ti используйте -arch=sm_89
 */

#include <cuda_runtime.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

// Константы
#define KEY_LENGTH 5
#define STATE_SIZE 256
#define U_FIELD_SIZE 32  // Размер U-поля в байтах

// Структура для результата
typedef struct {
    uint8_t key[KEY_LENGTH];
    int found;
} Result;

// Известный паттерн для проверки (padding string из PDF спецификации)
__constant__ uint8_t d_padding[32] = {
    0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41,
    0x64, 0x00, 0x4E, 0x56, 0xFF, 0xFA, 0x01, 0x08,
    0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
    0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A
};

// U-поле из PDF (будет загружено в constant memory)
__constant__ uint8_t d_u_field[U_FIELD_SIZE];

/*
 * RC4 KSA (Key Scheduling Algorithm) - оптимизированная версия
 */
__device__ void rc4_ksa(const uint8_t* key, uint8_t* S) {
    // Инициализация
    #pragma unroll
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
 * RC4 PRGA (Pseudo-Random Generation Algorithm) - генерация keystream
 */
__device__ void rc4_prga(uint8_t* S, uint8_t* output, int length) {
    uint8_t i = 0;
    uint8_t j = 0;
    
    for (int k = 0; k < length; k++) {
        i = i + 1;
        j = j + S[i];
        
        // Swap
        uint8_t temp = S[i];
        S[i] = S[j];
        S[j] = temp;
        
        // Генерация байта
        output[k] = S[(S[i] + S[j]) & 0xFF];
    }
}

/*
 * RC4 шифрование/расшифрование
 */
__device__ void rc4_crypt(const uint8_t* key, const uint8_t* input, 
                          uint8_t* output, int length) {
    uint8_t S[STATE_SIZE];
    uint8_t keystream[U_FIELD_SIZE];
    
    // KSA
    rc4_ksa(key, S);
    
    // PRGA
    rc4_prga(S, keystream, length);
    
    // XOR
    #pragma unroll 8
    for (int i = 0; i < length; i++) {
        output[i] = input[i] ^ keystream[i];
    }
}

/*
 * Проверка ключа против U-поля
 * Возвращает количество совпадающих байт с padding
 */
__device__ int verify_key(const uint8_t* key) {
    uint8_t decrypted[U_FIELD_SIZE];
    
    // Расшифровываем U-поле
    rc4_crypt(key, d_u_field, decrypted, U_FIELD_SIZE);
    
    // Проверяем совпадение с padding
    int matches = 0;
    #pragma unroll
    for (int i = 0; i < U_FIELD_SIZE; i++) {
        if (decrypted[i] == d_padding[i]) {
            matches++;
        }
    }
    
    return matches;
}

/*
 * CUDA kernel для брутфорса
 * Каждый thread проверяет один ключ
 */
__global__ void bruteforce_kernel(uint64_t start_key, uint64_t keys_per_thread,
                                  Result* result) {
    // Глобальный индекс треда
    uint64_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    uint64_t key_value = start_key + tid * keys_per_thread;
    
    // Проверяем, не вышли ли за пределы
    uint64_t max_key = (1ULL << 40);
    if (key_value >= max_key) return;
    
    // Локальный ключ
    uint8_t key[KEY_LENGTH];
    
    // Перебираем ключи для этого треда
    for (uint64_t i = 0; i < keys_per_thread && (key_value + i) < max_key; i++) {
        uint64_t current_key = key_value + i;
        
        // Преобразуем число в 5-байтовый ключ (little-endian)
        key[0] = (current_key >> 0) & 0xFF;
        key[1] = (current_key >> 8) & 0xFF;
        key[2] = (current_key >> 16) & 0xFF;
        key[3] = (current_key >> 24) & 0xFF;
        key[4] = (current_key >> 32) & 0xFF;
        
        // Проверяем ключ
        int matches = verify_key(key);
        
        // Если нашли полное совпадение
        if (matches == U_FIELD_SIZE) {
            // Атомарная проверка и запись результата
            int old = atomicCAS(&result->found, 0, 1);
            if (old == 0) {
                // Мы первые, кто нашёл ключ
                for (int j = 0; j < KEY_LENGTH; j++) {
                    result->key[j] = key[j];
                }
            }
            return;
        }
        
        // Частичное совпадение (для отладки, можно убрать для скорости)
        // if (matches >= 28) {
        //     printf("Partial match (%d/32): %02X%02X%02X%02X%02X\n",
        //            matches, key[0], key[1], key[2], key[3], key[4]);
        // }
    }
}

/*
 * Оптимизированный kernel с shared memory
 */
__global__ void bruteforce_kernel_optimized(uint64_t start_key, 
                                           uint64_t keys_per_thread,
                                           Result* result) {
    // Shared memory для U-поля (уже в constant memory, но можно кэшировать)
    __shared__ uint8_t s_u_field[U_FIELD_SIZE];
    
    // Загружаем U-поле в shared memory (один раз на блок)
    if (threadIdx.x < U_FIELD_SIZE) {
        s_u_field[threadIdx.x] = d_u_field[threadIdx.x];
    }
    __syncthreads();
    
    uint64_t tid = blockIdx.x * blockDim.x + threadIdx.x;
    uint64_t key_value = start_key + tid * keys_per_thread;
    uint64_t max_key = (1ULL << 40);
    
    if (key_value >= max_key) return;
    
    uint8_t key[KEY_LENGTH];
    uint8_t S[STATE_SIZE];
    uint8_t decrypted[U_FIELD_SIZE];
    
    for (uint64_t i = 0; i < keys_per_thread && (key_value + i) < max_key; i++) {
        uint64_t current_key = key_value + i;
        
        // Формируем ключ
        key[0] = (current_key >> 0) & 0xFF;
        key[1] = (current_key >> 8) & 0xFF;
        key[2] = (current_key >> 16) & 0xFF;
        key[3] = (current_key >> 24) & 0xFF;
        key[4] = (current_key >> 32) & 0xFF;
        
        // Inline RC4 для максимальной скорости
        // KSA
        #pragma unroll 256
        for (int j = 0; j < STATE_SIZE; j++) {
            S[j] = j;
        }
        
        uint8_t j = 0;
        for (int k = 0; k < STATE_SIZE; k++) {
            j = j + S[k] + key[k % KEY_LENGTH];
            uint8_t temp = S[k];
            S[k] = S[j];
            S[j] = temp;
        }
        
        // PRGA + XOR
        uint8_t pi = 0, pj = 0;
        #pragma unroll 8
        for (int k = 0; k < U_FIELD_SIZE; k++) {
            pi = pi + 1;
            pj = pj + S[pi];
            uint8_t temp = S[pi];
            S[pi] = S[pj];
            S[pj] = temp;
            decrypted[k] = s_u_field[k] ^ S[(S[pi] + S[pj]) & 0xFF];
        }
        
        // Быстрая проверка первых байт
        if (decrypted[0] == d_padding[0] && 
            decrypted[1] == d_padding[1] &&
            decrypted[2] == d_padding[2] &&
            decrypted[3] == d_padding[3]) {
            
            // Полная проверка
            int matches = 0;
            #pragma unroll
            for (int k = 0; k < U_FIELD_SIZE; k++) {
                if (decrypted[k] == d_padding[k]) matches++;
            }
            
            if (matches == U_FIELD_SIZE) {
                int old = atomicCAS(&result->found, 0, 1);
                if (old == 0) {
                    for (int j = 0; j < KEY_LENGTH; j++) {
                        result->key[j] = key[j];
                    }
                }
                return;
            }
        }
    }
}

/*
 * Парсинг hex строки в байты
 */
void hex_to_bytes(const char* hex, uint8_t* bytes, int length) {
    for (int i = 0; i < length; i++) {
        sscanf(hex + 2*i, "%2hhx", &bytes[i]);
    }
}

/*
 * Вывод прогресса
 */
void print_progress(uint64_t checked, uint64_t total, double elapsed) {
    double percent = (double)checked / total * 100.0;
    double speed = checked / elapsed / 1e9;  // Гигаключей в секунду
    double eta = (total - checked) / (checked / elapsed);
    
    printf("\r[%.2f%%] Проверено: %llu / %llu | Скорость: %.2f GK/s | "
           "Осталось: %.0f сек   ",
           percent, checked, total, speed, eta);
    fflush(stdout);
}

int main(int argc, char** argv) {
    printf("╔════════════════════════════════════════════════════════════════╗\n");
    printf("║  RC4 40-bit Brute Force - CUDA Accelerated                    ║\n");
    printf("║  Оптимизировано для RTX 4070 Ti                               ║\n");
    printf("╚════════════════════════════════════════════════════════════════╝\n\n");
    
    // Проверка аргументов
    if (argc < 2) {
        printf("Использование: %s <U_field_hex>\n", argv[0]);
        printf("Пример: %s 1e7be03f4c9e8c6a2d5f1b3a7e9c4d2f8a6b5c3e1f0d9e8a7b6c5d4e3f2a1b\n", 
               argv[0]);
        return 1;
    }
    
    // Парсинг U-поля
    uint8_t h_u_field[U_FIELD_SIZE];
    if (strlen(argv[1]) != U_FIELD_SIZE * 2) {
        printf("Ошибка: U-поле должно быть %d hex символов (%d байт)\n", 
               U_FIELD_SIZE * 2, U_FIELD_SIZE);
        return 1;
    }
    hex_to_bytes(argv[1], h_u_field, U_FIELD_SIZE);
    
    printf("U-поле: ");
    for (int i = 0; i < U_FIELD_SIZE; i++) {
        printf("%02X", h_u_field[i]);
    }
    printf("\n\n");
    
    // Информация о GPU
    int device;
    cudaGetDevice(&device);
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, device);
    
    printf("GPU: %s\n", prop.name);
    printf("Compute Capability: %d.%d\n", prop.major, prop.minor);
    printf("Multiprocessors: %d\n", prop.multiProcessorCount);
    printf("CUDA Cores: ~%d\n", prop.multiProcessorCount * 128);  // Примерно для Ampere/Ada
    printf("Global Memory: %.2f GB\n\n", prop.totalGlobalMem / 1e9);
    
    // Копируем U-поле в constant memory
    cudaMemcpyToSymbol(d_u_field, h_u_field, U_FIELD_SIZE);
    
    // Выделяем память для результата
    Result* d_result;
    Result h_result = {0};
    cudaMalloc(&d_result, sizeof(Result));
    cudaMemcpy(d_result, &h_result, sizeof(Result), cudaMemcpyHostToDevice);
    
    // Параметры запуска
    const int threads_per_block = 256;
    const int blocks = prop.multiProcessorCount * 8;  // 8 блоков на SM
    const uint64_t total_threads = (uint64_t)blocks * threads_per_block;
    const uint64_t total_keys = (1ULL << 40);  // 2^40
    const uint64_t keys_per_thread = (total_keys + total_threads - 1) / total_threads;
    
    printf("Параметры брутфорса:\n");
    printf("  Пространство ключей: 2^40 = %llu (%.2f триллионов)\n", 
           total_keys, total_keys / 1e12);
    printf("  Блоков: %d\n", blocks);
    printf("  Тредов на блок: %d\n", threads_per_block);
    printf("  Всего тредов: %llu\n", total_threads);
    printf("  Ключей на тред: %llu\n\n", keys_per_thread);
    
    printf("Начинаем брутфорс...\n\n");
    
    // Запуск
    clock_t start = clock();
    cudaEvent_t start_event, stop_event;
    cudaEventCreate(&start_event);
    cudaEventCreate(&stop_event);
    cudaEventRecord(start_event);
    
    // Разбиваем на батчи для отображения прогресса
    const int num_batches = 100;
    const uint64_t keys_per_batch = total_keys / num_batches;
    
    for (int batch = 0; batch < num_batches; batch++) {
        uint64_t start_key = batch * keys_per_batch;
        
        // Запускаем kernel
        bruteforce_kernel_optimized<<<blocks, threads_per_block>>>(
            start_key, keys_per_thread / num_batches, d_result
        );
        
        // Проверяем результат после каждого батча
        cudaMemcpy(&h_result, d_result, sizeof(Result), cudaMemcpyDeviceToHost);
        
        if (h_result.found) {
            printf("\n\n");
            break;
        }
        
        // Прогресс
        double elapsed = (double)(clock() - start) / CLOCKS_PER_SEC;
        print_progress((batch + 1) * keys_per_batch, total_keys, elapsed);
    }
    
    cudaEventRecord(stop_event);
    cudaEventSynchronize(stop_event);
    
    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start_event, stop_event);
    double elapsed = milliseconds / 1000.0;
    
    printf("\n\n");
    
    // Результат
    cudaMemcpy(&h_result, d_result, sizeof(Result), cudaMemcpyDeviceToHost);
    
    if (h_result.found) {
        printf("╔════════════════════════════════════════════════════════════════╗\n");
        printf("║  ✅ КЛЮЧ НАЙДЕН!                                              ║\n");
        printf("╚════════════════════════════════════════════════════════════════╝\n\n");
        
        printf("Ключ (hex): ");
        for (int i = 0; i < KEY_LENGTH; i++) {
            printf("%02X", h_result.key[i]);
        }
        printf("\n");
        
        printf("Ключ (dec): ");
        uint64_t key_value = 0;
        for (int i = 0; i < KEY_LENGTH; i++) {
            key_value |= ((uint64_t)h_result.key[i]) << (i * 8);
        }
        printf("%llu\n", key_value);
        
        // Проверка
        uint8_t S[STATE_SIZE];
        uint8_t decrypted[U_FIELD_SIZE];
        
        // CPU проверка
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
    
    printf("\nСтатистика:\n");
    printf("  Время выполнения: %.2f секунд\n", elapsed);
    printf("  Проверено ключей: %llu\n", total_keys);
    printf("  Скорость: %.2f GK/s (гигаключей в секунду)\n", 
           total_keys / elapsed / 1e9);
    printf("  Скорость: %.2f MK/s (мегаключей в секунду)\n", 
           total_keys / elapsed / 1e6);
    
    // Очистка
    cudaFree(d_result);
    cudaEventDestroy(start_event);
    cudaEventDestroy(stop_event);
    
    return h_result.found ? 0 : 1;
}
