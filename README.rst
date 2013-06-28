BREEZE
=========================
**A Customizable, Web-based Portal for 
Computational Statistics and Biomedical Data Analysis**

The aim of the BREEZE project is to build an easy approachable, continuous and 
real-time communication bridge between biologists and bioinformaticians. BREEZE 
provides the biologists a chance to analyse their data by themselves at any time and 
bioinformaticians with a tool to wrap their routine analysis R-scripts with web interface 
for easy access.

Insired by: FIMM

What it IS?
---------
- Web-based interface for the R-engine.
- A portal for bioinformaticians to  collect readyto-use data analysis scripts implemented in R language.
- A place where biologists can easily themselves run quality control checks and start routine analysis of their data.

What it IS NOT?
---------
- It is not a place to store your data. 
- It is not a framework to develop R scripts.
- It does not perform any computation itself.

Why would you use BREEZE?
---------
If you are a biologist and you DO NOT want to bother with R code and poke bioinformaticians every time you get 
new data, you are very welcome to BREEZE. If you are a bioinformatician and create R scripts and want to make them available to FIMM researchers, go 
ahead to push them to BREEZE.


Getting Started (for devs)
---------------
- git clone
- virtualenv --no-site-packages venv
- source venv/bin/activate
- pip install -r requirements.txt
- python manage.py runserver


We are aimed to build a 24/7 communication bridge between
biologists and bioinformatics resources.
