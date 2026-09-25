from setuptools import setup, find_packages

setup(
    name="foresightai",
    author="Ujjawal Bisht",
    author_email="ujjawalbisht@gmail.com",
    license="MIT",
    version="0.1.0",
    description="LLM-based persona simulation for pre-release customer reaction prediction",
    long_description=(
        "ForeSightAI models synthetic personas and simulates pre-release customer reactions "
        "using LLM-based analysis pipelines."
    ),
    long_description_content_type="text/plain",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
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