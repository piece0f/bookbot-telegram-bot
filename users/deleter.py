ids = input()
ids = ids.split(', ')

for id_ in ids:
    for i in range(0, 3):
        with open(f'users{i}', 'r') as file_read:
            group_list = file_read.readlines()
        if id_ + '\n' in group_list:
            group_list.remove(id_ + '\n')
            with open(f'users{i}', 'w') as file_write:
                file_write.write(''.join(group_list))
