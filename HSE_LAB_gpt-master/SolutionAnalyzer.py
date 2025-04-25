from typing import Dict, Any, List
import ast
from ast import parse, ClassDef, FunctionDef, Try, For, While, AST, If
from Logger import logger


class SolutionAnalyzer:
    def analyze(self, user_code: str, reference_code: str, criteria: Dict[str, float]) -> Dict[str, Any]:
        """
        Анализирует решение пользователя на основе эталонного кода и критериев оценки.
        Возвращает оценку и детализированный фидбэк.
        """
        score = 0
        feedback = []
        detailed_feedback = {}

        try:
            # Проверка синтаксиса
            ast.parse(user_code)

            # Базовые проверки структуры кода
            user_tree = ast.parse(user_code)
            ref_tree = ast.parse(reference_code) if reference_code else None

            # Проверка соответствия критериям
            for criterion, weight in criteria.items():
                criterion_score = 0
                criterion_feedback = []

                # Анализ в зависимости от типа критерия
                if "корректность" in criterion.lower():
                    criterion_score = self._check_correctness(user_code, reference_code)
                    criterion_feedback.append(f"Соответствие эталону: {criterion_score * 100:.0f}%")

                elif "оптимизация" in criterion.lower():
                    criterion_score = self._check_optimization(user_tree)
                    criterion_feedback.append(
                        "Код оптимален" if criterion_score > 0.7 else "Есть возможности для оптимизации")

                elif "читаемость" in criterion.lower():
                    criterion_score = self._check_readability(user_tree)
                    criterion_feedback.append(
                        "Хорошая читаемость" if criterion_score > 0.7 else "Нужны улучшения в читаемости")

                elif "ошибки" in criterion.lower() or "исключения" in criterion.lower():
                    criterion_score = self._check_error_handling(user_tree)
                    criterion_feedback.append(
                        "Есть обработка ошибок" if criterion_score > 0.5 else "Не хватает обработки ошибок")

                elif "функции" in criterion.lower():
                    criterion_score = self._check_functions(user_tree, ref_tree)
                    criterion_feedback.append(f"Реализовано функций: {criterion_score * 100:.0f}%")

                elif "классы" in criterion.lower():
                    criterion_score = self._check_classes(user_tree, ref_tree)
                    criterion_feedback.append(f"Реализовано классов: {criterion_score * 100:.0f}%")

                else:
                    criterion_score = self._general_check(user_code, criterion)
                    criterion_feedback.append("Критерий выполнен" if criterion_score > 0.5 else "Критерий не выполнен")

                # Добавление результатов по критерию
                score += criterion_score * weight
                feedback.append(
                    f"{criterion}: {criterion_score * 100:.0f}% - {'✅' if criterion_score >= 0.8 else '⚠️' if criterion_score >= 0.5 else '❌'}")

                detailed_feedback[criterion] = {
                    'score': round(criterion_score * 100),
                    'feedback': '\n'.join(criterion_feedback)
                }

        except SyntaxError as e:
            error_msg = f"❌ Синтаксическая ошибка: {e}"
            feedback.append(error_msg)
            detailed_feedback['Синтаксис'] = {
                'score': 0,
                'feedback': error_msg
            }
            return {
                "score": 0,
                "feedback": feedback,
                "detailed_feedback": detailed_feedback
            }

        # Добавляем общие рекомендации
        general_feedback = self._generate_general_feedback(user_code, score)
        feedback.extend(general_feedback)

        return {
            "score": round(score),
            "feedback": feedback,
            "detailed_feedback": detailed_feedback
        }

    def _generate_general_feedback(self, code: str, score: float) -> List[str]:
        """Генерирует общие рекомендации по коду"""
        feedback = []

        if score < 50:
            feedback.append("🔴 Требуется значительная доработка кода")
        elif score < 75:
            feedback.append("🟡 Код работает, но есть что улучшить")
        else:
            feedback.append("🟢 Хорошая работа! Код соответствует требованиям")

        # Проверка наличия комментариев
        if "#" not in code and '"""' not in code:
            feedback.append("ℹ️ Добавьте комментарии для улучшения читаемости")

        return feedback

    def _check_correctness(self, user_code: str, reference_code: str) -> float:
        """Проверка корректности реализации"""
        if not reference_code:
            return 0.5

        user_components = self._get_code_components(user_code)
        ref_components = self._get_code_components(reference_code)

        match_score = 0
        if user_components['functions'] == ref_components['functions']:
            match_score += 0.4
        if user_components['classes'] == ref_components['classes']:
            match_score += 0.3
        if user_components['loops'] == ref_components['loops']:
            match_score += 0.2
        if user_components['conditions'] == ref_components['conditions']:
            match_score += 0.1

        return min(1.0, match_score)

    def _check_optimization(self, tree: AST) -> float:
        """Проверка оптимизации кода"""
        has_nested_loops = any(
            isinstance(node, (For, While)) and
            any(isinstance(sub_node, (For, While)) for sub_node in ast.walk(node))
            for node in ast.walk(tree)
        )
        return 0.8 if not has_nested_loops else 0.3

    def _check_readability(self, tree: AST) -> float:
        """Проверка читаемости кода"""
        has_comments = any(
            isinstance(node, ast.Expr) and isinstance(node.value, ast.Str)
            for node in ast.walk(tree)
        )
        return 0.9 if has_comments else 0.5

    def _check_error_handling(self, tree: AST) -> float:
        """Проверка обработки ошибок"""
        has_error_handling = any(isinstance(node, Try) for node in ast.walk(tree))
        return 1.0 if has_error_handling else 0.2

    def _check_functions(self, user_tree: AST, ref_tree: AST) -> float:
        """Проверка реализации функций"""
        if not ref_tree:
            return 0.5

        user_funcs = [n.name for n in ast.walk(user_tree) if isinstance(n, FunctionDef)]
        ref_funcs = [n.name for n in ast.walk(ref_tree) if isinstance(n, FunctionDef)]

        if not ref_funcs:
            return 0.5

        implemented = sum(1 for func in ref_funcs if func in user_funcs)
        return implemented / len(ref_funcs)

    def _check_classes(self, user_tree: AST, ref_tree: AST) -> float:
        """Проверка реализации классов"""
        if not ref_tree:
            return 0.5

        user_classes = [n.name for n in ast.walk(user_tree) if isinstance(n, ClassDef)]
        ref_classes = [n.name for n in ast.walk(ref_tree) if isinstance(n, ClassDef)]

        if not ref_classes:
            return 0.5

        implemented = sum(1 for cls in ref_classes if cls in user_classes)
        return implemented / len(ref_classes)

    def _general_check(self, code: str, criterion: str) -> float:
        """Общая проверка для неизвестных критериев"""
        keywords = {
            'файловые операции': ['open(', 'with open(', 'read(', 'write('],
            'контекстные менеджеры': ['with '],
            'исключения': ['try:', 'except ', 'finally:']
        }

        for pattern, terms in keywords.items():
            if pattern in criterion.lower():
                return 0.8 if any(term in code for term in terms) else 0.2

        return 0.5

    def _get_code_components(self, code: str) -> Dict[str, List]:
        """Анализирует код и возвращает его основные компоненты"""
        tree = ast.parse(code)
        return {
            'functions': [n.name for n in ast.walk(tree) if isinstance(n, FunctionDef)],
            'classes': [n.name for n in ast.walk(tree) if isinstance(n, ClassDef)],
            'loops': [n.__class__.__name__ for n in ast.walk(tree) if isinstance(n, (For, While))],
            'conditions': [n.__class__.__name__ for n in ast.walk(tree) if isinstance(n, If)]
        }