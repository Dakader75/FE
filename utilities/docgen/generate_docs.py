from app.utilities.str_utils import snake_to_readable
from typing import Callable, Dict, List
from app.engine.query_engine import GameQueryEngine
import inspect

FUNC_TEMPLATE = \
'''
#### {readable_func_name}

    {func_name}{func_signature}

{func_doc}
  ---------------------
'''


def document_function(func: Callable) -> str:
  try:
    func_doc = func.__doc__
    func_signature = str(inspect.signature(func))
    func_signature = func_signature.replace('->', '\n\t\t->').replace('self, ', '')
    func_name = func.__name__
    readable_func_name = snake_to_readable(func_name)
    return FUNC_TEMPLATE.format(readable_func_name=readable_func_name, func_name=func_name, func_signature=str(func_signature), func_doc=func_doc)
  except:
    print("error, failed to document for func", func.__name__)
    return ""

# python -m utilities.docgen.generate_docs && ./docs/make.bat html
if __name__ == '__main__':
  # automatically generate the query functions doc
  with open('docs/source/appendix/Useful_Functions.md', 'w') as query_docs:
    # write base
    query_base = open('utilities/docgen/query_funcs_base.txt', 'r')
    query_docs.write(query_base.read() + "\n")

    query_funcs = [funcname for funcname in dir(GameQueryEngine) if not funcname.startswith('_')]
    # organize by tag
    query_doc_entries: Dict[str, List[str]] = {}
    for func_name in query_funcs:
      func = getattr(GameQueryEngine, func_name)
      entry = document_function(func)
      func_tag = func.tag
      if func_tag not in query_doc_entries:
        query_doc_entries[func_tag] = []
      query_doc_entries[func_tag].append(entry)

    for tag in sorted(query_doc_entries.keys()):
      section_header = \
"""
## {tag}
""".format(tag=tag)
      query_docs.write(section_header + "\n\n")
      for func_entry in sorted(query_doc_entries[tag]):
        query_docs.write(func_entry + "\n")
