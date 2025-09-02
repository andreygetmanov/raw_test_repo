# Copyright (c) Meta Platforms, Inc. and affiliates
from typing import Dict, List, Optional
from ..models.product import Item


class Store:
    """
    Represents a storage facility for Item objects with capacity, supporting addition, removal, retrieval, and listing functionalities.

        Class Attributes:
            cap: The maximum number of items allowed.
            _data: A dictionary mapping string keys to Item objects, used to store the main data.
            _map: A dictionary mapping integer IDs to string keys, used for internal key associations.

        Methods:
        - __init__
        - put
        - rm
        - get
        - get_at
        - ls
        - find

        The class methods enable managing items by adding to, removing from, or retrieving them from storage. The attributes track capacity, store items and manage internal key associations.
    """


    def __init__(self, cap: int=20):
        """
        Initializes the Store instance with a specified item capacity, internal storage for items, and an auxiliary ID-to-key mapping.

        This setup prepares the instance to efficiently manage and organize multiple items by both string keys and numeric IDs, facilitating flexible data access and association.

        Args:
            cap (int, optional): The maximum number of items the store can hold. Defaults to 20.

        Returns:
            None
        """
        self.cap = cap
        self._data: Dict[str, Item] = {}
        self._map: Dict[int, str] = {}

    def put(self, obj: Item, pos: Optional[int]=None) ->bool:
        """
        Attempts to store an item in the internal collection at a specific position or in the next free slot.

        This method ensures efficient management of items by either aggregating counts for identical items or allocating them to available positions. This helps maintain accurate and organized tracking of each unique item and its quantity.

        Args:
            obj (Item): The item object to add or increment within the collection.
            pos (Optional[int]): The desired position for the item. If None, the method will search for the next available slot.

        Returns:
            bool: True if the item was successfully added or its count was updated; False if the item could not be placed.
        """
        if obj.code in self._data:
            curr = self._data[obj.code]
            curr.count += obj.count
            return True
        if pos is not None:
            if pos < 0 or pos >= self.cap:
                return False
            if pos in self._map:
                return False
            self._map[pos] = obj.code
        else:
            for i in range(self.cap):
                if i not in self._map:
                    self._map[i] = obj.code
                    break
            else:
                return False
        self._data[obj.code] = obj
        return True

    def rm(self, code: str) ->bool:
        """
        Deletes the specified code from the object's internal data and mapping structures to ensure consistency and prevent orphaned references.

        Args:
            code (str): The unique identifier to be removed from internal data and mapping.

        Returns:
            bool: True if the code existed and was removed from both storage locations, False otherwise.
        """
        if code not in self._data:
            return False
        for k, v in list(self._map.items()):
            if v == code:
                del self._map[k]
        del self._data[code]
        return True

    def get(self, code: str) ->Optional[Item]:
        """
        Fetches an item from the store's internal collection using its unique code, enabling other components to efficiently locate and access stored records.

        Args:
            code (str): The unique code identifying the item to retrieve.

        Returns:
            Item or None: The item associated with the specified code, or None if no such item exists.
        """
        return self._data.get(code)

    def get_at(self, pos: int) ->Optional[Item]:
        """
        Fetches the stored element linked to a specific position index.

        This method enables efficient retrieval of stored elements by mapping positions to underlying codes, then fetching the corresponding data object. This design abstracts internal representations, allowing users to access elements using simple position keys.

        Args:
            pos (int): The position index to query within the store.

        Returns:
            Optional[Item]: The stored element if the position exists, otherwise None.

        Why:
            Allows clients to access data elements efficiently without exposing internal indexing or storage mechanisms, supporting straightforward data lookup and interaction.
        """
        if pos not in self._map:
            return None
        code = self._map[pos]
        return self._data.get(code)

    def ls(self) ->List[Item]:
        """
        Returns a list of items from the internal storage that have passed their validation criteria.

        This method ensures that only items which meet certain integrity or readiness checks are presented, filtering out incomplete or invalid entries. This promotes reliability when the data is consumed or processed further.

        Args:
            self: The Store instance containing the internal data.

        Returns:
            List[Item]: List of items from the internal store that have a successful `check()` result.
        """
        return [obj for obj in self._data.values() if obj.check()]

    def find(self, code: str) ->Optional[int]:
        """
        Locate and return the internal identifier corresponding to a specific code value.

        This method scans the internal mapping to retrieve the key (typically representing an internal record or item) that maps to the provided code. This facilitates efficient reverse lookups, allowing the system to relate external or encoded representations back to their associated internal identifiers.

        Args:
            code (str): The code value to search for within the internal mapping.

        Returns:
            Optional[int]: The key (identifier) associated with the code if found; otherwise, None.
        """
        for k, v in self._map.items():
            if v == code:
                return k
        return None
