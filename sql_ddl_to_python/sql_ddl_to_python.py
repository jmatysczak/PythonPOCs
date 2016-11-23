import os
import re
import sqlite3


def generate_model():
    with sqlite3.connect(':memory:') as conn:
        with open('ddl.sql', 'r') as f:
            conn.executescript(f.read())

        tables_by_name = {}

        print 'Collecting table meta data...'
        tables = execute(conn, "SELECT * FROM sqlite_master where type = '%s'" % 'table')
        for table in tables:
            table_name = table['tbl_name'].lower()
            print '    Processing: %s' % table_name

            columns = execute(conn, "PRAGMA table_info('%s')" % table_name)
            foreign_keys = execute(conn, "PRAGMA foreign_key_list('%s')" % table_name)

            for column in columns:
                column['name'] = column['name'].lower()
                column['is_embeddable'] = True
                column['is_single_cardinality'] = True

            tables_by_name[table_name] = {
                'columns': columns,
                'is_enum': is_enum(table_name, columns),
                'type_name': table_name.title().replace('_', ''),
                'foreign_keys': {fk['from']: fk['table'] for fk in foreign_keys},
                'primary_keys': [column['name'] for column in columns if column['pk'] == 1],
                'custom_imports': []
            }

        print 'Determining types, pass 1...'
        for table_name, table_info in tables_by_name.iteritems():
            print '    Processing: %s' % table_name

            for column in table_info['columns']:
                sql_type = SQL_TYPE_ONLY.findall(column['type'].lower())[0]
                column['type'] = {'bigint': 'long', 'datetime': 'datetime', 'decimal': 'float', 'varchar': 'basestring'}[sql_type]

        print 'Determining types, pass 2...'
        for table_name, table_info in tables_by_name.iteritems():
            print '    Processing: %s' % table_name

            for column in table_info['columns']:
                referenced_table_name = table_info['foreign_keys'].get(column['name'])
                if referenced_table_name is not None:
                    referenced_table_info = tables_by_name[referenced_table_name]
                    if referenced_table_info['is_enum']:
                        column['type'] = referenced_table_info['type_name']
                        table_info['custom_imports'].append('from %s import %s' % (column['type'], column['type']))
                    else:
                        referenced_table_info['columns'].append({
                            'name': table_name,
                            'type': table_info['type_name'],
                            'is_embeddable': False,
                            'is_single_cardinality': len(table_info['primary_keys']) == 1 and column['name'] in table_info['primary_keys']
                        })
                        referenced_table_info['custom_imports'].append('from %s import %s' % (table_info['type_name'], table_info['type_name']))

        generated_directory = 'generated'
        if os.path.exists(generated_directory):
            print 'The "%s" directory exists...emptying it...' % generated_directory
            #for generated_file in os.listdir(generated_directory):
            #    os.remove(os.path.join(generated_directory, generated_file))
        else:
            print 'The "%s" directory does not exist...creating it...' % generated_directory
            os.makedirs(generated_directory)

        print 'Writing Python types...'
        for table_name, table_info in tables_by_name.iteritems():
            type_name = table_info['type_name']

            print '    Writing "%s" as "%s"' % (table_name, type_name)

            if table_info['is_enum']:
                python_type = to_python_enum(conn, table_name, type_name)
            else:
                python_type = to_python_class(table_info)

            with open('%s/%s.py' % (generated_directory, type_name), 'w') as f:
                f.write(python_type)


SQL_TYPE_ONLY = re.compile('[a-z]*')


def execute(conn, sql):
    cursor = conn.cursor()
    cursor.execute(sql)
    return as_dicts(cursor)


def as_dicts(cursor):
    dicts = []
    for row in cursor.fetchall():
        row_dict = {}
        for index, column in enumerate(cursor.description):
            row_dict[column[0]] = row[index]
        dicts.append(row_dict)
    return dicts


def is_enum(table_name, columns):
    return table_name.endswith('_type') and len(columns) == 1 and table_name == columns[0]['name']


