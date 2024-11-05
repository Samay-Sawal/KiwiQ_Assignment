# KiwiQ_Assignment

Problem Statement: https://careful-mushroom-c61.notion.site/Assignment-Problem-Statement-12c6da3f922d80d8a49ecc16a606c417

In this Django Project, the default SQLite database is used. The code is divided into different python scripts. 
1. validator.py validates the different properties of the graph and makes sure that the setup is not violating anything.
2. executer.py executes the graph and creates instances of different models. It triggers functionalities from validator.py to validate the graph.
3. models.py has different models as mentioned in the schema of the problem statement
4. test_script.py calls the executor.py to run the graph. It passes a graph configuration file as input. Output contains an island present, data_out values of nodes, island (if any) etc. 
