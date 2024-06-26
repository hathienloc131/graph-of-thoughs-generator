from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List


class Prompter(ABC):
    """
    Abstract base class that defines the interface for all prompters.
    Prompters are used to generate the prompts for the language models.
    """

    @abstractmethod
    def aggregate_prompt(self, state_dicts: Dict, **kwargs) -> tuple[str, str]:
        """
        Generate a aggregation prompt for the language model.
        """
        pass

    @abstractmethod
    def improve_prompt(self, state_dicts: Dict, **kwargs) -> tuple[str, str]:
        """
        Generate an improve prompt for the language model.
        The thought state is unpacked to allow for additional keyword arguments
        and concrete implementations to specify required arguments explicitly.
        """
        pass

    @abstractmethod
    def generate_prompt(self, state_dicts: Dict, **kwargs) -> tuple[str, str]:
        """
        Generate a generate prompt for the language model.
        The thought state is unpacked to allow for additional keyword arguments
        and concrete implementations to specify required arguments explicitly.
        """
        pass

    @abstractmethod
    def split_prompt(self, state_dicts: Dict, **kwargs) -> tuple[str, str]:
        """
        Generate a split prompt for the language model.
        The thought state is unpacked to allow for additional keyword arguments
        and concrete implementations to specify required arguments explicitly.
        """
        pass

    @abstractmethod
    def improve_prompt(self, state_dicts: Dict, **kwargs) -> tuple[str, str]:
        """
        Generate a improve prompt for the language model.
        The thought state is unpacked to allow for additional keyword arguments
        and concrete implementations to specify required arguments explicitly.
        """
        pass

    @abstractmethod
    def score_prompt(self, state_dicts: Dict, **kwargs) -> tuple[str, str]:
        """
        Generate a score prompt for the language model.
        The thought state is unpacked to allow for additional keyword arguments
        and concrete implementations to specify required arguments explicitly.
        """
        pass