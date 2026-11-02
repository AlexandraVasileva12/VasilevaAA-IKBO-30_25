"""Программа для визуализации графа зависимостей."""

import argparse
import os
import string
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

MIN_DEPTH = 1
MAX_DEPTH = 100
MAVEN_PARTS = 3


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
    elif len(package.split(":")) != MAVEN_PARTS:
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


def get_pom_url(repo, package):
    """Собрать адрес POM-файла пакета Maven."""
    group, artifact, version = package.split(":")
    group_path = group.replace(".", "/")
    return (f"{repo.rstrip('/')}/{group_path}/{artifact}/"
            f"{version}/{artifact}-{version}.pom")


def download_pom(url):
    """Скачать POM-файл и вернуть его текст."""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as problem:
        error(f"не удалось скачать {url} ({problem})")


def get_dependencies(pom_text):
    """Достать из POM-файла список прямых зависимостей."""
    pom_text = pom_text.replace(
        'xmlns="http://maven.apache.org/POM/4.0.0"', "")
    try:
        root = ET.fromstring(pom_text)
    except ET.ParseError:
        error("POM-файл повреждён, не удалось его прочитать")
    result = []
    for dep in root.findall("dependencies/dependency"):
        if dep.findtext("scope") == "test":
            continue
        group = dep.findtext("groupId")
        artifact = dep.findtext("artifactId")
        version = dep.findtext("version", "?")
        result.append(f"{group}:{artifact}:{version}")
    return result


def print_dependencies(package, dependencies):
    """Вывести прямые зависимости пакета по одной на строке."""
    if not dependencies:
        print(f"У пакета {package} нет прямых зависимостей")
        return
    print(f"Прямые зависимости пакета {package}:")
    for dependency in dependencies:
        print("  " + dependency)


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

if not args.test_mode:
    pom_text = download_pom(get_pom_url(args.repo, args.package))
    print_dependencies(args.package, get_dependencies(pom_text))