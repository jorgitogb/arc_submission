import json
from pyld import jsonld


def main():
    with open('data/edal.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Assuming the JSON-LD document is the first element of the data list
    dataset = data[0]['author'][0]
    #print(dataset)
    expanded = jsonld.expand(dataset, False)
    print(json.dumps(expanded, indent=2))


if __name__ == '__main__':
    main()
