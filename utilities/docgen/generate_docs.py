from utilities.docgen.generate_trigger_docs import generate_trigger_docs
from utilities.docgen.generate_query_docs import generate_query_docs

# python -m utilities.docgen.generate_docs && ./docs/make.bat html
if __name__ == '__main__':
  generate_query_docs()
  generate_trigger_docs()