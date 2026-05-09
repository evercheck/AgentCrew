from abc import abstractmethod
from typing import Any


class Observable:
    """Base class for observables, implementing the observer pattern."""

    def __init__(self):
        self._observers: list["Observer"] = []

    def attach(self, observer: "Observer"):
        """Attaches an observer to the observable."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: "Observer"):
        """Detaches an observer from the observable."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self, event: str, data: Any = None):
        """Notifies all attached observers of a new event."""
        for observer in self._observers:
            observer.listen(event, data)


class Observer:
    """Abstract base class for observers."""

    @abstractmethod
    def listen(self, event: str, data: Any = None):
        """Updates the observer with new data from the observable."""
        pass
