## About

This is a website with some useful tools for RF engineering. It should be up and running at https://rfdesigntools.pythonanywhere.com/

Give it a try !

Did you find a bug or do you have a suggestion for improvement? Email me at andresmmera@protonmail.com


## Deploy this site locally

## LINUX
  
### 1) Install the python virtual environment package on your base system:

        sudo apt-get install python3.10-venv

### 2) Create a virtual environment: 

        python3 -m venv virtualenv

####  2.1) Activate it: 
        
        source virtualenv/bin/activate
        
####  2.2) Install the required packages in your virtual environment:

        python3 -m pip install django
        python3 -m pip install numpy
        python3 -m pip install schemdraw
        python3 -m pip install matplotlib
        
### 3) Start the server 
 
        python3 manage.py runserver
        
### 4) Go to http://127.0.0.1:8000 in your browser

## WINDOWS

### 1) Clone the repo using VisualStudio
### 2)
#### 2.1) Activate the virtual environment

    C:\Users\your_username\source\repos\rf-design-tools\virtualenv\Scripts\activate

####  2.2) Install the required packages in your virtual environment:

        python3 -m pip install django
        python3 -m pip install numpy
        python3 -m pip install schemdraw
        python3 -m pip install matplotlib

### 3) Start the server 
 
        python3 manage.py runserver
        
### 4) Go to http://127.0.0.1:8000 in your browser