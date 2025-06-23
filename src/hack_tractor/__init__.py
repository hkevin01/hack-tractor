"""
Hack Tractor - Educational Agricultural Equipment Interface Toolkit

A hackathon project exploring AI, ML, and agricultural technology.
This package provides educational tools for farm equipment simulation,
AI-powered optimization, and predictive maintenance demonstrations.

Educational Focus:
- Hackathon competition demonstration
- Agricultural technology research and learning
- Proof-of-concept development
- Right-to-Repair advocacy through open-source solutions
- Safe exploration of equipment interfaces through simulation

Safety Notice:
This package is designed for educational and demonstration purposes only.
All equipment interfaces are simulated for safety and learning.
"""

__version__ = "0.1.0"
__author__ = "Hack Tractor Team"
__email__ = "team@hack-tractor.edu"
__description__ = "Educational agricultural equipment interface toolkit"

# Package metadata
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]

# Educational and safety notices
EDUCATIONAL_NOTICE = """
🎓 EDUCATIONAL PROJECT NOTICE 🎓
This is a hackathon competition project designed for educational exploration
and demonstration of agricultural technology possibilities.

All equipment interfaces are simulated for safety and learning purposes.
Not intended for production use without proper validation and testing.
"""

SAFETY_NOTICE = """
🛡️ SAFETY FIRST 🛡️
- All equipment interfaces are simulated
- Multiple fail-safe mechanisms implemented
- Emergency stop capabilities included
- Educational use only - not for production deployment
- Respects intellectual property and safety regulations
"""


def print_notices():
    """Print educational and safety notices."""
    print(EDUCATIONAL_NOTICE)
    print(SAFETY_NOTICE)


if __name__ == "__main__":
    print_notices()
