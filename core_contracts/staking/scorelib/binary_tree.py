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


class TreeNodeAlreadyExists(Exception):
    pass


class TreeNodeNotFound(Exception):
    pass


class _BinaryTreeNode:
    """ __BinaryTreeNode is an item of the BinaryTreeDB
        Its structure is internal and shouldn't be manipulated outside of this module
    """
    _NAME = '_BINARY_TREE_NODE'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):
        name = var_key + _BinaryTreeNode._NAME
        self._name = var_key + _BinaryTreeNode._NAME
        self._init = VarDB(f'{self._name}_init', db, int)
        self._value = VarDB(f'{self._name}_value', db, value_type)
        self._left = VarDB(f'{self._name}_left', db, int)
        self._right = VarDB(f'{self._name}_right', db, int)
        self._db = db

    def __delete__(self) -> None:
        self._value.remove()
        self._left.remove()
        self._right.remove()
        self._init.remove()

    def set_left(self, node_id: int) -> None:
        self._left.set(node_id)

    def set_right(self, node_id: int) -> None:
        self._right.set(node_id)

    def get_children(self) -> tuple:
        return self._left.get(), self._right.get()

    def get_value(self):
        return self._value.get()

    def exists(self) -> bool:
        return self._init.get() == 1

    def set_value(self, value: type) -> None:
        self._init.set(1)
        self._value.set(value)


class BinaryTreeDB:
    """
    BinaryTreeDB is a tree data structure in which each node has at most two children,
    which are referred to as the left child and the right child.
    """

    _NAME = '_BINARY_TREE'

    def __init__(self, var_key: str, db: IconScoreDatabase, value_type: type):
        name = var_key + BinaryTreeDB._NAME
        self._value_type = value_type
        self._name = name
        self._db = db

    def _node(self, node_id) -> _BinaryTreeNode:
        return _BinaryTreeNode(str(node_id) + self._name, self._db, self._value_type)

    def _create_node(self, value, node_id: int = None) -> _BinaryTreeNode:
        if node_id is None:
            node_id = IdFactory(self._name + '_node', self._db).get_uid()

        node = self._node(node_id)

        # Check if node already exists
        if node.exists():
            raise TreeNodeAlreadyExists(self._name, node_id)

        node.set_value(value)
        return (node_id, node)

    def create_node(self, value, node_id: int = None) -> int:
        node_id, node = self._create_node(value, node_id)
        return node_id

    def set_left_child(self, node_parent_id: int, node_left_id: int) -> None:
        parent = self._node(node_parent_id)
        if not parent.exists():
            raise TreeNodeNotFound(self._name, node_parent_id)

        left = self._node(node_left_id)
        if not left.exists():
            raise TreeNodeNotFound(self._name, node_left_id)

        parent.set_left(node_left_id)

    def set_right_child(self, node_parent_id: int, node_right_id: int) -> None:
        parent = self._node(node_parent_id)
        if not parent.exists():
            raise TreeNodeNotFound(self._name, node_parent_id)

        right = self._node(node_right_id)
        if not right.exists():
            raise TreeNodeNotFound(self._name, node_right_id)

        parent.set_right(node_right_id)

    def get_node_value(self, node_id: int):
        node = self._node(node_id)
        return node.get_value()

    def get_children(self, node_id: int) -> tuple:
        node = self._node(node_id)
        return node.get_children()

    def traverse_post_order(self, node_id: int, callback, **kwargs) -> None:
        node = self._node(node_id)
        if not node.exists():
            return

        left, right = node.get_children()
        self.traverse_post_order(left, callback, **kwargs)
        self.traverse_post_order(right, callback, **kwargs)
        callback(self._db, node_id, **kwargs)

    def traverse_in_order(self, node_id: int, callback, **kwargs) -> None:
        node = self._node(node_id)
        if not node.exists():
            return

        left, right = node.get_children()
        self.traverse_in_order(left, callback, **kwargs)
        callback(self._db, node_id, **kwargs)
        self.traverse_in_order(right, callback, **kwargs)

    def traverse_pre_order(self, node_id: int, callback, **kwargs) -> None:
        node = self._node(node_id)
        if not node.exists():
            return

        callback(self._db, node_id, **kwargs)

        left, right = node.get_children()
        self.traverse_pre_order(left, callback, **kwargs)
        self.traverse_pre_order(right, callback, **kwargs)
