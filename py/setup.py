from setuptools import setup, find_packages

setup(
    name='cultural_heritage_imaging',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'opencv-python',
        'matplotlib',
        'vtk'
    ],
    entry_points={
        'console_scripts': [
            'mypackage=cultural_heritage_imaging.module:main',
        ],
    },
    author='Lilli Kelley, Chris Lenhard',
    author_email='lmk8240@rit.edu',
    description='A brief description of your package',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lillikelley/22753-cultural-heritage-imaging',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
