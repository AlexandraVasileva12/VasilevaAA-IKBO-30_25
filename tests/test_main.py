"""Тесты визуализатора графа зависимостей."""

import argparse
import contextlib
import io
import os
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(TESTS_DIR, "..", "src"))

import main  # noqa: E402

POM = """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <dependencies>
    <dependency>
      <groupId>com.squareup.okio</groupId>
      <artifactId>okio</artifactId>
      <version>3.6.0</version>
    </dependency>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>"""


def build_graph(file_name, package="A", max_depth=10, filter_text=""):
    """Построить граф по тестовому файлу из папки tests."""
    args = argparse.Namespace(
        repo=os.path.join(TESTS_DIR, file_name), test_mode=True,
        max_depth=max_depth, filter=filter_text)
    graph = {}
    with contextlib.redirect_stdout(io.StringIO()):
        main.dfs(package, args, graph, 0, [])
    return graph


class MavenTest(unittest.TestCase):
    """Работа с форматом пакетов Maven."""

    def test_pom_url(self):
        """Адрес POM-файла собирается из имени пакета."""
        url = main.get_pom_url("https://repo1.maven.org/maven2/",
                               "org.slf4j:slf4j-api:2.0.9")
        self.assertEqual(
            url, "https://repo1.maven.org/maven2/org/slf4j/slf4j-api/"
                 "2.0.9/slf4j-api-2.0.9.pom")

    def test_dependencies_without_test_scope(self):
        """Из POM берутся зависимости, кроме тестовых."""
        self.assertEqual(main.get_dependencies(POM),
                         ["com.squareup.okio:okio:3.6.0"])


class GraphTest(unittest.TestCase):
    """Построение графа алгоритмом DFS."""

    def test_simple_graph(self):
        """Общая зависимость D обходится один раз."""
        self.assertEqual(build_graph("test_repo.txt"),
                         {"A": ["B", "C"], "B": ["D"], "D": [],
                          "C": ["D"]})

    def test_max_depth(self):
        """Обход останавливается на заданной глубине."""
        self.assertEqual(build_graph("deep.txt", max_depth=2),
                         {"A": ["B"], "B": ["C"]})

    def test_filter(self):
        """Пакеты с подстрокой фильтра не попадают в граф."""
        graph = build_graph("big.txt", filter_text="C")
        self.assertNotIn("C", graph)
        self.assertNotIn("F", graph)
        self.assertEqual(graph["A"], ["B", "D"])

    def test_cycle(self):
        """Цикл находится, и программа не зацикливается."""
        args = argparse.Namespace(
            repo=os.path.join(TESTS_DIR, "cycle.txt"), test_mode=True,
            max_depth=10, filter="")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main.dfs("A", args, {}, 0, [])
        self.assertIn("Найден цикл: A -> B -> C -> A", output.getvalue())

    def test_unknown_package(self):
        """У пакета, которого нет в файле, нет зависимостей."""
        self.assertEqual(build_graph("big.txt", package="Z"), {"Z": []})


class MermaidTest(unittest.TestCase):
    """Вывод графа на языке Mermaid."""

    def test_mermaid_text(self):
        """Граф превращается в текст Mermaid."""
        text = main.to_mermaid({"A": ["B"], "B": []})
        self.assertEqual(text, 'graph TD\n    A["A"]\n    B["B"]\n'
                               '    A --> B')

    def test_node_id(self):
        """Из имени узла убираются недопустимые символы."""
        self.assertEqual(main.node_id("org.a:b-c:1.0"), "org_a_b_c_1_0")


class ErrorTest(unittest.TestCase):
    """Обработка ошибок в параметрах."""

    def assert_error(self, function, *arguments):
        """Проверить, что функция завершает программу с ошибкой."""
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                function(*arguments)

    def test_bad_package(self):
        """Имя пакета Maven без версии - ошибка."""
        self.assert_error(main.check_package, "org.slf4j:slf4j-api", False)

    def test_bad_test_package(self):
        """В тестовом режиме имя только из больших букв."""
        self.assert_error(main.check_package, "a1", True)

    def test_bad_url(self):
        """URL должен начинаться с http:// или https://."""
        self.assert_error(main.check_repo, "ftp://x", False)

    def test_missing_file(self):
        """Файл тестового репозитория должен существовать."""
        self.assert_error(main.check_repo, "nofile.txt", True)

    def test_bad_depth(self):
        """Глубина 0 - ошибка."""
        self.assert_error(main.check_depth, 0)

    def test_bad_filter(self):
        """Фильтр из одних пробелов - ошибка."""
        self.assert_error(main.check_filter, "   ")

    def test_bad_test_file(self):
        """Строка без двоеточия в тестовом файле - ошибка."""
        self.assert_error(main.read_test_repo,
                          os.path.join(TESTS_DIR, "bad.txt"))


if __name__ == "__main__":
    unittest.main()
