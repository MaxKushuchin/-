from CodeProcessor import CodeProcessor
from SolutionAnalyzer import SolutionAnalyzer
import Config
import os

def ensure_directories():
    """Создание необходимых директорий"""
    os.makedirs("Examples/GeneratedCode", exist_ok=True)
    os.makedirs("Result", exist_ok=True)
    os.makedirs("Topics", exist_ok=True)

def print_task_info(task):
    """Вывод информации о задаче"""
    print("\n" + "=" * 50)
    print(f"Тема: {task['topic']}")
    print(f"Сложность: {task['difficulty_level']}")
    print("\nЗадание:")
    print(task['task'])
    print("\nПример решения:")
    print(task['reference_code'])
    print("=" * 50 + "\n")

def main():
    ensure_directories()
    processor = CodeProcessor(Config.YAGPT_CONFIG['folder_id'], Config.YAGPT_CONFIG['auth'])
    analyzer = SolutionAnalyzer()

    # Выбор темы и сложности
    topic_id = 2  # Пример: тема "Collections"
    difficulty = "hard"  # Уровень сложности

    # Тест генерации задачи
    print("1. Тест генерации задачи:")
    task = processor.generate_task(topic_id=topic_id, difficulty=difficulty)
    print_task_info(task)

    # Используем референсный код задачи для тестов
    test_code = task['reference_code']

    # Тест обработки кода (gaps)
    print("2. Тест создания пропусков в коде:")
    processed = processor.process_code(test_code, "gaps", {"gap_symbol": "___"})
    print("Исходный код:")
    print(test_code)
    print("\nКод с пропусками:")
    print(processed['modified_code'])

    # Тест обработки кода (noise)
    print("\n3. Тест добавления шума в код:")
    processed = processor.process_code(test_code, "noise", {"noise_count": 2})
    print("Исходный код:")
    print(test_code)
    print("\nКод с шумом:")
    print(processed['modified_code'])

    # Тест анализа решения
    print("\n4. Тест анализа решения:")
    analysis = analyzer.analyze(test_code, task['reference_code'], task['criteria'])
    print(f"Оценка: {analysis['score']}/100")
    print("Фидбэк:")
    print(analysis['feedback'])

if __name__ == "__main__":
    main()
