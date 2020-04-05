from setuptools import setup, find_packages


setup(
    name='arulesviz',
    use_scm_version=True,
    description='Association Rules visualisation tool',
    version='0.0.1',
    url='https://github.com/zveryansky/python-arulesviz',
    author='Alex Zverianskii',
    author_email='',
    license='MIT',
    classifiers=[
    'License :: OSI Approved :: MIT License',

    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7'
    ],
    keywords='association rules graph bqplot arules arulesviz apriori lift slift',
    packages=find_packages(exclude=['examples', 'data']),
    install_requires=['ipywidgets', 'bqplot', 'efficient-apriori'],
)
