import ast

try:
    content = open('app.py', encoding='utf-8').read()
    ast.parse(content)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error at line {e.lineno}: {e.msg}")
    lines = content.split('\n')
    for i in range(max(0, e.lineno-5), min(len(lines), e.lineno+3)):
        print(f"{i+1}: {repr(lines[i])}")
