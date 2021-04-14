# Note: Previous linked list version is modified  by sending multiple parameters to create a node and creating
# different getters and setters as per the requirements.


# -*- coding: utf-8 -*-

# Copyright 2020 ICONation
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
from .id_factory import *


class EmptyLinkedListException(Exception):
    pass


class LinkedNodeNotFound(Exception):
    pass


class LinkedNodeAlreadyExists(Exception):
    pass


class _NodeDB:
    """ NodeDB is an item of the LinkedListDB
        Its structure is internal and shouldn't be manipulated outside of this module
    """
    _NAME = '_NODEDB'
    _UNINITIALIZED = 0
    _INITIALIZED = 1

    def __init__(self, var_key: str, db: IconScoreDatabase):
        self._name = var_key + _NodeDB._NAME
        self._init = VarDB(f'{self._name}_init', db, int)
        self._value = VarDB(f'{self._name}_value', db, int)
        self._key = VarDB(f'{self._name}_key', db, Address)
        self._block_height = VarDB(f'{self._name}_block_height', db, int)
        self._sender_address = VarDB(f'{self._name}_address', db, Address)
        self._next = VarDB(f'{self._name}_next', db, int)
        self._prev = VarDB(f'{self._name}_prev', db, int)
        self._db = db

    def delete(self) -> None:
        self._value.remove()
        self._key.remove()
        self._block_height.remove()
        self._sender_address.remove()
        self._prev.remove()
        self._next.remove()
        self._init.remove()

    def exists(self) -> bool:
        return self._init.get() != _NodeDB._UNINITIALIZED

    def get_value(self):
        return self._value.get()

    def get_key(self):
        return self._key.get()

    def get_block_height(self):
        return self._block_height.get()

    def get_sender_address(self):
        return self._sender_address.get()

    def set_value(self, _value: int) -> None:
        self._init.set(_NodeDB._INITIALIZED)
        self._value.set(_value)

    def set_key(self, _key: Address) -> None:
        self._init.set(_NodeDB._INITIALIZED)
        self._key.set(_key)

    def set_block_height(self, _block_height: int) -> None:
        self._init.set(_NodeDB._INITIALIZED)
        self._block_height.set(_block_height)

    def set_sender_address(self, _sender_address: Address) -> None:
        self._init.set(_NodeDB._INITIALIZED)
        self._sender_address.set(_sender_address)

    def get_next(self) -> int:
        return self._next.get()

    def set_next(self, next_id: int) -> None:
        self._next.set(next_id)

    def get_prev(self) -> int:
        return self._prev.get()

    def set_prev(self, prev_id: int) -> None:
        self._prev.set(prev_id)


class LinkedListDB:
    """ LinkedListDB is an iterable collection of items double linked by unique IDs.
        Order of retrieval is preserved.
        Circular linked listing or duplicates nodes in the same linkedlist is *not allowed*
        in order to prevent infinite loops.
    """

    _NAME = '_LINKED_LISTDB'

    def __init__(self, var_key: str, db: IconScoreDatabase):
        self._name = var_key + LinkedListDB._NAME
        self._head_id = VarDB(f'{self._name}_head_id', db, int)
        self._tail_id = VarDB(f'{self._name}_tail_id', db, int)
        self._length = VarDB(f'{self._name}_length', db, int)
        self._db = db

    def delete(self) -> None:
        self.clear()
        self._head_id.remove()
        self._tail_id.remove()
        self._length.remove()

    def __len__(self) -> int:
        return self._length.get()

    def __iter__(self):
        cur_id = self._head_id.get()

        # Empty linked list
        if not cur_id:
            return iter(())

        node = self._get_node(cur_id)
        yield cur_id, node.get_value(), node.get_key(), node.get_block_height(), node.get_sender_address()
        tail_id = self._tail_id.get()
        # Iterate until tail
        while cur_id != tail_id:
            cur_id = node.get_next()
            node = self._get_node(cur_id)
            yield cur_id, node.get_value(), node.get_key(), node.get_block_height(), node.get_sender_address()
            tail_id = self._tail_id.get()

    def _node(self, node_id) -> _NodeDB:
        return _NodeDB(str(node_id) + self._name, self._db)

    def _create_node(self, key: Address, value: int, block_height: int, sender_addres: Address,
                     node_id: int = None) -> tuple:
        if node_id is None:
            node_id = IdFactory(self._name + '_nodedb', self._db).get_uid()

        node = self._node(node_id)

        # Check if node already exists
        if node.exists():
            raise LinkedNodeAlreadyExists(self._name, node_id)

        node.set_value(value)
        node.set_key(key)
        node.set_block_height(block_height)
        node.set_sender_address(sender_addres)
        return node_id, node

    def _get_node(self, node_id: int) -> _NodeDB:
        node = self._node(node_id)
        if not node.exists():
            raise LinkedNodeNotFound(self._name, node_id)
        return node

    def _get_tail_node(self) -> _NodeDB:
        tail_id = self._tail_id.get()
        if not tail_id:
            raise EmptyLinkedListException(self._name)
        return self._get_node(tail_id)

    def clear(self) -> None:
        """ Delete all nodes from the linkedlist """
        cur_id = self._head_id.get()
        if not cur_id:
            # Empty list
            return

        node = self._get_node(cur_id)
        tail_id = self._tail_id.get()

        # Iterate until tail
        while cur_id != tail_id:
            cur_id = node.get_next()
            # We're done with this node
            node.delete()
            # Iterate to the next node
            node = self._get_node(cur_id)

        # Delete the last node
        node.delete()

        self._tail_id.remove()
        self._head_id.remove()
        self._length.set(0)

    def update_node(self, key: Address, value: int, block_height: int, sender_address: Address, node_id: int):
        node = self._node(node_id)
        if node.exists():
            node.set_value(value)
            node.set_key(key)
            node.set_block_height(block_height)
            node.set_sender_address(sender_address)
        else:
            revert(f'There is no node of the provided node id.')

    def append(self, key: Address, value: int, block_height: int, sender_address: Address, node_id: int = None) -> int:
        """ Append an element at the end of the linkedlist """
        cur_id, cur = self._create_node(key, value, block_height, sender_address, node_id)
        if self._length.get() == 0:
            # Empty LinkedList
            self._head_id.set(cur_id)
            self._tail_id.set(cur_id)
        else:
            # Append to tail
            tail = self._get_tail_node()
            tail.set_next(cur_id)
            cur.set_prev(self._tail_id.get())
            # Update tail to cur node
            self._tail_id.set(cur_id)

        self._length.set(self._length.get() + 1)

        return cur_id

    def remove_head(self) -> None:
        """ Remove the current head from the linkedlist """
        if self._length.get() == 1:
            self.clear()
        else:
            old_head = self._get_node(self._head_id.get())
            new_head = old_head.get_next()
            self._head_id.set(new_head)
            self._get_node(new_head).set_prev(0)
            old_head.delete()
            self._length.set(self._length.get() - 1)

    def remove_tail(self) -> None:
        """ Remove the current tail from the linkedlist """
        if self._length.get() == 1:
            self.clear()
        else:
            old_tail = self._get_node(self._tail_id.get())
            new_tail = old_tail.get_prev()
            self._tail_id.set(new_tail)
            self._get_node(new_tail).set_next(0)
            old_tail.delete()
            self._length.set(self._length.get() - 1)

    def remove(self, cur_id: int) -> None:
        """ Remove a given node from the linkedlist """
        if cur_id == self._head_id.get():
            self.remove_head()

        elif cur_id == self._tail_id.get():
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
            self._length.set(self._length.get() - 1)
