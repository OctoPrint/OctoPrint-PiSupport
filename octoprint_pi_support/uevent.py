import logging
import os
import socket
import threading

LOGGING_PREFIX = "octoprint.plugins.pi_support"


class UEvent:
    def __init__(self, data: bytes):
        items = data.split(b"\0")
        if len(items) == 0:
            raise ValueError("Invalid UEvent data")

        self.event = items.pop(0).decode()

        self.fields = {}
        for item in items:
            if b"=" not in item:
                continue
            parts = item.split(b"=", maxsplit=1)
            self.fields[parts[0].decode()] = parts[1].decode()

    def __str__(self):
        return f"{self.event}\n" + "\n".join(
            [f"\t{key}: {value}" for key, value in self.fields.items()]
        )


class UEventProcessor:
    NETLINK_KOBJECT_UEVENT = 15

    def __init__(self):
        self._logger = logging.getLogger(LOGGING_PREFIX + ".uevent")

        self._running = False
        self._thread = None
        self._sock = None

        self._listeners = []

    def register_listener(self, listener):
        self._listeners.append(listener)

    def unregister_listener(self, listener):
        self._listener.remove(listener)

    def start(self, daemon: bool = True):
        if self._thread or self._sock:
            return

        self._thread = threading.Thread(target=self._loop, name="uevent-processor")
        self._thread.daemon = daemon
        self._thread.start()

    def stop(self):
        self._running = False

        if not self._sock:
            return
        self._sock.shutdown()

    def _loop(self):
        self._sock = socket.socket(
            socket.AF_NETLINK, socket.SOCK_RAW, self.NETLINK_KOBJECT_UEVENT
        )
        addr = (os.getpid(), 1)

        self._logger.info("Starting listening to uevents")

        try:
            self._sock.bind(addr)
            self._running = True

            while self._running:
                try:
                    data = self._sock.recv(4096)
                    if len(data) == 0:
                        break

                    try:
                        uevent = UEvent(data)
                        self._logger.debug(f"Received uevent: {uevent.event}")
                        notifier = threading.Thread(target=self._notify, args=(uevent,))
                        notifier.daemon = True
                        notifier.start()
                    except ValueError:
                        self._logger.debug("Received invalid uevent")
                except TimeoutError:
                    pass
        except KeyboardInterrupt:
            pass
        except Exception:
            self._logger.exception("Exception in UEvent processor loop")
        finally:
            try:
                self._sock.close()
            except OSError:
                # already closed?
                self._logger.exception("Exception closing socket")

    def _notify(self, uevent: UEvent):
        for listener in self._listeners:
            if not callable(listener):
                continue
            try:
                listener(uevent)
            except Exception:
                self._logger.exception(f"Exception calling listener {listener!r}")


def main():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    processor = UEventProcessor()
    processor.register_listener(print)
    processor.start(daemon=False)


if __name__ == "__main__":
    main()
