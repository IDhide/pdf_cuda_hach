# Makefile для RC4 Brute Force

# Компиляторы
NVCC = nvcc
CXX = g++

# Флаги компиляции
NVCC_FLAGS = -O3 --use_fast_math -Xptxas -O3
CXX_FLAGS = -O3 -march=native -pthread -std=c++11

# Архитектура GPU (измените под вашу карту)
# RTX 4070 Ti: sm_89
# RTX 3090: sm_86
# RTX 2080: sm_75
GPU_ARCH = sm_89

# Цели
all: cuda cpu

cuda: rc4_crack_cuda

cpu: rc4_crack_cpu

# CUDA версия
rc4_crack_cuda: rc4_cuda_bruteforce.cu
	$(NVCC) $(NVCC_FLAGS) -arch=$(GPU_ARCH) $< -o $@
	@echo "✅ CUDA версия собрана: ./rc4_crack_cuda"

# CPU версия
rc4_crack_cpu: rc4_cpu_bruteforce.cpp
	$(CXX) $(CXX_FLAGS) $< -o $@
	@echo "✅ CPU версия собрана: ./rc4_crack_cpu"

# Тест
test_cuda: rc4_crack_cuda
	@echo "Тестирование CUDA версии..."
	./rc4_crack_cuda 28BF4E5E4E758A416400004E56FFFFA0108002E2E00B6D0683E802F0CA9FE6453697A

test_cpu: rc4_crack_cpu
	@echo "Тестирование CPU версии..."
	./rc4_crack_cpu 28BF4E5E4E758A416400004E56FFFFA0108002E2E00B6D0683E802F0CA9FE6453697A

# Очистка
clean:
	rm -f rc4_crack_cuda rc4_crack_cpu

# Информация о GPU
gpu_info:
	@echo "Информация о GPU:"
	@nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make all       - Собрать обе версии (CUDA и CPU)"
	@echo "  make cuda      - Собрать только CUDA версию"
	@echo "  make cpu       - Собрать только CPU версию"
	@echo "  make test_cuda - Протестировать CUDA версию"
	@echo "  make test_cpu  - Протестировать CPU версию"
	@echo "  make gpu_info  - Показать информацию о GPU"
	@echo "  make clean     - Удалить скомпилированные файлы"
	@echo ""
	@echo "Для изменения архитектуры GPU:"
	@echo "  make cuda GPU_ARCH=sm_86  (для RTX 3090)"
	@echo "  make cuda GPU_ARCH=sm_89  (для RTX 4070 Ti)"

.PHONY: all cuda cpu test_cuda test_cpu clean gpu_info help
