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

        # Add paths from sys.path that are site-packages directories this works for built-in modules
        paths.extend(venv_paths)

        # User site-packages
        if site.ENABLE_USER_SITE:
            venv_paths.append(site.USER_SITE)
            # Add virtual environment site-packages paths to the main paths list
        # Add common Ansible collection paths within the virtual environment
        for venv_path in venv_paths:
            # Standard collection path in site-packages
            paths.append(os.path.join(venv_path, "ansible_collections"))

        # Current working directory
        paths.append(os.path.join(os.getcwd(), "ansible_collections"))

        # Append any ANSIBLE_COLLECTIONS_PATH environment variable
        env_path = os.environ.get("ANSIBLE_COLLECTIONS_PATH")
        if env_path:
            for path in env_path.split(os.pathsep):
                paths.append(path)

        # Add standard Ansible collection paths
        if hasattr(C, "COLLECTIONS_PATHS"):
            paths.extend(C.COLLECTIONS_PATHS)

        # Remove duplicates while preserving order
        unique_paths = []
        for path in paths:
            if path not in unique_paths:
                unique_paths.append(path)

        logger.debug("Collection search paths: %s", unique_paths)
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
        if "." in module_name:
            collection_parts = module_name.split(".")
            if len(collection_parts) >= 3:
                namespace = collection_parts[0]
                collection = collection_parts[1]
                module = ".".join(collection_parts[2:])

                # Look in all possible collection paths
                collections_paths = self._get_collection_paths()

                for path in collections_paths:
                    # Two potential directory structures to check
                    module_paths = [
                        # Standard structure for Ansible collections
                        os.path.join(
                            path,
                            namespace,
                            collection,
                            "plugins",
                            "modules",
                            module.replace(".", os.path.sep) + ".py",
                        ),
                        # Alternative structure for Ansible collections
                        os.path.join(
                            path,
                            namespace,
                            "plugins",
                            "modules",
                            module.replace(".", os.path.sep) + ".py",
                        ),
                        # For buit-in modules, check in the modules directory
                        os.path.join(
                            path,
                            namespace,
                            "modules",
                            module.replace(".", os.path.sep) + ".py",
                        ),
                    ]

                    for module_path in module_paths:
                        if os.path.exists(module_path):
                            logger.debug("Found module at %s", module_path)
                            return module_path

        # For built-in modules, check in multiple locations
        module_paths = []
        
        # Handle DEFAULT_MODULE_PATH which might be a list or a single path
        if hasattr(C, 'DEFAULT_MODULE_PATH'):
            default_paths = C.DEFAULT_MODULE_PATH if isinstance(C.DEFAULT_MODULE_PATH, list) else [C.DEFAULT_MODULE_PATH]
            for default_path in default_paths:
                module_paths.append(
                    os.path.join(default_path, module_name.replace(".", os.path.sep) + ".py")
                )

        # Also look in lib/ansible/modules
        for path in sys.path:
            if "ansible" in path:
                potential_path = os.path.join(
                    path, "modules", module_name.replace(".", os.path.sep) + ".py"
                )
                if os.path.exists(potential_path):
                    module_paths.append(potential_path)

        for module_path in module_paths:
            if os.path.exists(module_path):
                logger.debug("Found built-in module at %s", module_path)
                return module_path

        logger.warning("Could not find module %s in any path", module_name)
        return None

    def setup_mocks(self) -> None:
        """
        Replace original modules with mocked versions.
        Backs up original modules before replacing them.
        """
        for module_name, mock_path in self.modules_to_mock.items():
            original_path = self._find_module_path(module_name)

            if not original_path:
                logger.warning("Could not find module %s to mock", module_name)
                continue

            if not os.path.exists(mock_path):
                logger.warning("Mock implementation not found at %s", mock_path)
                continue

            # Backup the original module
            backup_path = f"{original_path}.bak"
            shutil.copy2(original_path, backup_path)

            # Store paths for later restoration
            self.original_modules[module_name] = original_path
            self.backup_paths[module_name] = backup_path

            # Replace with mock
            shutil.copy2(mock_path, original_path)
            logger.info("Replaced %s with mock implementation", module_name)

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
                logger.info("Restored original %s module", module_name)

    def __enter__(self):
        """Support for context manager protocol."""
        self.setup_mocks()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure restoration happens when exiting the context."""
        self.restore_modules()
