from setuptools import setup, find_packages


def get_requirements():
    requirements_list = []
    with open('requirements.txt') as requirements:
        for install in requirements:
            requirements_list.append(install.strip())
    return requirements_list


setup(name='telegram-find-in-channel-bot',
      version='0.1.2',
      author='Zhu Chuang',
      author_email='genelocated@yandex.com',
      packages=find_packages(),
      install_requires=get_requirements(),
      entry_points={
          'console_scripts': ['telegram-find-in-channel-bot = tgficbot.main:main']
      })
