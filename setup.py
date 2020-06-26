from setuptools import setup, find_packages

setup(name='telegram-find-in-channel-bot',
      version='0.2.0',
      author='Zhu Chuang',
      author_email='genelocated@yandex.com',
      packages=find_packages(),
      install_requires=['telethon==1.9.0'],
      entry_points={
          'console_scripts':
          ['telegram-find-in-channel-bot = tgficbot.main:main']
      })
