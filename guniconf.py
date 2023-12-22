from db import seedDatabase

def on_starting(server):
    seedDatabase()
