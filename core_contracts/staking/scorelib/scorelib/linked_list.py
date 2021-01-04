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
from .consts import *


class EmptyLinkedListException(Exception):
    pass


class LinkedNodeNotFound(Exception):
    pass


class LinkedNodeAlreadyExists(Exception):
    pass


class LinkedNodeCannotMoveItself(Exception):
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
        self._next = VarDB(f'{self._name}_next', db, int)
        self._prev = VarDB(f'{self._name}_prev', db, int)
        self._db = db

    def delete(self) -> None:
        self._value.remove()
        self._key.remove()
        self._prev.remove()
        self._next.remove()
        self._init.remove()

    def exists(self) -> bool:
        return self._init.get() != _NodeDB._UNINITIALIZED

    def get_value(self):
        return self._value.get()

    def get_key(self):
        return self._key.get()

    def set_value(self, _value : int) -> None:
        self._init.set(_NodeDB._INITIALIZED)
        self._value.set(_value)

    def set_key(self, _key : Address) -> None:
        self._init.set(_NodeDB._INITIALIZED)
        self._key.set(_key)

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
        yield cur_id, node.get_value(),node.get_key()
        tail_id = self._tail_id.get()

        # Iterate until tail
        while cur_id != tail_id:
            cur_id = node.get_next()
            node = self._get_node(cur_id)
            yield cur_id, node.get_value(), node.get_key()
            tail_id = self._tail_id.get()

    def _node(self, node_id) -> _NodeDB:
        return _NodeDB(str(node_id) + self._name, self._db)

    def _create_node(self, key : Address, value: int, node_id: int = None) -> tuple:
        if node_id is None:
            node_id = IdFactory(self._name + '_nodedb', self._db).get_uid()

        node = self._node(node_id)

        # Check if node already exists
        if node.exists():
            raise LinkedNodeAlreadyExists(self._name, node_id)

        node.set_value(value)
        node.set_key(key)
        return (node_id, node)

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

    def _get_head_node(self) -> _NodeDB:
        head_id = self._head_id.get()
        if not head_id:
            raise EmptyLinkedListException(self._name)
        return self._get_node(head_id)

    def node_value(self, cur_id: int):
        """ Returns the value of a given node id """
        return self._get_node(cur_id).get_value()

    def head_value(self):
        """ Returns the value of the head of the linkedlist """
        return self.node_value(self._head_id.get())

    def tail_value(self):
        """ Returns the value of the tail of the linkedlist """
        return self.node_value(self._tail_id.get())

    def next(self, cur_id: int) -> int:
        """ Get the next node id from a given node
            Raises StopIteration if it doesn't exist """
        node = self._get_node(cur_id)
        next_id = node.get_next()
        if not next_id:
            raise StopIteration(self._name)
        return next_id

    def prev(self, cur_id: int) -> int:
        """ Get the next node id from a given node
            Raises StopIteration if it doesn't exist """
        node = self._get_node(cur_id)
        prev_id = node.get_prev()
        if not prev_id:
            raise StopIteration(self._name)
        return prev_id

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

    def append(self,key : Address, value : int, node_id: int = None) -> int:
        """ Append an element at the end of the linkedlist """
        cur_id, cur = self._create_node(key, value, node_id)
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

    def prepend(self, value, node_id: int = None) -> int:
        """ Prepend an element at the beginning of the linkedlist """
        cur_id, cur = self._create_node(value, node_id)

        if self._length.get() == 0:
            # Empty LinkedList
            self._head_id.set(cur_id)
            self._tail_id.set(cur_id)
        else:
            # Prepend to head
            head = self._get_head_node()
            head.set_prev(cur_id)
            cur.set_next(self._head_id.get())
            # Update head to cur node
            self._head_id.set(cur_id)

        self._length.set(self._length.get() + 1)

        return cur_id

    def append_after(self, value, after_id: int, node_id: int = None) -> int:
        """ Append an element after an existing item of the linkedlist """
        if after_id == self._tail_id.get():
            return self.append(value, node_id)

        after = self._get_node(after_id)
        cur_id, cur = self._create_node(value, node_id)

        afternext_id = after.get_next()
        afternext = self._get_node(afternext_id)

        # after>nid
        after.set_next(cur_id)
        # after>next>pid
        afternext.set_prev(cur_id)
        # cur>nid
        cur.set_next(afternext_id)
        # cur>pid
        cur.set_prev(after_id)

        self._length.set(self._length.get() + 1)
        return cur_id

    def prepend_before(self, value, before_id: int, node_id: int = None) -> int:
        """ Append an element before an existing item of the linkedlist """
        if before_id == self._head_id.get():
            return self.prepend(value, node_id)

        before = self._get_node(before_id)
        cur_id, cur = self._create_node(value, node_id)

        beforeprev_id = before.get_prev()
        beforeprev = self._get_node(beforeprev_id)

        # before>pid
        before.set_prev(cur_id)
        # before>prev>nid
        beforeprev.set_next(cur_id)
        # cur>nid
        cur.set_next(before_id)
        # cur>pid
        cur.set_prev(beforeprev_id)

        self._length.set(self._length.get() + 1)
        return cur_id

    def move_node_after(self, cur_id: int, after_id: int) -> None:
        """ Move an existing node after another existing node """
        if cur_id == after_id:
            raise LinkedNodeCannotMoveItself(self._name, cur_id)

        if after_id == self._tail_id.get():
            return self.move_node_tail(cur_id)

        cur = self._get_node(cur_id)

        if after_id == cur.get_prev():
            # noop
            return

        after = self._get_node(after_id)
        afternext_id = after.get_next()
        afternext = self._get_node(afternext_id)
        curprev_id = cur.get_prev()
        if curprev_id:  # cur may be the head
            curprev = self._get_node(curprev_id)
        curnext_id = cur.get_next()
        if curnext_id:  # cur may be the tail
            curnext = self._get_node(curnext_id)

        # after>nid
        after.set_next(cur_id)
        # after>next>pid
        afternext.set_prev(cur_id)
        # curprev>nid
        if curprev_id:
            curprev.set_next(curnext_id)
        else:
            # cur was head, set new head
            self._head_id.set(curnext_id)
        # curnext>pid
        if curnext_id:
            curnext.set_prev(curprev_id)
        else:
            # cur was tail, set new tail
            self._tail_id.set(curprev_id)
        # cur>nid
        cur.set_next(afternext_id)
        # cur>pid
        cur.set_prev(after_id)

    def move_node_before(self, cur_id: int, before_id: int) -> None:
        """ Move an existing node before another existing node """
        if cur_id == before_id:
            raise LinkedNodeCannotMoveItself(self._name, cur_id)

        if before_id == self._head_id.get():
            return self.move_node_head(cur_id)

        cur = self._get_node(cur_id)

        if before_id == cur.get_next():
            # noop
            return

        before = self._get_node(before_id)
        beforeprev_id = before.get_prev()
        beforeprev = self._get_node(beforeprev_id)
        curprev_id = cur.get_prev()
        if curprev_id:  # cur may be the head
            curprev = self._get_node(curprev_id)
        curnext_id = cur.get_next()
        if curnext_id:  # cur may be the tail
            curnext = self._get_node(curnext_id)

        # before>pid
        before.set_prev(cur_id)
        # before>prev>nid
        beforeprev.set_next(cur_id)
        # curprev>nid
        if curprev_id:
            curprev.set_next(curnext_id)
        else:
            # cur was head, set new head
            self._head_id.set(curnext_id)
        # curnext>pid
        if curnext_id:
            curnext.set_prev(curprev_id)
        else:
            # cur was tail, set new tail
            self._tail_id.set(curprev_id)
        # cur>nid
        cur.set_next(before_id)
        # cur>pid
        cur.set_prev(beforeprev_id)

    def move_node_tail(self, cur_id: int) -> None:
        """ Move an existing node at the tail of the linkedlist """
        if cur_id == self._tail_id.get():
            raise LinkedNodeCannotMoveItself(self._name, cur_id)

        cur = self._get_node(cur_id)
        tail_id = self._tail_id.get()
        tail = self._get_node(tail_id)
        curprev_id = cur.get_prev()
        curprev = self._get_node(curprev_id)
        curnext_id = cur.get_next()
        curnext = self._get_node(curnext_id)

        # curprev>nid
        curprev.set_next(curnext_id)
        # curnext>pid
        curnext.set_prev(curprev_id)
        # tail>nid
        tail.set_next(cur_id)
        # cur>pid
        cur.set_prev(tail_id)
        # update tail
        self._tail_id.set(cur_id)

    def move_node_head(self, cur_id: int) -> None:
        """ Move an existing node at the head of the linkedlist """
        if cur_id == self._head_id.get():
            raise LinkedNodeCannotMoveItself(self._name, cur_id)

        cur = self._get_node(cur_id)
        head_id = self._head_id.get()
        head = self._get_node(head_id)
        curprev_id = cur.get_prev()
        curprev = self._get_node(curprev_id)
        curnext_id = cur.get_next()
        curnext = self._get_node(curnext_id)

        # curprev>nid
        curprev.set_next(curnext_id)
        # curnext>pid
        curnext.set_prev(curprev_id)
        # head>pid
        head.set_prev(cur_id)
        # cur>nid
        cur.set_next(head_id)
        # update head
        self._head_id.set(cur_id)

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

    def select(self, offset: int, cond=None, **kwargs) -> list:
        """ Returns a limited amount of items in the LinkedListDB that optionally fulfills a condition """
        items = iter(self)
        result = []

        # Skip N items until offset
        try:
            for _ in range(offset):
                next(items)
        except StopIteration:
            # Offset is bigger than the size of the bag
            raise StopIteration(self._name)

        # Do a maximum iteration count of MAX_ITERATION_LOOP
        for _ in range(MAX_ITERATION_LOOP):
            try:
                node = next(items)
                if cond:
                    if cond(self._db, node, **kwargs):
                        result.append(node)
                else:
                    result.append(node)
            except StopIteration:
                # End of array : stop here
                break

        return result


class UIDLinkedListDB(LinkedListDB):
    """
        UIDLinkedListDB is a linked list of unique IDs.
        The linkedlist node ID is equal to the value of the UID provided,
        so the developer needs to make sure the UID provided is globally unique to the application.
        Consequently, the concept of node ID is merged with the UID provided
        from a developper point of view, which simplifies the usage of the linkedlist.
    """
    _NAME = 'UID_LINKED_LIST_DB'

    def __init__(self, address: Address, db: IconScoreDatabase):
        name = f'{str(address)}_{UIDLinkedListDB._NAME}'
        super().__init__(name, db, int)
        self._name = name

    def append(self, uid: int, _: int = None) -> None:
        super().append(uid, uid)

    def prepend(self, uid: int, _: int = None) -> None:
        super().prepend(uid, uid)

    def append_after(self, value: int, after_id: int, _: int = None) -> None:
        super().append_after(value, after_id, value)

    def prepend_before(self, value: int, before_id: int, _: int = None) -> None:
        super().prepend_before(value, before_id, value)

    def __iter__(self):
        for node_id, uid in super().__iter__():
            yield uid
