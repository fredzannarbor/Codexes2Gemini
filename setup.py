from setuptools import setup, find_packages
import os

print(os.listdir('Codexes2Gemini'))
print(os.listdir('.'))
setup(
    name='Codexes2Gemini',
    version='0.4.0.0',  # Update your version number
    python_requires='>=3.11',
    description='Humans and AIs making books richer, more diverse, and more surprising.',
    url='https://github.com/fredzannarbor/Codexes2Gemini',
    entry_points={
        'console_scripts': [
            'codexes2gemini-ui = Codexes2Gemini.ui.streamlit_ui:main',
            'codexes2gemini-ui-1455 = Codexes2Gemini.ui.streamlit_ui:main',
            'dataset2gemini = Codexes2Gemini.ui.build_from_dataset_of_codexes:main'
        ]
    },
    author='Fred_Zimmerman',
    author_email='wfz@nimblebooks.com',
    license='MIT',
    packages=['Codexes2Gemini', 'Codexes2Gemini.ui', 'resources'],  # No need for package_dir
    package_data={
        'Codexes2Gemini': [
            'classes/*',
            'classes/*/*',
            'classes/*/*/*',
            'classes/*/*/*/*',
            'ui/*',
            'ui/*/*',
            'resources/*',
            'resources/*/*',
            'resources/*/*/*',
            'documentation/*',
            'documentation/*/*',
        ],
        'resources': [
            '*',
            '*/*',
            '*/*/*',
        ],
    },
    install_requires=['streamlit', 'pymupdf', 'pypandoc', 'python-docx', 'google-generativeai', 'docx2txt', 'chardet',
                      ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
)