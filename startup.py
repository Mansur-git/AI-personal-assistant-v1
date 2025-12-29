from private_tools import create_tasks_table
from private_tools import create_user_profile_table
import os

def startup():
    create_tasks_table()
    create_user_profile_table()