from app.events.triggers import ALL_TRIGGERS, EventTrigger, RegionTrigger

TRIGGER_TEMPLATE = \
'''> `{trigger_nid}`: {trigger_desc}
'''

PROPERTY_TEMPLATE = \
'''> - **{property_name}** (`{property_type}`): {property_desc}
'''

NO_FIELD_MSG = \
'''> - No custom fields
'''

def _document_trigger(trigger: EventTrigger) -> str:
  try:
    docstr = trigger.__doc__
    lines = docstr.split('\n')
    desclines = [line.strip().replace('\n', '') for line in lines if not ':' in line]
    arglines = [line.strip().replace('\n', '') for line in lines if ':' in line]
    desc_str = TRIGGER_TEMPLATE.format(trigger_nid=trigger.nid if hasattr(trigger, 'nid') else trigger.__name__, trigger_desc=' '.join(desclines))
    any_property = False
    for argline in arglines:
      any_property = True
      name, desc = argline.strip().split(":")
      typename = trigger.__annotations__.get(name, '')
      desc_str += PROPERTY_TEMPLATE.format(property_name=name, property_type=typename, property_desc=desc)
    if not any_property:
      desc_str += NO_FIELD_MSG
    desc_str += '\n---------------------'
    return desc_str
  except:
    print("error, failed to document for func", trigger.nid)
    return ""

def generate_trigger_docs():
  full_doc_str = ""
  # automatically generate the query functions doc
  # write base
  query_base = open('utilities/docgen/trigger_reference_base.txt', 'r')
  full_doc_str += query_base.read() + "\n"

  documented_triggers = ALL_TRIGGERS.copy()
  documented_triggers.append(RegionTrigger)
  for trigger in documented_triggers:
    trigger_docstr = _document_trigger(trigger)
    full_doc_str += trigger_docstr + '\n'

  with open('docs/source/appendix/trigger_reference.md', 'w') as trigger_docs:
    trigger_docs.write(full_doc_str)
