from setuptools import setup, find_packages

setup(
    name='Codexes2Gemini',
    version='0.2.0.4',
    python_requires='>=3.11',
    description='Humans and AIs making books richer, more diverse, and more surprising.',
    url='https://github.com/fredzannarbor/Codexes2Gemini',
    entry_points={
        'console_scripts': [
            'codexes2gemini-ui = Codexes2Gemini.UI.streamlit_ui:main',
            'codexes2gemini-ui-1455 = Codexes2Gemini.UI.streamlit_ui:main'
        ]
    },
    author='Fred_Zimmerman',
    author_email='wfz@nimblebooks.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'Codexes2Gemini': ['resources/prompts/*.json'],
    },
    install_requires=['streamlit'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
)