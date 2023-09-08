import csv
def read_csv(parameter):
    input_file = csv.DictReader(open("configs/demo.csv"))
    parameter_list = []
    for row in input_file:
        parameter_list.append(row[str(parameter)])
    return parameter_list

round = read_csv('XMAX')
print(round)
