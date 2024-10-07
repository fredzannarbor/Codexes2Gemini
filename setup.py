
from setuptools import setup, find_packages
import os

# TODO fix build of datasets2gemini entry point in testpypi
print(os.listdir('Codexes2Gemini'))
print(os.listdir('.'))


def run_streamlit_ui():
    """Wrapper function to change working directory before running Streamlit UI."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    from Codexes2Gemini.ui.streamlit_ui import main
    main()


def run_build_from_dataset():
    """Wrapper for dataset2gemini entry point."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    from Codexes2Gemini.ui.build_from_dataset_of_codexes import main
    main()

setup(
    name='Codexes2Gemini',
    version='0.4.3.3',  # Update your version number
    python_requires='>=3.11',
    description='Humans and AIs making books richer, more diverse, and more surprising.',
    url='https://github.com/fredzannarbor/Codexes2Gemini',
    entry_points={
        'console_scripts': [
            'codexes2gemini-ui = setup:run_streamlit_ui',
            'codexes2gemini-ui-1455 = setup:run_streamlit_ui',  # Use the wrapper here
            'dataset2gemini = setup:run_build_from_dataset'  # Use the wrapper here
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