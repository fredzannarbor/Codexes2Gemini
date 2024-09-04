from setuptools import setup, find_packages

setup(
    name='Codexes2Gemini.leo_bloom_core',
    version='0.3.0',
    packages=find_packages(),
    install_requires=[
        'pandas', 'numpy', 'CurrencyConverter', 'streamlit'
    ],
    entry_points={
        'console_scripts': [
            'leo_bloom_core = leo_bloom_core.call_all_FROs:main'
        ]
    },
)

# TODO -- make all lower level imports relative
