"""_summary_

Returns:
    _type_: _description_
"""
import os
import shutil
import logging
import sys
import site
from typing import Dict, Optional, List
import ansible.constants as C

logger = logging.getLogger(__name__)

class ModuleMocker:
    """
    Class to mock Ansible modules by replacing them with custom implementations.
    """
    
    def __init__(self, modules_to_mock: Dict[str, str]):
        """
        Initialize the ModuleMocker.
        
        Args:
            modules_to_mock: Dictionary mapping module names to paths of mock implementations
                             e.g., {"community.general.file_size": "/path/to/mock/file_size.py"}
        """
        self.modules_to_mock = modules_to_mock
        self.original_modules = {}  # To store paths to original modules
        self.backup_paths = {}  # To store paths to backup files
        
    def _get_collection_paths(self) -> List[str]:
        """
        Get a comprehensive list of paths where Ansible collections might be located,
        including virtual environment paths.
        
        Returns:
            List of paths to check for Ansible collections
        """
        paths = []
        
        
        # Add virtual environment site-packages paths
        venv_paths = []
        
        # Current virtual environment site-packages
        venv_paths.extend(site.getsitepackages())
        
        # User site-packages
        if site.ENABLE_USER_SITE:
            venv_paths.append(site.USER_SITE)
            
        # Add common Ansible collection paths within the virtual environment
        for venv_path in venv_paths:
            # Standard collection path in site-packages
            paths.append(os.path.join(venv_path, 'ansible_collections'))
        
        # Current working directory
        paths.append(os.path.join(os.getcwd(), 'ansible_collections'))
        
        # Append any ANSIBLE_COLLECTIONS_PATH environment variable
        env_path = os.environ.get('ANSIBLE_COLLECTIONS_PATH')
        if env_path:
            for path in env_path.split(os.pathsep):
                paths.append(path)

        # Add standard Ansible collection paths
        if hasattr(C, 'COLLECTIONS_PATHS'):
            paths.extend(C.COLLECTIONS_PATHS)
                    
        # Remove duplicates while preserving order
        unique_paths = []
        for path in paths:
            if path not in unique_paths:
                unique_paths.append(path)
        
        logger.debug(f"Collection search paths: {unique_paths}")
        return unique_paths
        
    def _find_module_path(self, module_name: str) -> Optional[str]:
        """
        Find the path to the specified Ansible module.
        
        Args:
            module_name: Fully qualified module name (e.g., "community.general.file_size")
            
        Returns:
            The path to the module file or None if not found
        """
        # Parse the collection name
        if '.' in module_name:
            collection_parts = module_name.split('.')
            if len(collection_parts) >= 3:
                namespace = collection_parts[0]
                collection = collection_parts[1]
                module = '.'.join(collection_parts[2:])
                
                # Look in all possible collection paths
                collections_paths = self._get_collection_paths()
                
                for path in collections_paths:
                    # Two potential directory structures to check
                    module_paths = [
                        # Standard structure: ansible_collections/namespace/collection/plugins/modules/
                        os.path.join(
                            path, 
                            'ansible_collections', 
                            namespace, 
                            collection, 
                            'plugins',
                            'modules',
                            module.replace('.', os.path.sep) + '.py'
                        ),
                        # Alternative structure when path already includes ansible_collections
                        os.path.join(
                            path, 
                            namespace, 
                            collection, 
                            'plugins',
                            'modules',
                            module.replace('.', os.path.sep) + '.py'
                        )
                    ]
                    
                    for module_path in module_paths:
                        if os.path.exists(module_path):
                            logger.debug(f"Found module at {module_path}")
                            return module_path
        
        # For built-in modules, check in multiple locations
        module_paths = [
            os.path.join(C.DEFAULT_MODULE_PATH, module_name.replace('.', os.path.sep) + '.py')
        ]
        
        # Also look in lib/ansible/modules
        for path in sys.path:
            if 'ansible' in path:
                potential_path = os.path.join(path, 'modules', module_name.replace('.', os.path.sep) + '.py')
                if os.path.exists(potential_path):
                    module_paths.append(potential_path)
        
        for module_path in module_paths:
            if os.path.exists(module_path):
                logger.debug(f"Found built-in module at {module_path}")
                return module_path
                
        logger.warning(f"Could not find module {module_name} in any path")
        return None

    def setup_mocks(self) -> None:
        """
        Replace original modules with mocked versions.
        Backs up original modules before replacing them.
        """
        for module_name, mock_path in self.modules_to_mock.items():
            original_path = self._find_module_path(module_name)
            
            if not original_path:
                logger.warning(f"Could not find module {module_name} to mock")
                continue
                
            if not os.path.exists(mock_path):
                logger.warning(f"Mock implementation not found at {mock_path}")
                continue
                
            # Backup the original module
            backup_path = f"{original_path}.bak"
            shutil.copy2(original_path, backup_path)
            
            # Store paths for later restoration
            self.original_modules[module_name] = original_path
            self.backup_paths[module_name] = backup_path
            
            # Replace with mock
            shutil.copy2(mock_path, original_path)
            logger.info(f"Replaced {module_name} with mock implementation")
            
    def restore_modules(self) -> None:
        """
        Restore original modules from backups.
        """
        for module_name, original_path in self.original_modules.items():
            backup_path = self.backup_paths.get(module_name)
            if backup_path and os.path.exists(backup_path):
                # Restore from backup
                shutil.copy2(backup_path, original_path)
                # Remove backup
                os.remove(backup_path)
                logger.info(f"Restored original {module_name} module")
    
    def __enter__(self):
        """Support for context manager protocol."""
        self.setup_mocks()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure restoration happens when exiting the context."""
        self.restore_modules()