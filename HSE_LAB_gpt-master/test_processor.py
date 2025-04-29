import unittest
import os
from CodeProcessor import CodeProcessor
import Config
from Utils import is_code_syntax_valid
import ast


class TestCodeProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = CodeProcessor(Config.YAGPT_CONFIG['folder_id'], Config.YAGPT_CONFIG['auth'])
        # Очистка папок перед тестами
        self._clear_directory("Examples/GeneratedCode")
        self._clear_directory("Result")

    def _clear_directory(self, path):
        if os.path.exists(path):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    def test_random_topic_generation(self):
        """Тест генерации случайной темы"""
        random_topic = self.processor.get_random_topic()
        self.assertIn(random_topic['topic_id'], range(1, 10))
        self.assertIn(random_topic['difficulty'], ['easy', 'medium', 'hard'])

        # Проверяем, что тема корректно загружается
        task = self.processor.generate_task(
            topic_id=random_topic['topic_id'],
            difficulty=random_topic['difficulty']
        )
        self.assertEqual(task['task_id'], random_topic['topic_id'])
        self.assertEqual(task['difficulty'], random_topic['difficulty'])

    def test_task_generation_all_topics(self):
        """Тест генерации задач для всех тем"""
        for topic_id in range(1, 10):
            for difficulty in ['easy', 'medium', 'hard']:
                task = self.processor.generate_task(topic_id=topic_id, difficulty=difficulty)
                self.assertEqual(task['task_id'], topic_id)
                self.assertEqual(task['difficulty'], difficulty)
                self.assertIn("task", task)
                self.assertIn("reference_code", task)

    def test_advanced_gaps_processing(self):
        """Тест улучшенной логики пропусков"""
        test_code = """
def calculate_sum(a, b):
    if a > 0 and b > 0:
        return a + b
    return 0

class Calculator:
    def multiply(self, x, y):
        return x * y
"""
        # Тестируем разные варианты пропусков
        for gap_symbol in ["___", "???", "GAP"]:
            result = self.processor.process_code(
                test_code,
                "gaps",
                {"gap_symbol": gap_symbol}
            )
            self.assertTrue(is_code_syntax_valid(result["modified_code"]))
            self.assertIn(gap_symbol, result["modified_code"])

            # Проверяем, что пропуски добавлены в ключевых местах
            modified_code = result["modified_code"]
            self.assertTrue(
                f"def calculate_sum({gap_symbol}" in modified_code or
                f"if {gap_symbol}" in modified_code or
                f"return {gap_symbol}" in modified_code or
                f"def multiply(self, {gap_symbol}" in modified_code
            )

    def test_hints_generation(self):
        """Тест генерации трехуровневых подсказок"""
        test_code = "def foo():\n    return 42"
        solution_code = """
class Solution:
    def calculate(self, x):
        return x * 2

def process_data(data):
    if not data:
        raise ValueError("No data")
    return [item.upper() for item in data]
"""
        hints = self.processor.generate_hints(test_code, solution_code)

        # Проверяем наличие всех уровней подсказок
        self.assertEqual(len(hints), 3)
        self.assertIn("hint_1", hints)
        self.assertIn("hint_2", hints)
        self.assertIn("hint_3", hints)

        # Проверяем, что подсказки учитывают решение
        self.assertIn("классы", hints["hint_2"])
        self.assertIn("функции", hints["hint_2"])
        self.assertIn("calculate", hints["hint_3"])

        # Тест без решения
        basic_hints = self.processor.generate_hints(test_code)
        self.assertIn("🔍", basic_hints["hint_1"])
        self.assertIn("🤔", basic_hints["hint_2"])
        self.assertIn("💡", basic_hints["hint_3"])

    def test_solution_analysis(self):
        """Тест анализа решений"""
        task = self.processor.generate_task(topic_id=3, difficulty="medium")  # Functions topic
        analysis = self.processor.analyze_solution(
            task['reference_code'],
            task
        )

        # Проверяем базовую структуру ответа
        self.assertIn("score", analysis)
        self.assertIn("feedback", analysis)
        self.assertIn("detailed_feedback", analysis)

        # Для эталонного кода оценка должна быть высокой
        self.assertGreaterEqual(analysis['score'], 80)

        # Проверяем анализ изменений между попытками
        bad_code = "def wrong_function(): pass"
        analysis1 = self.processor.analyze_solution(bad_code, task)
        analysis2 = self.processor.analyze_solution(task['reference_code'], task)

        self.assertIn("Прогресс", '\n'.join(analysis2['feedback']))
        self.assertLess(analysis1['score'], analysis2['score'])

    def test_directory_creation(self):
        self.assertTrue(os.path.exists("Examples/GeneratedCode"))
        self.assertTrue(os.path.exists("Result"))


if __name__ == "__main__":
    unittest.main()
