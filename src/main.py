"""Программа для визуализации графа зависимостей."""

import argparse
import os
import re
import string
import sys
import urllib.error
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET

MIN_DEPTH = 1
MAX_DEPTH = 100
MAVEN_PARTS = 3
HTML_FILE = "graph.html"
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Граф зависимостей</title></head>
<body>
<pre class="mermaid">
{graph}
</pre>
<script type="module">
import mermaid from
  "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.esm.min.mjs";
mermaid.initialize({{ startOnLoad: true }});
</script>
</body>
</html>
"""


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
        print(f"Предупреждение: не удалось скачать {url} ({problem})")
        return None


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


def read_test_repo(path):
    """Прочитать тестовый репозиторий: строки вида 'A: B C'."""
    graph = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line == "":
                continue
            if ":" not in line:
                error(f"неверная строка в тестовом файле: {line}")
            name, dependencies = line.split(":", 1)
            graph[name.strip()] = dependencies.split()
    return graph


def load_dependencies(package, args):
    """Получить прямые зависимости пакета."""
    if args.test_mode:
        return read_test_repo(args.repo).get(package, [])
    if "?" in package or "$" in package:
        return []
    pom_text = download_pom(get_pom_url(args.repo, package))
    if pom_text is None:
        return []
    return get_dependencies(pom_text)


def apply_filter(dependencies, filter_text):
    """Убрать пакеты, имя которых содержит подстроку фильтра."""
    if filter_text == "":
        return dependencies
    result = []
    for dependency in dependencies:
        if filter_text not in dependency:
            result.append(dependency)
    return result


def dfs(package, args, graph, depth, path):
    """Обойти зависимости пакета в глубину (DFS) с рекурсией."""
    if package in path:
        print("Найден цикл:", " -> ".join(path + [package]))
        return
    if package in graph or depth >= args.max_depth:
        return
    dependencies = load_dependencies(package, args)
    dependencies = apply_filter(dependencies, args.filter)
    graph[package] = dependencies
    path.append(package)
    for dependency in dependencies:
        dfs(dependency, args, graph, depth + 1, path)
    path.pop()


def node_id(package):
    """Сделать имя узла для Mermaid: только буквы, цифры и _."""
    return re.sub(r"\W", "_", package)


def to_mermaid(graph):
    """Построить текст графа на языке Mermaid."""
    nodes = []
    for package, dependencies in graph.items():
        for name in [package] + dependencies:
            if name not in nodes:
                nodes.append(name)
    lines = ["graph TD"]
    for name in nodes:
        lines.append(f'    {node_id(name)}["{name}"]')
    for package, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"    {node_id(package)} --> {node_id(dependency)}")
    return "\n".join(lines)


def show_image(mermaid_text):
    """Сохранить граф в HTML-файл и открыть его в браузере."""
    with open(HTML_FILE, "w", encoding="utf-8") as file:
        file.write(HTML_TEMPLATE.format(graph=mermaid_text))
    print("Изображение графа сохранено в", HTML_FILE)
    webbrowser.open("file://" + os.path.abspath(HTML_FILE))


def build_parser():
    """Создать парсер параметров командной строки."""
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
    return parser


def main():
    """Запустить программу."""
    args = build_parser().parse_args()
    check_package(args.package, args.test_mode)
    check_repo(args.repo, args.test_mode)
    check_depth(args.max_depth)
    check_filter(args.filter)
    graph = {}
    dfs(args.package, args, graph, 0, [])
    mermaid_text = to_mermaid(graph)
    print(mermaid_text)
    show_image(mermaid_text)


if __name__ == "__main__":
    main()
