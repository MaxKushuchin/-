# Utils.py
import os
import sys
import json
import ast
import re
from pathlib import Path
from typing import Optional, Dict, Any
from Logger import logger


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Ограничение значения диапазоном"""
    return max(min_value, min(value, max_value))


def load_text_from_file(filename: str, folder: str = "") -> str:
    """Загрузка текста из файла с сохранением отступов."""
    path = os.path.join(folder, filename) if folder else filename
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading file {filename}: {e}")
        raise




def get_resource_path(filename: str) -> Optional[str]:
    """Получение полного пути к ресурсу"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)

    full_path = os.path.join(base_path, filename)
    if not os.path.exists(full_path):
        logger.warning(f"File not found: {full_path}")
        return None
    return full_path


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Загрузка JSON из файла"""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON {filepath}: {e}")
        return {}


def save_json(data: Any, output_folder: str = "result",
              output_name: str = "result", output_postfix: str = "json") -> str:
    """Сохранение данных в JSON файл"""
    os.makedirs(output_folder, exist_ok=True)
    file_name = f"{output_name}.{output_postfix}"
    file_path = os.path.join(output_folder, file_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info(f"Data saved to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")
        raise


def save_text_as_txt(text: str, output_folder: str = "result",
                     output_name: str = "result") -> str:
    """Сохранение текста в файл"""
    os.makedirs(output_folder, exist_ok=True)
    file_name = f"{output_name}.txt"
    file_path = os.path.join(output_folder, file_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)
        logger.info(f"Text saved to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving text: {e}")
        raise


def is_code_syntax_valid(code: str) -> bool:
    """Проверка синтаксиса кода"""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logger.warning(f"Syntax error: {e}")
        return False


def SH(s: str, placeholder: str = "***", percent: float = 0.20) -> str:
    """Сокращение строки с сохранением начала и конца"""
    if not s:
        return s

    length = len(s)
    visible_length = max(1, int(length * percent))
    return f"{s[:visible_length]}{placeholder}{s[-visible_length:]}"


def count_tokens(messages: list[Dict]) -> int:
    """Подсчет токенов в сообщениях"""
    return sum(len(str(msg.get("content", ""))) for msg in messages)


def calculate_cost_for_combined_messages(messages: list[Dict],
                                         cost_per_1000: float) -> str:
    """Расчет стоимости обработки сообщений"""
    tokens = count_tokens(messages)
    cost = (tokens / 1000) * cost_per_1000
    return f"Tokens: {tokens}, Cost: ${cost:.4f}"