<p align="center">
<a href="">
    <img src="https://img.shields.io/badge/makes-372839-blue">
</a>

<a href="">
    <img src="https://img.shields.io/badge/no-23122-green">
</a>

<a href="">
    <img src="https://img.shields.io/badge/sense-666-blue">
</a>
<a href="">
    <img src="https://img.shields.io/badge/butt-88-yellow">
</a>
<a href="">
    <img src="https://img.shields.io/badge/attracts-100-green">
</a>
</p>

## Association rules visualisation with Python

 Python-arulesviz is a port of an incredible R's library [arulesviz](https://cran.r-project.org/web/packages/arulesViz/vignettes/arulesViz.pdf). If familiar with R I would highly recommend to try it.

Python-arulesviz works as a jupyter-notebook widget ([Video (30mb)](/data/demo.gif)):
![](/data/preview.png)

## Install:
``` bash
pip install arulesviz
```

## Usage:
``` python
g = Arulesviz(transactions, 0.001, 0.3, 12, products_to_drop=[])
g.create_rules()
g.plot_graph(width=1800, directed=False, charge=-150, link_distance=20)
```

## [Detailed examples](/examples/groceries.ipynb)
