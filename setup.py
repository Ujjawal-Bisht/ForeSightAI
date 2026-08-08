from setuptools import setup, find_packages

setup(
    name="foresightai",
    version="0.1.0",
    description="LLM-based persona simulation for pre-release customer reaction prediction",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.12",
    install_requires=[
        "scikit-learn>=1.4",
        "hdbscan>=0.8",
        "numpy>=1.26",
        "pandas>=2.2",
        "sentence-transformers>=2.7",
        "django-environ==0.14.0",
    ],
    extras_require={
        "dev": ["pytest>=8.0", "pytest-django>=4.8", "jupyter"],
    },
)