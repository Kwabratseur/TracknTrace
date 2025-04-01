from setuptools import setup
from setuptools.command.install import install

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(name='TracknTrace',
      version='0.0.1',
      description='Track building performance and Trace errors',
      long_description=long_description,
      long_description_content_type="text/markdown",
      include_package_data=True,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education'
      ],
      keywords='Track Trace building performance errors gap analysis DSMR KNMI blame',
      url='https://github.com/Kwabratseur/TracknTrace',
      author='Jeroen van \'t Ende',
      author_email='jeroen.vantende@outlook.com',
      license='MIT', # mit should be fine, looking at the deps.. only those BSD-3
      packages=['TracknTrace',
                'TracknTrace.preprocessor',
                'TracknTrace.categorizer'],
      package_data={"TracknTrace": ["*.metadata", "*.txt"]},
      install_requires=[
        'pandas', # BSD-3
        'numpy', # BSD-3
        'markdown',
        'matplotlib',
        'pillow',
        'pytexit',
        'seaborn',
        'scikit-learn',
        'mufit',
        'openpyxl',
        'tabulate',
        'latex'
      ],
      entry_points = {
        'console_scripts': ['TracknTrace=TracknTrace.wrapper:main'],#,
                            #'preprocessor=TracknTrace.preprocessor',
                            #'categorizer=TracknTrace.categorizer'],
      },
      zip_safe=False)
