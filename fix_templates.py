import os
import re

TEMPLATES_DIR = "templates"

REPLACEMENTS = [
    ("url_for('main.')", "url_for('main.index')"),
]

# точечные исправления
SPECIFIC_FIXES = {
    "index.html": {
        "url_for('main.create_survey')": "url_for('main.create_survey')"
    }
}

def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # общий фикс
    content = content.replace("url_for('main.')", "url_for('main.index')")

    # index.html особые случаи
    if "index.html" in path:
        content = content.replace(
            "url_for('main.index')",
            "url_for('main.create_survey')"
        )

        # фикс кнопки (если есть неправильная логика)
        content = content.replace(
            'href="{{ url_for(\'main.create_survey\') }}" class="btn btn-success"',
            'href="{{ url_for(\'main.create_survey\') }}" class="btn btn-success"'
        )

    if content != original:
        print(f"FIXED: {path}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    for root, _, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith(".html"):
                fix_file(os.path.join(root, file))

    print("DONE")

if __name__ == "__main__":
    main()