import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.category import Category

print("Category.children lazy strategy:", Category.children.property.lazy)
print("Category.parent lazy strategy:", Category.parent.property.lazy)
