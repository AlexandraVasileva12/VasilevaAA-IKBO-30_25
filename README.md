# Визуализатор графа зависимостей (Maven)

Вариант 5. CLI-программа на Python для анализа и визуализации графа
зависимостей пакетов Maven. Готовые менеджеры пакетов и библиотеки
для получения зависимостей не используются.

## Этап 1. Параметры командной строки

| Опция | Описание |
|---|---|
| `--package` | имя анализируемого пакета (обязательно). Обычный режим: `группа:название:версия`, тестовый режим: большие латинские буквы (`A`) |
| `--repo` | URL репозитория или путь к файлу тестового репозитория (обязательно) |
| `--test-mode` | режим работы с тестовым репозиторием (флаг) |
| `--max-depth` | максимальная глубина анализа, от 1 до 100 (по умолчанию 3) |
| `--filter` | подстрока для фильтрации пакетов (по умолчанию пусто) |

На этапе 1 программа выводила все параметры в формате `ключ = значение`.
При неверных параметрах выводится сообщение об ошибке.

## Этап 2. Сбор данных

Пакеты задаются в формате Maven: `группа:название:версия`.
Программа:

1. собирает адрес POM-файла пакета:
   `репозиторий/группа(точки→слэши)/название/версия/название-версия.pom`;
2. скачивает его стандартным модулем `urllib.request`;
3. разбирает XML стандартным модулем `xml.etree.ElementTree` и берёт
   все `<dependency>` из раздела `<dependencies>` (зависимости со
   `<scope>test</scope>` пропускаются);
4. выводит прямые зависимости по одной на строке.

Менеджеры пакетов и сторонние библиотеки не используются.

Пример:

```
python src\main.py --package com.squareup.okhttp3:okhttp:4.12.0 --repo https://repo1.maven.org/maven2
Прямые зависимости пакета com.squareup.okhttp3:okhttp:4.12.0:
  com.squareup.okio:okio:3.6.0
  org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.21
```

Если пакет не найден, выводится ошибка:

```
python src\main.py --package com.squareup.okhttp3:okhttp:999 --repo https://repo1.maven.org/maven2
Ошибка: не удалось скачать ... (HTTP Error 404: Not Found)
```

## Запуск

```
run.bat --package org.slf4j:slf4j-api:2.0.9 --repo https://repo1.maven.org/maven2 --max-depth 2 --filter test
```

или

```
python src\main.py --package A --repo tests\test_repo.txt --test-mode
```

## Примеры ошибок

```
python src\main.py --package slf4j --repo https://x
Ошибка: имя пакета Maven пишется так: группа:название:версия

python src\main.py --package a:b --repo ftp://x
Ошибка: URL должен начинаться с http:// или https://

python src\main.py --package A --repo nofile.txt --test-mode
Ошибка: файл тестового репозитория не найден: nofile.txt

python src\main.py --package a:b --repo http://x --max-depth 0
Ошибка: глубина должна быть от 1 до 100
```
