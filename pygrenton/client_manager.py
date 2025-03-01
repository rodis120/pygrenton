"""Implementation of CLU client manager."""

import logging
import random
import re
import socket
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from multiprocessing.pool import ThreadPool
from threading import Lock, Thread
from typing import Any

from .cipher import GrentonCipher
from .exceptions import InvalidUpdateMessageError
from .utils import generate_id_hex, parse_list

_LOGGER = logging.getLogger(__name__)

_CLIENT_REFRESH_INTERVAL = 60
_CLIENT_PAGE_SIZE = 16

_UPDATE_MESSAGE_PATTERN = re.compile(r"^resp:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:[\da-fA-F]+:clientReport:(\d+):\{(.*)\}$")

@dataclass
class UpdateContext:
    object_id: str
    index: int
    value: Any

@dataclass(eq=True, frozen=True)
class _FeatureKey:
    object_id: str
    index: int

@dataclass
class _FeatureEntry:
    object_id: str
    index: int
    last_state: Any = None
    update_handlers: set[Callable[[UpdateContext], None]] = field(default_factory=set)

    def __hash__(self) -> int:
        return hash((self.object_id, self.index))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, _FeatureEntry) and
            self.object_id == other.object_id and
            self.index == other.index
        )

@dataclass
class _ClientPage:
    client_id: int
    features: list[_FeatureEntry] = field(default_factory=list)
    modified: bool = True
    modification_time: float = field(default_factory=time.time)

    def __hash__(self) -> int:
        return hash(self.client_id)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, _ClientPage) and
            self.client_id == other.client_id and
            self.features == other.features
        )

