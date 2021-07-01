import csv

with open('example.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    new_csv = []
    for row in csv_reader:
        new_row = []
        i = 0
        if line_count > 0:
            for element in row:
                if i == 0:
                    new_row.append(element)
                else:
                    level = int(int(element)/25)
                    new_row.append((level, int(element)))
                i += 1
            new_csv.append(new_row)

        line_count += 1

    with open('priority_example.csv', 'w') as f:
        writer = csv.writer(f, delimiter=';')

        # write multiple rows
        writer.writerows(new_csv)