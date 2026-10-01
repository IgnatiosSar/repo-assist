
from pathlib import Path

from repo_assist.models.code_chunk_model import CodeChunk
from repo_assist.models.repository_model import FileInfo
from repo_assist.parsers.code_parser import CodeParser
import tree_sitter, tree_sitter_java



class JavaCodeParser(CodeParser):
    def parse_file(self, file_info: FileInfo) -> list[CodeChunk]:
        path = file_info.path
        java_language = tree_sitter.Language(tree_sitter_java.language())
        parser = tree_sitter.Parser(java_language)
        code_in_bytes = Path(path).read_bytes()
        tree = parser.parse(code_in_bytes)
        root_node = tree.root_node
  
        methods = self.find_methods(root_node)
        chunks = self.create_code_chunks(methods, code_in_bytes, file_info)
        return chunks

        
    def find_methods(self, node):
        methods = []
        if node.type == "method_declaration":
            methods.append(node)
        for child in node.children:
            methods.extend(self.find_methods(child))
        return methods

    def find_symbol(self, node):
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        return name_node.text.decode("utf-8")

    def find_parent_class(self, node):
        parent = node.parent
        while parent is not None:
            if parent.type == "class_declaration":
                return self.find_symbol(parent)
            parent = parent.parent
        return None
    
    def create_code_chunks(self, methods, source_bytes, file_info):
        chunks = []
        for method in methods:
            symbol = self.find_symbol(method)
            parent_symbol = self.find_parent_class(method)
            start_line = method.start_point.row + 1  
            end_line = method.end_point.row + 1    
            start_byte = method.start_byte
            end_byte = method.end_byte
            content = source_bytes[start_byte:end_byte].decode("utf-8")

            chunks.append(CodeChunk(
                content=content,
                path=file_info.path,
                language=file_info.language,
                symbol=symbol,
                start_line=start_line,
                end_line=end_line,
                parent_symbol=parent_symbol
            ))
        return chunks
        