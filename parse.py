"""
Преобразовать XML файл в файловую структуру (папки, *.txt файлы) для последующей загрузки в GIT,
так как изначальный файл велик и сложно читаем глазами. Кроме того, требуется обеспечить независимость
от перестановки неименованых узлов (не должно восприниматься как различие).

Принцип преобразования состоит в том, что узлы приобразуются к каталогам,
а дочерние узлы к вложенным каталогам. Свойства узлов записываются в файле body.txt и помещаются
в соответствующий узлу каталог. Финальные узлы (не имеющие дочерних узлов) записываются аналогично свойствам - в файл
body.txt.
Так как файл с изначальными данными содержит наборы неименованых узлов (узлы с именем 'row', принадлежащие одному
родителю), реализована возможность именования узлов, опираясь на данные вложенных узлов. Приоритеты именования указаны
в списке nodeNames. Для ряда узлов реализовна возможность именования по нескольким ключевым полям. Для этого реализованы
соответствующие функции:
parse_recipients_sets
rename_recipients_sets
parse_named_algorithms
parse_rules_discharge_objects
parse_rules_loading_objects
"""

import os
import xmltodict
from collections import OrderedDict
from util.variables import nodeNames, rules_xml, result
from sys import argv
import re


def path(*args):
    return os.path.join(*args)


def xml_to_files(xml_file, result_dir, rename_recipients=False):
    with open(xml_file, 'r', encoding='utf-8') as f:
        data_dict = xmltodict.parse(f.read())
    parse_node_to_file_structure(data_dict, result_dir)
    if rename_recipients:
        rename_recipients_sets()


"""
parse_node_to_file_structure
Функция принимает узел и выполняет обход всех его дочерних узлов.
Дочерние узлы помещаются в child_nodes и передаются на следующий уровени рекурсии
Неименованые узлы (имеющие неуникальное имя) именуются на основании вложенных данных и передаются на следующий уровень
рекурсии
Узлы нижнего уровня записываются в body.txt
"""

def parse_node_to_file_structure(node: OrderedDict, work_dir=os.getcwd()):
    child_nodes = []
    list_nodes = []
    body = ''

    for key in node.keys():
        if isinstance(node[key], str):
            body += f'{key} : {node[key]}\n'
        elif isinstance(node[key], OrderedDict):
            child_nodes.append(key)
        elif isinstance(node[key], list):
            list_nodes.append(key)

    if body:
        body_file = path(work_dir, 'body.txt')
        with open(body_file, 'w', encoding='utf-8') as f:
            f.writelines(body)

    if len(child_nodes):
        for item in child_nodes:
            child_node_path = path(work_dir, item)
            os.mkdir(child_node_path)

            # Обеспечение спецефического именования ряда неименованых узлов
            if work_dir == 'data\\classData':
                if item == 'НаборыПолучателей':
                    parse_recipients_sets(node[item], child_node_path)
                    continue
                elif item == 'ИменованныеАлгоритмы':
                    parse_named_algorithms(node[item], child_node_path)
                    continue
                elif item == 'ПравилаВыгрузкиОбъектов':
                    parse_rules_discharge_objects(node[item], child_node_path)
                    continue
                elif item == 'ПравилаЗагрузкиОбъектов':
                    parse_rules_loading_objects(node[item], child_node_path)
                    continue

            parse_node_to_file_structure(node[item], child_node_path)

    if len(list_nodes):
        for list_node in list_nodes:
            list_node_path = path(work_dir, list_node)
            os.mkdir(list_node_path)
            for item in node[list_node]:
                for testNodeName in nodeNames:
                    if testNodeName in item.keys() and isinstance(item[testNodeName], str):
                        child_node_path = path(list_node_path, item[testNodeName])
                        os.mkdir(child_node_path)
                        parse_node_to_file_structure(item, child_node_path)
                        break


def parse_recipients_sets(node: OrderedDict, work_dir=os.getcwd()):
    for item in node['row']:
        child_node_path = path(work_dir, item['Наименование'])
        os.mkdir(child_node_path)
        parse_node_to_file_structure(item, child_node_path)


def parse_named_algorithms(node: OrderedDict, work_dir):
    for item in node['row']:
        child_node_path = path(work_dir, item['ИмяАлгоритма'])
        os.mkdir(child_node_path)
        parse_node_to_file_structure(item, child_node_path)


def parse_rules_discharge_objects(node: OrderedDict, work_dir):
    for item in node['row']:
        child_node_path = path(work_dir, item['ТипОбъекта'])
        os.mkdir(child_node_path)
        parse_node_to_file_structure(item, child_node_path)


def parse_rules_loading_objects(node: OrderedDict, work_dir):
    for item in node['row']:
        child_node_path = path(work_dir, f'{item["НаборПолучателей"]} - '
                                         f'{item["ТипОбъектаИсточника"]} - '
                                         f'{item["ТипОбъекта"]}')
        os.mkdir(child_node_path)
        parse_node_to_file_structure(item, child_node_path)


def rename_recipients_sets():
    work_dir = path(os.getcwd(), 'data', 'classData', 'ПравилаЗагрузкиОбъектов')
    recipients_dir = path(os.getcwd(), 'data', 'classData', 'НаборыПолучателей')
    recipients = {}
    pattern = re.compile('.*Ссылка : (.+)\n.*')
    for item in os.listdir(recipients_dir):
        body_file = path(recipients_dir, item, 'body.txt')
        with open(body_file, 'r', encoding='utf-8') as f:
            text = ''.join(f.readlines())
            if pattern.findall(text):
                recipients[pattern.findall(text)[0]] = item

    pattern = re.compile('(\w+-\w+-\w+-\w+-\w+) - .+ - .+')
    for item in os.listdir(work_dir):
        if pattern.findall(item):
            os.rename(path(work_dir, item),
                      path(work_dir, item.replace(pattern.findall(item)[0], recipients[pattern.findall(item)[0]])))


if __name__ == '__main__':
    if len(argv) == 2:
        script, rules_xml = argv
        rules_xml = path(rules_xml)
    elif len(argv) > 3:
        script, rules_xml, result = argv
        rules_xml = path(rules_xml)
        result = path(result)
    xml_to_files(rules_xml, result, rename_recipients=False)