class ClientManager:

    def __init__(  # noqa: PLR0913
        self,
        cipher: GrentonCipher,
        clu_ip: str,
        clu_port: int,
        client_ip: str,
        client_port: int,
        handler_threads: int=4,
        keep_alive_interval: float=10
    ) -> None:
        """Create a new ClientManager."""
        self._cipher = cipher
        self._clu_ip = clu_ip
        self._clu_port = clu_port
        self._client_ip = client_ip
        self._client_port = client_port
        self._keep_alive_interval = keep_alive_interval

        self._last_client_refresh_time = time.time()
        self._last_keep_alive_packet_time = time.time()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((client_ip, client_port))

        self._running = True
        self._listener_thread = Thread(target=self._listener, daemon=True)
        self._listener_thread.start()

        self._keep_alive_thread = Thread(target=self._keep_alive, daemon=True)
        self._keep_alive_thread.start()

        self._handler_thread_pool = ThreadPool(processes=handler_threads)

        self._feature_entries: dict[_FeatureKey, _FeatureEntry] = {}
        self._client_pages: dict[int, _ClientPage] = {}
        self._nonfull_pages: set[_ClientPage] = {}
        self._client_pages_lock = Lock()
        self._page_modified = False

    def __del__(self) -> None:
        """Terminates client managern on instance destruction."""
        self.close()

    def close(self) -> None:
        """Close the client manager."""
        self._running = False
        self._socket.close()
        self._handler_thread_pool.terminate()

    def add_update_handler(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        with self._client_pages_lock:
            key = _FeatureKey(object_id, index)

            if key in self._feature_entries:
                self._feature_entries[key].update_handlers.add(handler)
                return

            feature_entry = _FeatureEntry(object_id, index)
            feature_entry.update_handlers.add(handler)

            if self._nonfull_pages:
                page = self._nonfull_pages.pop()
            else:
                page = _ClientPage(self._gen_unique_client_id())
                self._client_pages[page.client_id] = page

            page.features.append(feature_entry)
            page.modification_time = time.time()

            self._page_modified = True

            if len(page.features) < _CLIENT_PAGE_SIZE:
                self._nonfull_pages.add(page)

    def remove_update_handler(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        with self._client_pages_lock:
            key = _FeatureKey(object_id, index)

            entry = self._feature_entries.get(key)
            if entry is None:
                return

            entry.update_handlers.remove(handler)

            if not entry.update_handlers:
                self._remove_feature_entry(entry)

    def _remove_feature_entry(self, key: _FeatureKey) -> None:
        entry = self._feature_entries.get(key)
        for page in self._client_pages.values():
            if entry in page.features:
                page.features.remove(entry)
                page.modified = True
                page.modification_time = time.time()
                self._page_modified = True

                self._nonfull_pages.add(page)

                if not page.features:
                    del self._client_pages[page.client_id]
                    self._nonfull_pages.remove(page)
                break

    def _gen_unique_client_id(self) -> int:
        while True:
            client_id = random.randint(0, 1 << 30)  # noqa: S311
            if client_id not in self._client_pages:
                return client_id

    def _send_keep_alive_packet(self) -> None:
        data = b"12345678" # some random data to keep udp connection alive, clu is not supposed to respond to this packet
        # might replace it with calling checkAlive() function in the future
        self._socket.sendto(data, (self._client_ip, self._clu_port))

    def _register_client(self, page: _ClientPage) -> None:
        features_str = "{" + ",".join(f"{{{fe.object_id},{fe.index}}}" for fe in page.features) + "}"
        payload = f'SYSTEM:clientRegister("{self._client_ip}",{self._client_port},{page.client_id},{features_str})'

        session_id = generate_id_hex()
        payload = f"req:{self._client_ip}:{session_id}:{payload}"

        self._socket.sendto(self._cipher.encrypt(payload.encode()), (self._clu_ip, self._clu_port))

    def _refresh_clients(self) -> None:
        with self._client_pages_lock:
            for page in self._client_pages.values():
                page.modified = False
                self._register_client(page)

    def _refresh_modified_clients(self) -> None:
        with self._client_pages_lock:
            for page in self._client_pages.values():
                if page.modified:
                    page.modified = False
                    self._register_client(page)
            self._page_modified = True

    def _parse_update_message(self, msg: str) -> tuple[int, list[Any]]:
        m = re.match(_UPDATE_MESSAGE_PATTERN, msg)

        if m is None:
            raise InvalidUpdateMessageError

        client_id = int(m.group(1))
        values = parse_list(m.group(2))

        return client_id, values

    def _process_update_message(self, msg: str, msg_time: float) -> None:
        client_id, values = self._parse_update_message(msg)

        with self._client_pages_lock:
            page = self._client_pages.get(client_id)

            if page is None or page.modified or page.modification_time > msg_time:
                return

            for fe, new_value in filter(lambda x: x[0].last_state != x[1], zip(page.features, values, strict=True)):
                fe.last_state = new_value

                for handler in fe.update_handlers:
                    self._handler_thread_pool.apply_async(
                        func=handler,
                        args=(UpdateContext(fe.object_id, fe.index, new_value),),
                        error_callback=lambda _: _LOGGER.exception("Exception occured in an update handler")
                    )

    def _listener(self) -> None:
        while self._running:
            try:
                data, _ = self._socket.recvfrom(1024)
                msg_time = time.time()
                decrypted = self._cipher.decrypt(data).decode()

                self._process_update_message(decrypted, msg_time)

            except Exception:
                _LOGGER.exception("Exception occured in listener thread")

    def _keep_alive(self) -> None:
        while self._running:
            try:
                self._send_keep_alive_packet()
                self._last_keep_alive_packet_time = time.time()

                if self._page_modified:
                    self._refresh_modified_clients()

                if time.time() - self._last_client_refresh_time >= _CLIENT_REFRESH_INTERVAL:
                    self._refresh_clients()
                    self._last_client_refresh_time = time.time()

                current_time = time.time()
                time.sleep(min(
                    self._keep_alive_interval - (current_time - self._last_keep_alive_packet_time),
                    _CLIENT_REFRESH_INTERVAL - (current_time - self._last_client_refresh_time)
                ))
            except Exception:
                _LOGGER.exception("Exception occured in keep-alive thread")
