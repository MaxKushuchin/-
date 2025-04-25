# CodeProcessor.py
import os
import random
import ast
from typing import Dict, Any, List, Optional
from Utils import load_text_from_file
from Logger import logger
from Utils import is_code_syntax_valid
import re




class CodeProcessor:
    def __init__(self, folder_id: str, auth: str, model: str = "yandexgpt-lite",
                 model_version: str = "rc", temperature: float = 0.3):
        self.folder_id = folder_id
        self.auth = auth
        self.model = model
        self.model_version = model_version
        self.temperature = temperature
        self.topics = self._load_topics()
        self._ensure_files_exist()
        self._configure_ml()

    def _configure_ml(self):
        """Настройка подключения к Yandex ML"""
        try:
            from yandex_cloud_ml_sdk import YCloudML
            self.sdk = YCloudML(folder_id=self.folder_id, auth=self.auth)
            self.ml_model = self.sdk.models.completions(
                self.model,
                model_version=self.model_version
            ).configure(temperature=self.temperature)
            logger.info("Yandex ML configured successfully")
        except Exception as e:
            logger.error(f"Yandex ML configuration failed: {e}")
            raise

    def _load_topics(self) -> Dict[int, Dict[str, Any]]:
        """Полная загрузка всех тем из файлов"""
        topics = {}
        for i in range(1, 10):
            filename = f"{i}_{self._get_topic_name(i)}.txt"
            try:
                # Указываем правильный путь к файлам тем
                content = load_text_from_file(os.path.join("Topics", filename))
                topic_data = self._parse_topic_content(content)
                topics[i] = {
                    "id": i,
                    "name": self._get_topic_name(i),
                    "filename": filename,
                    **topic_data
                }
            except Exception as e:
                logger.error(f"Error loading topic {i}: {e}")
                topics[i] = self._create_default_topic(i)
        return topics

    def _parse_topic_content(self, content: str) -> Dict[str, Any]:
        """Полный парсинг содержимого файла темы."""
        sections = {}
        current_section = None

        for line in content.split('\n'):
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                sections[current_section] = []
            elif current_section and line.strip():
                sections[current_section].append(line)

        processed = {
            "description": '\n'.join(sections.get("Тема", [])),
            "requirements": '\n'.join(sections.get("Требования", [])),
            "easy_task": '\n'.join(sections.get("Уровень сложности: Легкий", [])),
            "medium_task": '\n'.join(sections.get("Уровень сложности: Средний", [])),
            "hard_task": '\n'.join(sections.get("Уровень сложности: Сложный", [])),
            "example_code": '\n'.join(sections.get("Пример решения", [])),
            "criteria": self._parse_criteria('\n'.join(sections.get("Критерии оценки", [])))
        }

        return processed

    def _parse_criteria(self, criteria_text: str) -> Dict[str, float]:
        """Parses evaluation criteria from text."""
        criteria = {}
        for line in criteria_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split('(')
            if len(parts) != 2:
                logger.warning(f"Invalid criteria format: {line}")
                continue

            criterion_name = parts[0].strip()
            weight_str = parts[1].replace('%)', '').strip()

            try:
                weight = float(weight_str) / 100  # Convert percentage to fraction
                criteria[criterion_name] = weight
            except ValueError:
                logger.warning(f"Invalid weight format: {line}")

        return criteria

    def _create_default_topic(self, topic_id: int) -> Dict[str, Any]:
        """Создание темы по умолчанию при ошибке загрузки"""
        return {
            "id": topic_id,
            "name": self._get_topic_name(topic_id),
            "filename": f"{topic_id}_default.txt",
            "description": f"Default topic {topic_id}",
            "requirements": "",
            "easy_task": f"Basic task for topic {topic_id}",
            "medium_task": f"Medium task for topic {topic_id}",
            "hard_task": f"Hard task for topic {topic_id}",
            "example_code": f"# Example code for topic {topic_id}",
            "criteria": {
                "Correctness": 0.5,
                "Completeness": 0.3,
                "Style": 0.2
            }
        }

    def _get_topic_name(self, topic_id: int) -> str:
        """Получение названия темы по ID"""
        names = {
            1: "Loops",
            2: "Conditions",
            3: "Functions",
            4: "Strings",
            5: "Collections",
            6: "Files",
            7: "OOP",
            8: "Exceptions",
            9: "Decorators"
        }
        return names.get(topic_id, "Unknown")

    def _ensure_files_exist(self):
        """Создание необходимых файлов и папок"""
        os.makedirs("Topics", exist_ok=True)
        os.makedirs("Examples/GeneratedCode", exist_ok=True)
        os.makedirs("Result", exist_ok=True)

        if not os.path.exists('file.txt'):
            with open('file.txt', 'w') as f:
                f.write("Пример содержимого файла\nСтрока 1\nСтрока 2\nОшибка: тест\nСтрока 4")

    def generate_task(self, topic_id: int = None, difficulty: str = "medium") -> Dict[str, Any]:
        """Полная генерация задачи с выбором темы и сложности"""
        if topic_id is None:
            topic_id = random.randint(1, 9)
        elif topic_id not in self.topics:
            raise ValueError(f"Invalid topic ID: {topic_id}")

        topic = self.topics[topic_id]
        task_map = {
            "easy": ("Легкий", topic["easy_task"]),
            "medium": ("Средний", topic["medium_task"]),
            "hard": ("Сложный", topic["hard_task"])
        }

        difficulty_level, task = task_map.get(difficulty, ("Средний", topic["medium_task"]))

        return {
            "task_id": topic_id,
            "topic": topic["name"],
            "difficulty": difficulty,
            "difficulty_level": difficulty_level,
            "description": topic["description"],
            "requirements": topic["requirements"],
            "task": task,
            "reference_code": topic["example_code"],
            "criteria": topic["criteria"]
        }

    def process_code(self, code: str, task_type: str = "gaps", task_params: Optional[Dict] = None) -> Dict[str, Any]:
        """Полная обработка кода с проверкой синтаксиса."""
        if task_params is None:
            task_params = {}

        # Проверка синтаксиса
        if not is_code_syntax_valid(code):
            return {
                "status": "error",
                "message": "Syntax error in code",
                "original_code": code,
                "modified_code": "",
                "hints": {}
            }

        # Продолжение обработки
        try:
            if task_type == "gaps":
                processed_code = self._create_gaps(code, task_params)
            elif task_type == "noise":
                processed_code = self._add_noise(code, task_params)
            else:
                processed_code = code

            # Сохранение и возврат результата
            original_path = self._save_code_file(code, "original")
            modified_path = self._save_code_file(processed_code, "modified")

            return {
                "status": "success",
                "original_code": code,
                "modified_code": processed_code,
                "original_path": original_path,
                "modified_path": modified_path
            }
        except Exception as e:
            logger.error(f"Error processing code: {e}")
            return {
                "status": "error",
                "message": str(e),
                "original_code": code,
                "modified_code": "",
                "hints": {}
            }

    def _create_gaps(self, code: str, params: Dict) -> str:
        """Создание пропусков в коде"""
        gap_symbol = params.get("gap_symbol", "___")
        lines = code.split('\n')
        gap_lines = []

        for i, line in enumerate(lines):
            if i % 3 == 0 and "=" in line:  # Каждая 3-я строка с присваиванием
                parts = line.split('=')
                if len(parts) == 2:
                    gap_lines.append(f"{parts[0].strip()} = {gap_symbol}")
                else:
                    gap_lines.append(line)
            elif "def " in line:  # Пропуски в функциях
                gap_lines.append(line.replace(":", f" {gap_symbol}"))
            else:
                gap_lines.append(line)

        return '\n'.join(gap_lines)


    def _add_noise(self, code: str, params: Dict) -> str:
        """Добавление шума в код"""
        lines = code.split('\n')
        noise_lines = []
        noise_count = params.get("noise_count", 3)

        for line in lines:
            noise_lines.append(line)
            if "def " in line and noise_count > 0:
                noise_lines.append("    # TODO: Implement this function")
                noise_count -= 1

        return '\n'.join(noise_lines)

    def _save_code_file(self, code: str, prefix: str) -> str:
        """Сохранение кода в файл с правильными путями"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if prefix == "original":
            # Для исходного кода - папка GeneratedCode
            os.makedirs("Examples/GeneratedCode", exist_ok=True)
            filename = f"{prefix}_{timestamp}.py"
            filepath = os.path.join("Examples", "GeneratedCode", filename)
        else:
            # Для модифицированного кода - папка Result
            os.makedirs("Result", exist_ok=True)
            filename = f"{prefix}_{timestamp}.py"
            filepath = os.path.join("Result", filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        return filepath

    def generate_hints(self, code: str, solution: str = None) -> Dict[str, str]:
        """Генерация трехуровневых подсказок"""
        hints = {
            "hint_1": "🔍 Проверьте синтаксис основных конструкций",
            "hint_2": "🤔 Проанализируйте логику программы",
            "hint_3": "💡 Ключевые моменты решения:"
        }

        if solution:
            # Анализ решения для более точных подсказок
            if "def " not in code and "def " in solution:
                hints["hint_2"] = "🤔 В решении должны быть функции"

            if "class " not in code and "class " in solution:
                hints["hint_2"] = "🤔 В решении должны быть классы"

            # Добавляем часть решения в 3-ю подсказку
            lines = solution.split('\n')
            hints["hint_3"] += "\n" + '\n'.join(lines[:min(5, len(lines))])

        return hints

    def analyze_solution(self, user_code: str, task_info: Dict) -> Dict[str, Any]:
        """Анализ решения пользователя"""
        if not task_info or "reference_code" not in task_info:
            return {
                "status": "error",
                "message": "Invalid task information"
            }

        try:
            # Проверка синтаксиса
            ast.parse(user_code)

            # Подготовка данных для анализа
            reference_code = task_info["reference_code"]
            criteria = task_info.get("criteria", {})

            # Базовый анализ
            score = 0
            feedback = []

            if "def " in reference_code and "def " in user_code:
                score += criteria.get("function_implementation", 0.3) * 100
                feedback.append("✅ Функции реализованы")
            elif "def " in reference_code:
                feedback.append("🔴 Отсутствуют требуемые функции")

            if "class " in reference_code and "class " in user_code:
                score += criteria.get("class_implementation", 0.2) * 100
                feedback.append("✅ Классы реализованы")
            elif "class " in reference_code:
                feedback.append("🔴 Отсутствуют требуемые классы")

            # Проверка соответствия основным требованиям
            requirements = task_info.get("requirements", "").split('\n')
            for req in requirements:
                if req.strip() and req.strip() in user_code:
                    score += criteria.get("requirements_met", 0.2) * 100 / len(requirements)
                    feedback.append(f"✅ Требование выполнено: {req}")

            # Ограничение оценки 100%
            score = min(100, score)

            return {
                "status": "success",
                "score": round(score),
                "feedback": '\n'.join(feedback),
                "detailed_criteria": criteria
            }

        except SyntaxError as e:
            return {
                "status": "error",
                "message": str(e),
                "score": 0,
                "feedback": f"Синтаксическая ошибка: {str(e)}"
            }