# -*- coding: utf-8 -*-

# Copyright 2021 BalancedDAO
#
# Modified from the original ICONation LinkedList implementation.
# 1. Serialization of data in each node and metadata for the list in order to
#    reduce database reads and writes.
# 2. IdFactory removed. This version relies on external tracking to maintain
#    unique node IDs.
# 3. Methods not necessary for Balanced were removed.
# 4. __setitem__ and __getitem__ methods were introduced to allow for key
#    access to individual nodes.
#
# Original work Copyright 2020 ICONation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from iconservice import *


class EmptyLinkedListException(Exception):
    pass


class LinkedNodeAlreadyExists(Exception):
    pass


class LinkedNodeCannotMoveItself(Exception):
    pass


class _Node:
    """ A Node is an item of the LinkedListDB. Its structure is
        internal and shouldn't be manipulated outside of this module.
    """

    _NAME = '_Node'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):
        self._db = db
        self._value_type = value_type
        self._name = var_key + _Node._NAME
        self._node_data = VarDB(f'{self._name}_node_data', db, str)
        self._data_string = ""
        self._value = None
        self._next = 0
        self._prev = 0
        self.unpack()

    ######### LinkedListDB 2.0 Compatibility Layer #########
    def serialize_value(self) -> str:
        if self._value_type == int:
            return str(self._value)
        if self._value_type == str:
            return self._value
        elif self._value_type == Address:
            return str(self._value)
        elif self._value_type == bytes:
            return self._value.hex()
        else:
            raise NotImplementedError(f"Invalid type {self._value_type}")

    @staticmethod
    def deserialize_value(value: str, value_type: type):
        if value_type == int:
            return int(value)
        if value_type == str:
            return value
        elif value_type == Address:
            return Address.from_string(value)
        elif value_type == bytes:
            return bytes.fromhex(value)
        else:
            raise NotImplementedError(f"Invalid type {value_type}")

    def unpack(self) -> None:
        self._data_string = self._node_data.get()
        if self._data_string != "":
            nodedata = self._data_string.split('|')
            self._value = self.deserialize_value(nodedata[0], self._value_type)
            self._next = int(nodedata[1])
            self._prev = int(nodedata[2])

    def repack(self) -> None:
        nodedata = [self.serialize_value(), str(self._next), str(self._prev)]
        self._node_data.set('|'.join(nodedata))

    @staticmethod
    def default_value(value_type: type):
        if value_type == int:
            return 0
        if value_type == str:
            return ""
        elif value_type == Address:
            return None
        elif value_type == bytes:
            return b''
        else:
            raise NotImplementedError(f"Invalid type {value_type}")

    ######### LinkedListDB 1.0 Methods #########

    def delete(self) -> None:
        self._node_data.remove()

    def exists(self) -> bool:
        return self._data_string != ""

    def get_value(self):
        return self._value

    def set_value(self, value) -> None:
        self._value = value

    def get_next(self) -> int:
        return self._next

    def set_next(self, next_id: int) -> None:
        self._next = next_id

    def get_prev(self) -> int:
        return self._prev

    def set_prev(self, prev_id: int) -> None:
        self._prev = prev_id


