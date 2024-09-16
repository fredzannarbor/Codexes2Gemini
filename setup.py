from setuptools import setup, find_packages


setup(
    name='Codexes2Gemini',
    version='0.3.4.6',
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
    package_dir={'': 'Codexes2Gemini'},  # Root package is in 'Codexes2Gemini' directory
    packages=find_packages(where='Codexes2Gemini',
                           exclude=['user_data', 'user_data/*', 'user_data/**/*']),
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
        'resources': [  # Add this separate entry for 'resources'
            '*',  # Include everything directly under 'resources'
            '*/*',  # Include everything one level deep
            '*/*/*',  # Include everything two levels deep (adjust as needed)
        ],
    },
    install_requires=['streamlit', 'pymupdf', 'pypandoc', 'python-docx', 'google-generativeai', 'docx2txt', 'chardet',
                      'google-cloud-texttospeech'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
)