def to_python_enum(conn, table_name, type_name):
    enum_values = [record[0] for record in conn.execute('SELECT %s FROM %s' % (table_name, table_name))]

    python_enum = get_python_type_header()
    python_enum += 'class %s:\n' % type_name
    python_enum += '    __frozen = False\n'
    python_enum += '\n'
    for enum_value in enum_values:
        python_enum += '    %s = None\n' % enum_value.upper()
    python_enum += '\n'
    python_enum += '    def __init__(self, value):\n'
    python_enum += '        if %s.__frozen:\n' % type_name
    python_enum += '            raise AssertionError("New instances of %s can not be created!")\n' % type_name
    python_enum += '        self.__value = value\n'
    python_enum += '\n'
    python_enum += '    def __str__(self):\n'
    python_enum += '        return self.__value\n'
    python_enum += '\n'
    python_enum += '    @staticmethod\n'
    python_enum += '    def freeze():\n'
    python_enum += '        %s.__frozen = True\n' % type_name
    python_enum += '\n'
    python_enum += '\n'

    for enum_value in enum_values:
        python_enum += '%s.%s = %s("%s")\n' % (type_name, enum_value.upper(), type_name, enum_value)

    python_enum += '\n'
    python_enum += '%s.freeze()' % type_name

    return python_enum


def to_python_class(table_info):
    columns = table_info['columns']
    type_name = table_info['type_name']
    embeddable_columns = [column for column in columns if column['is_embeddable']]

    python_class = get_python_type_header()
    python_class += 'from datetime import datetime\n'
    python_class += '\n'
    python_class += 'from model.Freezeable import Freezeable\n'
    python_class += 'from model.typed_property import typed_property\n'
    for custom_import in table_info['custom_imports']:
        python_class += custom_import + '\n'
    python_class += '\n'
    python_class += '\n'
    python_class += 'class %s(Freezeable):\n' % type_name
    python_class += '    def __init__(self):\n'
    for column in columns:
        initial_value = 'None' if column['is_single_cardinality'] else '[]'
        python_class += '        self.__%s = %s\n' % (column['name'], initial_value)
    python_class += '        self._freeze()\n'
    python_class += '\n'
    python_class += '    def __str__(self):\n'
    python_class += '        return "' + type_name + '(' + columns_to_keys_str(embeddable_columns) + ')" % (' + columns_to_values_str(embeddable_columns) + ')\n'
    python_class += '\n'
    for column in columns:
        if column['is_single_cardinality']:
            python_class += '    @property\n'
            python_class += '    def %s(self):\n' % column['name']
            python_class += '        return self.__%s\n' % column['name']
            python_class += '\n'
            python_class += '    @%s.setter\n' % column['name']
            python_class += '    @typed_property(%s)\n' % column['type']
            python_class += '    def %s(self, %s):\n' % (column['name'], column['name'])
            python_class += '        self.__%s = %s\n' % (column['name'], column['name'])
            python_class += '\n'
        else:
            python_class += '    def %s(self):\n' % column['name']
            python_class += '        return list(self.__%s)\n' % column['name']
            python_class += '\n'
            python_class += '    @typed_property(%s)\n' % column['type']
            python_class += '    def add_%s(self, %s):\n' % (column['name'], column['name'])
            python_class += '        self.__%s.append(%s)\n' % (column['name'], column['name'])
            python_class += '\n'
            python_class += '    @typed_property(%s)\n' % column['type']
            python_class += '    def remove_%s(self, %s):\n' % (column['name'], column['name'])
            python_class += '        self.__%s.remove(%s)\n' % (column['name'], column['name'])
            python_class += '\n'

    return python_class


def columns_to_keys_str(columns):
    return ', '.join([c['name'] + ':%s' for c in columns])


def columns_to_values_str(columns):
    return ', '.join(['self.__' + c['name'] for c in columns])


def get_python_type_header():
    header = ''
    header += '# Do not edit this file by hand!\n'
    header += '# Change the data model, then regenerate the DDL, and then regenerate this model using the sql_to_python.py script!\n'
    header += '\n'
    header += '\n'
    return header


generate_model()