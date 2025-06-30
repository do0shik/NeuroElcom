import json
import ast
import re


def fix_json_string(s):
    # Исправляем пропущенные кавычки в id
    s = re.sub(r"'id': (\d+\.\d+\.\d+\.\d+\.\d+)", r"'id': '\1'", s)
    # Убираем кавычки вокруг цен, чтобы все были числами
    s = re.sub(r"'price': '(\d+)'", r"'price': \1", s)
    return s


# Прочитаем построчно и объединим в одну строку
with open('example/test_data.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    raw_content = ''.join(lines)

try:
    # Исправляем проблемы в данных перед парсингом
    fixed_content = fix_json_string(raw_content)

    # Преобразуем из Python-подобного текста в объект Python
    parsed_data = ast.literal_eval(fixed_content)

    # Сохраняем в валидный JSON
    with open('test_data_clean.json', 'w', encoding='utf-8') as f_out:
        json.dump(parsed_data, f_out, indent=2, ensure_ascii=False)
    print("✅ Файл успешно преобразован и сохранён как test_data_clean.json")

except Exception as e:
    print("❌ Ошибка при разборе данных:", e)
    # Для отладки можно сохранить "исправленный" текст
    with open('example/fixed_content.txt', 'w', encoding='utf-8') as f_debug:
        f_debug.write(fixed_content)
    print("Сохранён исправленный текст в fixed_content.txt для отладки")