class LinkedListDB:
    """ LinkedListDB is an iterable collection of items double linked by unique IDs.
        Order of retrieval is preserved.
        Circular linked listing or duplicates nodes in the same linkedlist is *not allowed*
        in order to prevent infinite loops.
    """

    _NAME = '_LINKED_LISTDB'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):
        self._db = db
        self.__cachedb = {}
        self._value_type = value_type
        self._name = var_key + LinkedListDB._NAME
        self._metadata = VarDB(f'{self._name}_metadata', db, str)
        self._data_string = ""
        self._head_id = 0
        self._tail_id = 0
        self._length = 0
        self.__deserialize()

    ######### LinkedListDB 2.0 Method #########
    def __deserialize(self) -> None:
        self._data_string = self._metadata.get()
        if self._data_string != "":
            metadata = self._data_string.split('|')
            self._head_id = int(metadata[0])
            self._tail_id = int(metadata[1])
            self._length = int(metadata[2])

    def reload(self) -> None:
        self.__deserialize()

    def serialize(self) -> None:
        metadata = [str(self._head_id), str(self._tail_id), str(self._length)]
        new_data_string = '|'.join(metadata)
        if new_data_string != self._data_string:
            self._metadata.set(new_data_string)

    ######### LinkedListDB 1.0 Methods #########
    def delete(self) -> None:
        self.clear()
        self._metadata.remove()

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, node_id: int):
        return self._get_node(node_id).get_value()

    def __setitem__(self, key: int, value):
        node = self._get_node(key)
        node.set_value(value)
        node.repack()

    def __contains__(self, node_id: int) -> bool:
        node = self._node(node_id)
        return node.exists()

    def _node(self, node_id) -> _Node:
        return _Node(str(node_id) + self._name, self._db, self._value_type)

    def _create_node(self, value, node_id: int) -> tuple:
        node = self._node(node_id)

        # Check if node already exists
        if node.exists():
            raise LinkedNodeAlreadyExists(self._name, node_id)

        node.set_value(value)
        node.repack()
        return node_id, node

    def set_node_value(self, value, node_id: int) -> None:
        node = self._get_node(node_id)
        node.set_value(value)
        node.repack()

    def _get_node(self, node_id: int) -> _Node:
        if node_id not in self.__cachedb:
            node = self._node(node_id)
            self.__cachedb[node_id] = node
        node = self.__cachedb[node_id]
        if not node.exists():
            self._append(node_id)
        return node

    def _get_tail_node(self) -> _Node:
        node_id = self._tail_id
        if not node_id:
            raise EmptyLinkedListException(self._name)
        if node_id not in self.__cachedb:
            node = self._get_node(node_id)
            self.__cachedb[node_id] = node
        return self.__cachedb[node_id]

    def node_value(self, cur_id: int):
        """ Returns the value of a given node id """
        if cur_id not in self.__cachedb:
            node = self._get_node(cur_id)
            self.__cachedb[cur_id] = node
        return self.__cachedb[cur_id].get_value()

    def get_head_id(self) -> int:
        return self._head_id

    def get_tail_id(self) -> int:
        return self._tail_id

    def head_value(self):
        """ Returns the value of the head of the linkedlist """
        return self.node_value(self._head_id)

    def tail_value(self):
        """ Returns the value of the tail of the linkedlist """
        return self.node_value(self._tail_id)

    def next(self, cur_id: int) -> int:
        """ Get the next node id from a given node
            Raises StopIteration if it doesn't exist """
        if cur_id not in self.__cachedb:
            node = self._get_node(cur_id)
            self.__cachedb[cur_id] = node
        next_id = self.__cachedb[cur_id].get_next()
        if not next_id:
            raise StopIteration(self._name)
        return next_id

    def get_next_ro(self, cur_id: int) -> int:
        cur = self._node(cur_id)
        return cur.get_next()

    def get_prev_ro(self, cur_id: int) -> int:
        cur = self._node(cur_id)
        return cur.get_prev()

    def get_metadata(self) -> str:
        return self._metadata.get()

    def clear(self) -> None:
        # Delete all nodes from the linkedlist
        cur_id = self._head_id
        if not cur_id:
            # Empty list
            return

        node = self._get_node(cur_id)
        tail_id = self._tail_id

        # Iterate until tail
        while cur_id != tail_id:
            cur_id = node.get_next()
            # We're done with this node
            node.delete()
            # Iterate to the next node
            node = self._get_node(cur_id)

        # Delete the last node
        node.delete()

        self._tail_id = 0
        self._head_id = 0
        self._length = 0
        self.serialize()

    def append(self, value, node_id: int = None) -> int:
        """ Append an element at the end of the linkedlist """
        cur_id, cur = self._create_node(value, node_id)
        self.__cachedb[cur_id] = cur
        return self._append(cur_id)

    def _append(self, cur_id: int = None) -> int:
        """ Append an existing node at the end of the linkedlist """
        cur = self.__cachedb[cur_id]

        if self._length == 0:
            # Empty LinkedList
            self._head_id = cur_id
            self._tail_id = cur_id
            self._length = self._length + 1
            self.serialize()
        else:
            # Append to tail
            tail = self._get_tail_node()
            tail.set_next(cur_id)
            tail.repack()
            cur.set_prev(self._tail_id)
            cur.repack()
            # Update tail to cur node
            self._tail_id = cur_id
            self._length = self._length + 1
            self.serialize()

        return cur_id

    def move_head_to_tail(self) -> None:
        self.move_node_tail(self._head_id)

    def move_node_tail(self, cur_id: int) -> None:
        """ Move an existing node to the tail of the linkedlist """

        cur = self._get_node(cur_id)
        tail = self._get_node(self._tail_id)
        curprev_id = cur.get_prev()
        # cur may be the head
        if curprev_id:
            curprev = self._get_node(curprev_id)
        curnext_id = cur.get_next()
        curnext = self._get_node(curnext_id)

        if cur_id == self._head_id:
            self._head_id = curnext_id

        # curprev>nid
        if curprev_id:
            curprev.set_next(curnext_id)
            curprev.repack()
        # curnext>pid
        curnext.set_prev(curprev_id)
        curnext.repack()
        # tail>nid
        tail.set_next(cur_id)
        # cur>pid
        cur.set_prev(self._tail_id)
        cur.set_next(0)
        # update tail
        self._tail_id = cur_id
        tail.repack()
        cur.repack()

    def remove_head(self) -> None:
        """ Remove the current head from the linkedlist """
        if self._length == 1:
            self.clear()
        else:
            old_head = self._get_node(self._head_id)
            new_head = old_head.get_next()
            self._head_id = new_head
            head = self._get_node(new_head)
            head.set_prev(0)
            old_head.delete()
            self._length = self._length - 1
            head.repack()

    def remove_tail(self) -> None:
        """ Remove the current tail from the linkedlist """
        if self._length == 1:
            self.clear()
        else:
            old_tail = self._get_node(self._tail_id)
            new_tail = old_tail.get_prev()
            self._tail_id = new_tail
            tail = self._get_node(new_tail)
            tail.set_next(0)
            old_tail.delete()
            self._length = self._length - 1
            tail.repack()

    def remove(self, cur_id: int) -> None:
        """ Remove a given node from the linkedlist """
        if cur_id == self._head_id:
            self.remove_head()

        elif cur_id == self._tail_id:
            self.remove_tail()

        else:
            cur = self._get_node(cur_id)
            curnext_id = cur.get_next()
            curnext = self._get_node(curnext_id)
            curprev_id = cur.get_prev()
            curprev = self._get_node(curprev_id)
            curnext.set_prev(curprev_id)
            curprev.set_next(curnext_id)
            cur.delete()
            self._length = self._length - 1
            curnext.repack()
            curprev.repack()
        self.serialize()
