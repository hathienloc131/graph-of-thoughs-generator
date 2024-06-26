# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# main author: Nils Blach

from abc import ABC, abstractmethod
from typing import List, Dict, Union, Any
from configs.lm_config import LM_CONFIG

class AbstractLanguageModel(ABC):
    """
    Abstract base class that defines the interface for all language models.
    """

    def __init__(
        self, model_name: str = "", cache: bool = False
    ) -> None:
        """
        Initialize the AbstractLanguageModel instance with configuration, model details, and caching options.

        `Input`:
        - config_path: `<str>` Path to the config file. Defaults to "".
        - model_name: `<str>` Name of the language model. Defaults to "".
        - cache: `<str>` Flag to determine whether to cache responses. Defaults to False.
        """
        self.model_name: str = model_name
        self.config: Dict = LM_CONFIG
        self.cache = cache
        if self.cache:
            self.respone_cache: Dict[str, List[Any]] = {}
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.cost: float = 0.0


    def clear_cache(self) -> None:
        """
        Clear the response cache.
        """
        self.respone_cache.clear()

    @abstractmethod
    def query(self, query: str, num_responses: int = 1, problem_description: str = None) -> Any:
        """
        Abstract method to query the language model.

        `Input`:
        - query: `<str>` The query to be posed to the language model.
        - num_responses: `<int>` The number of desired responses.
        
        `Output`:
        - `<Any>` The language model's response(s).
        """
        pass

    @abstractmethod
    def get_response_texts(self, query_responses: Union[List[Dict], Dict]) -> List[str]:
        """
        Abstract method to extract response texts from the language model's response(s).

        `Input`:

        - query_responses: `<Union[List[Dict], Dict]>` The responses returned from the language model.

        `Output`:
        - `<List[str]>` List of textual responses.
        """
        pass