import unittest
import os
from CodeProcessor import CodeProcessor
import Config
from Utils import is_code_syntax_valid

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

    def test_task_generation(self):
        task = self.processor.generate_task(topic_id=1)
        self.assertIn("loop", task["description"].lower())
        self.assertIn("task", task)
        self.assertIn("reference_code", task)

    def test_code_processing_gaps(self):
        result = self.processor.process_code("def foo():\n    return 42", "gaps", {"gap_symbol": "___"})
        self.assertTrue(is_code_syntax_valid(result["modified_code"]))
        self.assertTrue(os.path.exists(result["original_path"]))
        self.assertTrue(os.path.exists(result["modified_path"]))
        self.assertTrue("GeneratedCode" in result["original_path"])
        self.assertTrue("Result" in result["modified_path"])

    def test_code_processing_noise(self):
        result = self.processor.process_code("def bar(x):\n    return x * 2", "noise", {"noise_count": 2})
        self.assertTrue(is_code_syntax_valid(result["modified_code"]))
        self.assertTrue("GeneratedCode" in result["original_path"])
        self.assertTrue("Result" in result["modified_path"])

    def test_directory_creation(self):
        self.assertTrue(os.path.exists("Examples/GeneratedCode"))
        self.assertTrue(os.path.exists("Result"))

if __name__ == "__main__":
    unittest.main()