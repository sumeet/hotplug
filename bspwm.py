import json
import subprocess


class Bspwm:

    @classmethod
    def monitors(cls):
        monitor_names = cls._query_monitor_names()
        return [cls._query_monitor(name) for name in monitor_names]

    @classmethod
    def set_desktop_layout(cls, monitor, monitor_names):
        cls._run('monitor', monitor.name, '-d', *monitor_names)

    @classmethod
    def set_monitor_padding(cls, monitor, padding_amount):
        cls._run('config', '-m', monitor.name, 'top_padding', str(padding_amount))

    @classmethod
    def send_to_monitor(cls, node, monitor_name):
        cls._run('node', str(node.id), '-m', monitor_name)

    @classmethod
    def remove_monitor(cls, monitor_name):
        cls._run('monitor', monitor_name, '-r')

    @classmethod
    def _query_monitor(cls, monitor_name):
        output = cls._run('query', '-T', '-m', monitor_name)
        return Monitor(json.loads(output))

    @classmethod
    def _query_monitor_names(cls):
        output = cls._run('query', '-M', '--names')
        return [line.strip() for line in output.splitlines()]

    @classmethod
    def _run(cls, *args):
        print(f'running bspc {args}')
        return subprocess.run(['bspc'] + list(args),
                              stdout=subprocess.PIPE).stdout.decode('utf-8').strip()


class Monitor:

    def __init__(self, raw_output):
        self._raw_output = raw_output

    def __repr__(self):
        return f'<Monitor {self.name}>'

    @property
    def name(self):
        return self._raw_output['name']

    # TODO: should we differentiates windows in different screens? maybe we
    # attach the desktop number or name with the screen, for now we're just
    # focused on moving the screens, can deal with sorting them later
    @property
    def windows(self):
        for desktop in self._raw_output['desktops']:
            if not desktop['root']:
                continue
            root = Node(desktop['root'])
            if root.is_window:
                yield root
            for child in root.all_children:
                if child.is_window:
                    yield child


# a node is what bspwm calls a window
class Node:

    def __init__(self, raw_output, parent=None):
        self._raw_output = raw_output
        self.parent = parent

    def __repr__(self):
        return f'<Node is_window: {self.is_window}, class_name: {self.class_name}>'

    @property
    def is_window(self):
        # bspwm nodes are either structural (no window associated with them,
        # they are hierarchical parents of others) or actually contain windows.
        return self._raw_output['client'] != None


    # typically the name of the app, formatted. i.e., "Ripcord" vs "ripcord"
    @property
    def class_name(self):
        if not self.is_window:
            return None
        return self._raw_output['client']['className']

    @property
    def is_private(self):
        return self._raw_output['private']

    @property
    def id(self):
        return self._raw_output['id']

    @property
    def first_child(self):
        if self._raw_output['firstChild']:
            return Node(self._raw_output['firstChild'], parent=self)
        return None

    @property
    def second_child(self):
        if self._raw_output['secondChild']:
            return Node(self._raw_output['secondChild'], parent=self)
        return None

    @property
    def all_children(self):
        first_child = self.first_child
        if first_child:
            yield first_child
            for child in first_child.all_children:
                yield child

        second_child = self.second_child
        if second_child:
            yield second_child
            for child in second_child.all_children:
                yield child

    def find_node(self, node_id):
        if self.id == node_id:
            return self
        if self.first_child:
            node = self.first_child.find_node(node_id)
            if node:
                return node
        if self.second_child:
            node = self.second_child.find_node(node_id)
            if node:
                return node
