current_custom_path = None
def get_components() -> bool:
    # For getting custom project components at runtime
    import importlib
    import importlib.util
    import os
    import sys
    from app.resources.resources import RESOURCES

    global current_custom_path

    cc_path = RESOURCES.get_custom_components_path()
    if not cc_path:
        return False

    module_path = os.path.join(cc_path, '__init__.py')
    if module_path != current_custom_path and os.path.exists(module_path):
        current_custom_path = module_path
        print("Importing Custom Components")
        spec = importlib.util.spec_from_file_location('custom_components', module_path)
        module = importlib.util.module_from_spec(spec)
        # spec.name is 'custom_components'
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

    return os.path.exists(module_path)

# def clean():
#     import sys
#     if 'custom_components' in sys.modules:  # clean up namespace of other projects files
#         del sys.modules['custom_components']
#         for module in list(sys.modules.keys()):
#             if module.startswith('custom_components'):
#                 del sys.modules[module]
