# Copyright (c) Meta Platforms, Inc. and affiliates
from decimal import Decimal
from typing import Optional, List, Tuple
from .models.product import Item
from .payment.payment_processor import Handler, Tx, TxStatus, Cash
from .inventory.inventory_manager import Store


class SysErr(Exception):
    """
    Represents a system error with associated details.

        Attributes:
            code: The error code.
            message: The error message.
            timestamp: The time when the error occurred.

        Methods:
            __init__
            log
            to_dict

        This class provides convenient storage for system error data, including code, message, and timestamp, and includes utility methods to log the error or convert it to a dictionary.
    """

    pass


class Sys:
    """
    Represents an automated system for managing transactions and stored items, such as a vending machine or similar transaction-based device.

        This class handles the transaction flow, manages an internal store of items, interacts with a transaction handler (such as a cash manager), and provides methods for listing items, purchasing, adding funds, and canceling transactions.

        Attributes:
            store: An instance of Store initialized with a default capacity of 20. Used to manage stored items internally.
            h: The transaction handler, either supplied by the user or set to a default Cash handler. Manages transaction logic for the object.
            _tx: Internal variable set to None, holds the current transaction object if one is active.

        Methods:
        - __init__
        - ls
        - pick
        - add_money
        - buy
        - cancel

        The methods allow for listing and validating items, safely conducting purchases (including money handling and transaction rollback on errors), and managing transaction cancellation. Attributes provide access to the internal item store, transaction handler, and track the current active transaction, if any.
    """


    def __init__(self, h: Optional[Handler]=None):
        """
        Constructs a new instance by preparing an internal data store and configuring the transaction handling mechanism. This setup ensures that the system is organized to manage item storage and transactional operations efficiently from the start.

        Args:
            h (Optional[Handler]): An optional transaction handler. If not supplied, a default handler is instantiated to process transaction-related actions.

        Returns:
            None. This constructor initializes internal components but does not return a value.
        """
        self.store = Store()
        self.h = h or Cash()
        self._tx: Optional[Tx] = None

    def ls(self) ->List[Tuple[int, Item]]:
        """
        Retrieves all items from the backend store, associates each with its current position, and returns a list sorted by position.

        This method ensures the output reflects the order of items as maintained by the underlying store, which helps maintain consistency when presenting or processing stored data. By pairing each item with its respective position and sorting the results, the method supports deterministic behavior and reliable downstream use.

        Args:
            self: The instance of the class.

        Returns:
            List[Tuple[int, Item]]: A list of (position, item) tuples, where each item is paired with its position in the store. The list is sorted in ascending order of position.
        """
        items = []
        for item in self.store.ls():
            pos = self.store.find(item.code)
            if pos is not None:
                items.append((pos, item))
        return sorted(items, key=lambda x: x[0])

    def pick(self, pos: int) ->Optional[Item]:
        """
        Retrieves an item from the internal store by its position and ensures that the item is available and meets defined validity checks.

        This method ensures that users interact only with valid and accessible items, preventing operations on invalid or inaccessible entries.

        Args:
            pos (int): The zero-based index in the store identifying the item to retrieve.

        Returns:
            Optional[Item]: The item located at the given position in the store, if it exists and passes validation.

        Raises:
            SysErr: If the position is out of bounds or the item fails the availability check.
        """
        item = self.store.get_at(pos)
        if not item:
            raise SysErr('invalid pos')
        if not item.check():
            raise SysErr('unavailable')
        return item

    def add_money(self, amt: Decimal) ->None:
        """
        Registers a monetary increment to the system's current handler, ensuring the operation is supported.

        This method verifies that the internal monetary handler accepts cash modifications before updating its balance. This precaution is necessary to maintain integrity and consistency of state when managing different handler types within the system.

        Args:
            amt (Decimal): The monetary value to be added to the active handler.

        Returns:
            None
        Raises:
            SysErr: If the current handler does not support cash operations.
        """
        if not isinstance(self.h, Cash):
            raise SysErr('cash not supported')
        self.h.add(amt)

    def buy(self, pos: int) ->Tuple[Item, Optional[Decimal]]:
        """
        Handles the process of selecting, purchasing, and dispensing an item at a specific position by managing the payment, ensuring item availability, processing any required change, and enforcing rollback in case of failures.

        This method coordinates selection of the requested item, initiates the financial transaction, validates successful payment, attempts to physically dispense the item, and, when relevant, handles returning change. If any step fails, the transaction is reversed and an error is raised to maintain consistency and prevent incorrect charges or inventory depletion.

        Args:
            pos (int): The position index of the item to be purchased.

        Returns:
            Tuple[Item, Optional[Decimal]]: A tuple containing the dispensed item and, if applicable, the change returned (or None if not applicable).

        Raises:
            SysErr: If payment processing fails or the item cannot be dispensed.
        """
        item = self.pick(pos)
        tx = self.h.proc(Decimal(str(item.val)))
        self._tx = tx
        if tx.st != TxStatus.DONE:
            raise SysErr(tx.msg or 'tx failed')
        if not item.mod():
            self.h.rev(tx)
            raise SysErr('dispense failed')
        ret = None
        if isinstance(self.h, Cash):
            ret = self.h.ret()
        return item, ret

    def cancel(self) ->Optional[Decimal]:
        """
        Cancels the ongoing transaction, reverting any pending actions and optionally returning a result.

        This method ensures that if a transaction is no longer valid or needed, it is properly reversed to maintain the integrity of the object's state. After attempting the reversal, if the handler supports extracting a related value, that value is returned. Regardless of success or the handler type, the internal transaction reference is cleared to avoid inconsistencies.

        Args:
            self: Instance containing the transaction context and handler.

        Returns:
            Optional[Decimal]: A value derived from the handler if supported; otherwise, None.

        Raises:
            SysErr: If no transaction is active or if the reversal process fails.
        """
        if not self._tx:
            raise SysErr('no tx')
        ok = self.h.rev(self._tx)
        if not ok:
            raise SysErr('rev failed')
        ret = None
        if isinstance(self.h, Cash):
            ret = self.h.ret()
        self._tx = None
        return ret
