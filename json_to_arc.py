from pyld import jsonld
from arctrl.arctrl import JsonController
import json


def main():
    with open('/data/edal.json', 'r') as f:
        dataset = json.loads(f.read())

    with open('context/data_context.json', 'r') as f:
        context = json.loads(f.read())

    expanded = jsonld.expand(dataset)
    compacted = jsonld.compact(expanded, context)

    arc = JsonController.Investigation().from_json_string(compacted)


if __name__ == '__main__':
    main()
