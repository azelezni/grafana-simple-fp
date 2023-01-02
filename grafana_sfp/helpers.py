import argparse
import json


class KvDictAppendAction(argparse.Action):
    """
    argparse action to split an argument into KEY=VALUE form
    on the first = and append to a dictionary.
    """

    def __call__(self, parser, args, values, option_string=None):
        assert (len(values) == 1)
        try:
            (k, v) = values[0].split('=', 2)
        except ValueError:
            raise argparse.ArgumentError(self, f'could not parse argument "{values[0]}" as k=v format')
        d = getattr(args, self.dest) or {}
        d[k] = v
        setattr(args, self.dest, d)


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, 'value'):
            return obj.value
        else:
            return json.JSONEncoder.default(self, obj.__dict__)
