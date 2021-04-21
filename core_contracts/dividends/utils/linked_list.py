
from iconservice import *


class NodeUtil:

    @staticmethod
    def encode_data(value, value_type: type) -> str:
        if value_type == int:
            return str(value)
        elif value_type == str:
            return value
        elif value_type == Address:
            return str(value)
        elif value_type == bytes:
            return value.hex()
        else:
            revert("Error while encoding data in linked list")

    @staticmethod
    def decode_data(value: str, value_type: type):
        if value_type == int:
            return int(value)
        elif value_type == str:
            return value
        elif value_type == Address:
            return Address.from_string(value)
        elif value_type == bytes:
            return bytes.fromhex(value)
        else:
            revert("Error while decoding data in linked list")

    @staticmethod
    def get_default_value(value_type: type):
        if value_type == int:
            return 0
        elif value_type == str:
            return ""
        elif value_type == Address:
            return None
        elif value_type == bytes:
            return b''
        else:
            revert(f"Invalid type to return default value {value_type}")


class Node:

    _NODE_KEY = "node_data_key"

    def __init__(self,
                 var_key: str,
                 db: IconScoreDatabase,
                 value_type: type) -> None:
        # Basic components of a node in double linked list
        self.__value = NodeUtil.get_default_value(value_type)
        self.__next = ""
        self.__prev = ""

        # required db components to store variables in vardb
        self._db = db
        self.__value_type = value_type
        self.__data_db = VarDB(f'{var_key}_{self._NODE_KEY}', db, str)
        self.load_from_db()

    def load_from_db(self) -> None:
        data_in_str = self.__data_db.get()
        if data_in_str != "":
            node = data_in_str.split('|')
            self.__value = NodeUtil.decode_data(node[0], self.__value_type)
            self.__next = node[1]
            self.__prev = node[2]

    def save_to_db(self) -> None:
        encoded_data = NodeUtil.encode_data(self.__value, self.__value_type)
        if ("|" in encoded_data) or ("|" in self.__next) or ("|" in self.__prev):
            revert("Illegal character in data or next or previous key")
        node = [encoded_data, self.__next, self.__prev]
        self.__data_db.set('|'.join(node))

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value
        self.save_to_db()

    @property
    def next_(self):
        return self.__next

    @next_.setter
    def next_(self, next_):
        self.__next = next_
        self.save_to_db()

    @property
    def prev(self):
        return self.__prev

    @prev.setter
    def prev(self, prev):
        self.__prev = prev
        self.save_to_db()

    # Remove from DB
    def remove(self):
        self.__data_db.remove()

    # Check if data exists in db
    def exists(self) -> bool:
        return self.__data_db.get() != ""


class LinkedListDB:

    _LINKED_LIST_KEY = "linked_list_key"

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):

        self.__head = ""
        self.__tail = ""
        self.__length: int = 0

        self._db = db
        self.__value_type = value_type
        self.__composite_key = f"{var_key}_{self._LINKED_LIST_KEY}"
        self.__metadata_db = VarDB(self.__composite_key, db, str)
        self.__metadata = ""

    def load_metadata(self) -> None:
        self.__metadata = self.__metadata_db.get()
        if self.__metadata != "":
            metadata = self.__metadata.split('|')
            self.__head = metadata[0]
            self.__tail = metadata[1]
            self.__length = int(metadata[2])

    def save_metadata(self) -> None:
        if ('|' in self.__head) or ('|' in self.__tail):
            revert("Illegal character in head or tail")
        metadata = [self.__head, self.__tail, str(self.__length)]
        updated_metadata = '|'.join(metadata)
        if updated_metadata != self.__metadata:
            self.__metadata_db.set(updated_metadata)

    def append(self, node_key, node_value):
        self.load_metadata()
        new_node = self.get_node(node_key)

        # Do not allow duplicate items, as the key is used to index the values
        if new_node.exists():
            revert(f"Item already exists in linked list {self.__composite_key}")

        new_node.value = node_value

        if self.__length == 0:
            self.__head = node_key
            self.__tail = node_key

        else:
            tail = self.get_node(self.__tail)
            tail.next_ = node_key
            tail.save_to_db()

            new_node.prev = self.__tail
            self.__tail = node_key

        self.__length = self.__length + 1
        new_node.value = node_value
        new_node.save_to_db()
        self.save_metadata()

    def get_node(self, node_key: str) -> Node:
        return Node(node_key+self.__composite_key, self._db, self.__value_type)

    def remove(self, node_key):
        self.load_metadata()

        node_to_delete = self.get_node(node_key)
        if not node_to_delete.exists():
            return

        if node_key == self.__head:
            self.__head = node_to_delete.next_
            next_node = self.get_node(self.__head)
            next_node.prev = NodeUtil.get_default_value(self.__value_type)
            node_to_delete.remove()
            next_node.save_to_db()

        elif node_key == self.__tail:
            self.__tail = node_to_delete.prev
            prev_node = self.get_node(self.__tail)
            prev_node.next_ = NodeUtil.get_default_value(self.__value_type)
            node_to_delete.remove()
            prev_node.save_to_db()

        else:
            prev_node = self.get_node(node_to_delete.prev)
            next_node = self.get_node(node_to_delete.next_)

            prev_node.next_ = node_to_delete.next_
            next_node.prev = node_to_delete.prev

            prev_node.save_to_db()
            next_node.save_to_db()

        self.__length = self.__length - 1
        self.save_metadata()

    def __len__(self) -> int:
        self.load_metadata()
        return self.__length

    def __getitem__(self, node_key: str):
        node = self.get_node(node_key)
        return node.value

    def __setitem__(self, key, value):
        node = self.get_node(key)
        if not node.exists():
            self.append(key, value)
        else:
            node.value = value
        node.save_to_db()

    @property
    def head(self):
        self.load_metadata()
        return self.__head

    @property
    def tail(self):
        self.load_metadata()
        return self.__tail
