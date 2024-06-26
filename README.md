# **💭Auto Graph of Thoughts: A Hands-free and Cost Effective Method for using Graph of Thoughts**

## Introduction
Auto Graph of Thoughts (AutoGoT) which extends GoT by allowing LLMs to freely generate prompts for each type of Thought and utilizes those prompts to generate output for each thought.

**Keywords:** LLM, Natural language processing, Prompting.

## Overview Architecture
<p align="center">
<img src="assets/current_got/Arch.png" />

<i>Graph Architecture of AutoGoT</i>
</p>


## License
This project is licensed under the [MIT License](./LICENSE).

## Configurations

<p align="left">
 <a href=""><img src="https://img.shields.io/badge/python-3.9-aff.svg"></a>
 <a href=""><img src="https://img.shields.io/badge/graphviz-fff.svg"></a>
</p>

### Prerequisites and System Requirements
- You must have [graphviz](https://graphviz.org) framework inside your system.
    - Ubuntu:
    ```zsh
    sudo apt-get install graphviz
    ```
    - MacOS:
    ```zsh
    brew install graphviz
    ```

### Run locally
- Create conda environment, note that python version should be <span style="color:#9BB8ED;">Python 3.9</span>
```
conda create --name graph-of-thought-genor python=3.9
conda activate graph-of-thought-genor
```

- Install required packages

```
pip install -r requirements.txt --no-cache-dir
```