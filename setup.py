from setuptools import setup, find_packages
from os import path
import glob

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='telegram-find-in-channel-bot',
    version='0.4.0',
    url='https://github.com/chuangzhu/telegram-find-in-channel-bot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Zhu Chuang',
    author_email='genelocated@yandex.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['telethon==1.21.1'],
    python_requires='>=3.7',  # We used some f-strings here
    entry_points={
        'console_scripts':
        ['telegram-find-in-channel-bot = tgficbot.main:main']
    })
