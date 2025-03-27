import os

def test_csv_generated():
    assert os.path.exists("data/solution_data.csv"), "CSV file missing!"
    assert os.path.getsize("data/solution_data.csv") > 0, "CSV file is empty!"

def test_gif_generated():
    assert os.path.exists("data/heat_equation_simulation.gif"), "GIF file missing!"
    assert os.path.getsize("data/heat_equation_simulation.gif") > 0, "GIF file is empty!"
