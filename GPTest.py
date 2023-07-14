import ast
import sys
import os

class DefinitionCollector(ast.NodeVisitor):
    def __init__(self):
        self.definitions = {
            'classes': set(),
            'functions': set(),
            'imports': set(),
        }

    def visit_ClassDef(self, node):
        self.definitions['classes'].add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.definitions['functions'].add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.definitions['imports'].add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.definitions['imports'].add(alias.name)
        self.generic_visit(node)


def analyze_definitions(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())

    collector = DefinitionCollector()
    collector.visit(tree)

    return collector.definitions


def project_structure_and_info(path):
    all_files = []  # List to hold all file paths
    all_imports = set()
    all_classes = set()
    all_functions = set()

    for root, dirs, files in os.walk(path):
        for name in files:
            all_files.append(os.path.join(root, name))  # Add each file path to the list
            if name.endswith('.py'):
                definitions = analyze_definitions(os.path.join(root, name))
                all_imports.update(definitions['imports'])
                all_classes.update(definitions['classes'])
                all_functions.update(definitions['functions'])

    with open("allboutme.txt", "w") as file:
        file.write(f'Python Version: {sys.version}\n')
        file.write(f'\nAll Imports: {all_imports}\n')
        file.write(f'\nAll Classes: {all_classes}\n')
        file.write(f'\nAll Functions: {all_functions}\n')
        file.write(f'All Files:\n')
        for file_path in all_files:  # Write each file path to the output file
            file.write(f'   {file_path}\n')


project_path = "/Users/kkmac2/Downloads/TelegramBots/FTGB"
project_structure_and_info(project_path)