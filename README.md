# KiwiQ_Assignment<br/>

Problem Statement: https://careful-mushroom-c61.notion.site/Assignment-Problem-Statement-12c6da3f922d80d8a49ecc16a606c417<br/>

In this Django Project, the default SQLite database is used. The code is divided into different python scripts. <br/>
1. validator.py validates the different properties of the graph and makes sure that the setup is not violating anything.<br/>
2. executer.py executes the graph and creates instances of different models. It triggers functionalities from validator.py to validate the graph.<br/>
3. models.py has different models as mentioned in the schema of the problem statement<br/>
4. test_script.py calls the executor.py to run the graph. It passes a graph configuration file as input. The output contains data_out values of nodes, islands (if any), topological order etc.<br/>

Steps to run this repository<br/>
In terminal type:<br/>
Step 1: >> git clone https://github.com/SamaySawal/KiwiQ_Assignment.git<br/>
Step 2: >> cd KiwiQ_Assignment<br/>
Step 3: >> python manage.py migrate<br/>
Step 4: >> python manage.py runserver<br/>
<br/>
On a different terminal:<br/>
Step 1: >> cd KiwiQ_Assignment<br/>
Step 2: >> python manage.py test_script<br/>

The output will be available on the second terminal. To ensure robust testing we can add more test cases instances in the test_script.py file.<br/>
