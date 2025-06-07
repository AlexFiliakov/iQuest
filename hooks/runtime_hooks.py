"""
Runtime hooks to fix import issues
"""

import sys
import os

# Fix jaraco.text missing drop_comment function
def _fix_jaraco_text():
    """Fix missing drop_comment function in jaraco.text"""
    try:
        import jaraco.text
        if not hasattr(jaraco.text, 'drop_comment'):
            # Add a dummy drop_comment function
            def drop_comment(s, comment='#'):
                """Remove comment from string"""
                if comment in s:
                    return s[:s.index(comment)].rstrip()
                return s
            jaraco.text.drop_comment = drop_comment
    except ImportError:
        # Create a minimal jaraco.text module
        import types
        jaraco = types.ModuleType('jaraco')
        jaraco.text = types.ModuleType('jaraco.text')
        
        def drop_comment(s, comment='#'):
            """Remove comment from string"""
            if comment in s:
                return s[:s.index(comment)].rstrip()
            return s
        
        jaraco.text.drop_comment = drop_comment
        sys.modules['jaraco'] = jaraco
        sys.modules['jaraco.text'] = jaraco.text

# Fix pkg_resources vendor imports and missing attributes
def _fix_pkg_resources_vendor():
    """Ensure pkg_resources vendor modules and NullProvider are available"""
    try:
        import pkg_resources
        
        # Ensure NullProvider exists
        if not hasattr(pkg_resources, 'NullProvider'):
            # Create a minimal NullProvider class
            class NullProvider:
                """Minimal NullProvider implementation"""
                def __init__(self, module):
                    self.module = module
                
                def get_resource_filename(self, manager, resource_name):
                    return None
                
                def get_resource_stream(self, manager, resource_name):
                    return None
                
                def get_resource_string(self, manager, resource_name):
                    return b''
                
                def has_resource(self, resource_name):
                    return False
                
                def resource_isdir(self, resource_name):
                    return False
                
                def resource_listdir(self, resource_name):
                    return []
                
                def run_script(self, script_name, namespace):
                    pass
                
                def get_metadata(self, name):
                    return ''
                
                def get_metadata_lines(self, name):
                    return []
                
                def has_metadata(self, name):
                    return False
            
            pkg_resources.NullProvider = NullProvider
        
        # Ensure register_loader_type exists
        if not hasattr(pkg_resources, 'register_loader_type'):
            def register_loader_type(loader_type, provider_factory):
                """Minimal implementation of register_loader_type"""
                # Store in a registry if needed
                if not hasattr(pkg_resources, '_provider_factories'):
                    pkg_resources._provider_factories = {}
                pkg_resources._provider_factories[loader_type] = provider_factory
            
            pkg_resources.register_loader_type = register_loader_type
        
        # Ensure get_provider exists
        if not hasattr(pkg_resources, 'get_provider'):
            def get_provider(package_or_requirement):
                """Minimal implementation of get_provider"""
                # Return NullProvider as a fallback
                return pkg_resources.NullProvider(package_or_requirement)
            
            pkg_resources.get_provider = get_provider
        
        # Also ensure _vendor exists
        if not hasattr(pkg_resources, '_vendor'):
            import types
            pkg_resources._vendor = types.ModuleType('pkg_resources._vendor')
            sys.modules['pkg_resources._vendor'] = pkg_resources._vendor
            
    except ImportError:
        import types
        pkg_resources = types.ModuleType('pkg_resources')
        
        # Create NullProvider
        class NullProvider:
            """Minimal NullProvider implementation"""
            def __init__(self, module):
                self.module = module
            
            def get_resource_filename(self, manager, resource_name):
                return None
            
            def get_resource_stream(self, manager, resource_name):
                return None
            
            def get_resource_string(self, manager, resource_name):
                return b''
            
            def has_resource(self, resource_name):
                return False
            
            def resource_isdir(self, resource_name):
                return False
            
            def resource_listdir(self, resource_name):
                return []
            
            def run_script(self, script_name, namespace):
                pass
            
            def get_metadata(self, name):
                return ''
            
            def get_metadata_lines(self, name):
                return []
            
            def has_metadata(self, name):
                return False
        
        pkg_resources.NullProvider = NullProvider
        
        # Add register_loader_type function
        def register_loader_type(loader_type, provider_factory):
            """Minimal implementation of register_loader_type"""
            if not hasattr(pkg_resources, '_provider_factories'):
                pkg_resources._provider_factories = {}
            pkg_resources._provider_factories[loader_type] = provider_factory
        
        pkg_resources.register_loader_type = register_loader_type
        
        # Add get_provider function
        def get_provider(package_or_requirement):
            """Minimal implementation of get_provider"""
            return pkg_resources.NullProvider(package_or_requirement)
        
        pkg_resources.get_provider = get_provider
        
        pkg_resources._vendor = types.ModuleType('pkg_resources._vendor')
        sys.modules['pkg_resources'] = pkg_resources
        sys.modules['pkg_resources._vendor'] = pkg_resources._vendor

# Apply fixes
_fix_jaraco_text()
_fix_pkg_resources_vendor()

# Add fallback for jaraco imports
class JaracoImportFixer:
    """Fallback importer for jaraco modules"""
    
    def find_module(self, fullname, path=None):
        if fullname.startswith('jaraco.'):
            return self
        return None
    
    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
            
        # Try to import from pkg_resources._vendor
        try:
            vendor_name = fullname.replace('jaraco.', 'pkg_resources._vendor.jaraco.')
            __import__(vendor_name)
            sys.modules[fullname] = sys.modules[vendor_name]
            return sys.modules[fullname]
        except ImportError:
            pass
            
        # Create empty module as fallback
        import types
        module = types.ModuleType(fullname)
        
        # Add drop_comment if this is jaraco.text
        if fullname == 'jaraco.text':
            def drop_comment(s, comment='#'):
                """Remove comment from string"""
                if comment in s:
                    return s[:s.index(comment)].rstrip()
                return s
            module.drop_comment = drop_comment
        
        sys.modules[fullname] = module
        return module

# Install the import fixer
sys.meta_path.insert(0, JaracoImportFixer())