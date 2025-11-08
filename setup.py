from setuptools import setup, find_packages

setup(
    name="xml-lib",
    version="0.1.0",
    description="XML-Lifecycle Validator & Publisher with Relax NG + Schematron",
    author="XML-Lib Contributors",
    packages=find_packages(where="cli"),
    package_dir={"": "cli"},
    package_data={
        "": ["*.j2"],  # Include Jinja2 templates
    },
    include_package_data=True,
    data_files=[
        ("templates/php", [
            "templates/php/page.php.j2",
            "templates/php/minimal_page.php.j2",
            "templates/php/header.php.j2",
            "templates/php/footer.php.j2",
            "templates/php/toc.php.j2",
            "templates/php/functions.php.j2",
            "templates/php/style.css.j2",
        ]),
    ],
    install_requires=[
        "click>=8.1.0",
        "lxml>=4.9.0",
        "python-pptx>=0.6.21",
        "cryptography>=41.0.0",
        "jsonlines>=4.0.0",
        "psycopg2-binary>=2.9.0",
        "jinja2>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "xml-lib=xml_lib.cli:main",
        ],
    },
    python_requires=">=3.9",
)
