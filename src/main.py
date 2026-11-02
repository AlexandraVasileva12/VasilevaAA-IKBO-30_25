"""Программа для визуализации графа зависимостей."""

import argparse
import os
import string
import sys

MIN_DEPTH = 1
MAX_DEPTH = 100


def error(message):
    """Вывести сообщение об ошибке и завершить программу."""
    print("Ошибка:", message)
    sys.exit(1)


def check_package(package, test_mode):
    """Проверить имя пакета."""
    if package.strip() == "":
        error("имя пакета не может быть пустым")
    if test_mode:
        for letter in package:
            if letter not in string.ascii_uppercase:
                error("в тестовом режиме имя пакета - большие "
                      "латинские буквы, например A")
    elif ":" not in package:
        error("имя пакета Maven пишется так: группа:название:версия")


def check_repo(repo, test_mode):
    """Проверить URL репозитория или путь к файлу."""
    if test_mode:
        if not os.path.isfile(repo):
            error("файл тестового репозитория не найден: " + repo)
    elif not repo.startswith(("http://", "https://")):
        error("URL должен начинаться с http:// или https://")


def check_depth(depth):
    """Проверить максимальную глубину."""
    if depth < MIN_DEPTH or depth > MAX_DEPTH:
        error(f"глубина должна быть от {MIN_DEPTH} до {MAX_DEPTH}")


def check_filter(text):
    """Проверить подстроку для фильтрации."""
    if text != "" and text.strip() == "":
        error("фильтр не может состоять только из пробелов")


parser = argparse.ArgumentParser(description="Граф зависимостей")

parser.add_argument("--package", required=True,
                    help="имя анализируемого пакета")
parser.add_argument("--repo", required=True,
                    help="URL репозитория или путь к тестовому файлу")
parser.add_argument("--test-mode", action="store_true",
                    help="режим работы с тестовым репозиторием")
parser.add_argument("--max-depth", type=int, default=3,
                    help="максимальная глубина анализа")
parser.add_argument("--filter", default="",
                    help="подстрока для фильтрации пакетов")

args = parser.parse_args()

check_package(args.package, args.test_mode)
check_repo(args.repo, args.test_mode)
check_depth(args.max_depth)
check_filter(args.filter)

for key, value in vars(args).items():
    print(f"{key} = {value}")