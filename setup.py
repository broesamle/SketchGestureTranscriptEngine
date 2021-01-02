import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spadoak",
    version="0.1.0",
    author="Martin Brösamle",
    author_email="m@martinbroesamle.de",
    description="SpaDoAK: Spatial Domain Annotation Kit (not maintained!)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/broesamle/spadoak",
    packages=setuptools.find_packages(),
    keywords=["svg",
              "vector graphics",
              "scalable vector graphics",
              "xml",
              "visualisation"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Visualization",
        "Intended Audience :: Science/Research"],
    install_requires=['pyx>=0.15', 'latexcodec>=2'],
    python_requires='>=3.7')
