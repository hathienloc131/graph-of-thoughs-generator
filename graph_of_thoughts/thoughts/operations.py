from __future__ import annotations
import logging
from enum import Enum
from typing import List, Iterator, Dict, Callable, Union
from abc import ABC, abstractmethod
import itertools

from graph_of_thoughts.thoughts.thought import Thought
from graph_of_thoughts.language_model import AbstractLanguageModel
from graph_of_thoughts.prompter import Prompter
from graph_of_thoughts.judge import Judge
from graph_of_thoughts.parser import Parser


class OperationType(Enum):
    """
    Enum to represent different operation types that can be used as unique identifiers.
    """

    split: int = 0
    generate: int = 1
    improve: int = 2
    aggregate: int = 3


class Operation(ABC):
    """
    Abstract base class that defines the interface for all operations.
    """

    _ids: Iterator[int] = itertools.count(0)
    operation_type: OperationType = None
    operation_name: str = None


    def __init__(self) -> None:

        self.id: int = next(Operation._ids)
        self.predecessors: List[Operation] = []
        self.successors: List[Operation] = []
        self.executed: bool = False

        self.thoughts: List[Thought] = []


    def can_be_executed(self) -> bool:
        return all(predecessor.executed for predecessor in self.predecessors)


    def get_previous_thoughts(self) -> List[Thought]:
        previous_thoughts: List[Thought] = [
            thought
            for predecessor in self.predecessors
            for thought in predecessor.get_thoughts()
        ]

        print(previous_thoughts)

        return previous_thoughts


    def add_predecessor(self, operation: Operation) -> None:
        self.predecessors.append(operation)
        operation.successors.append(self)


    def add_successor(self, operation: Operation) -> None:
        self.successors.append(operation)
        operation.predecessors.append(self)


    def get_previous_thoughts(self) -> List[Thought]:
        """
        Iterates over all predecessors and aggregates their thoughts.

        `Output`
        - `<List[Thought]>` A list of all thoughts from the predecessors.
        """
        previous_thoughts: List[Thought] = [thought for predecessor in self.predecessors
            for thought in predecessor.get_thoughts()
        ]

        return previous_thoughts
    

    def add_predecessor(self, operation: Operation) -> None:
        """
        Add a preceding operation and update the relationships.

        `Input`
        - operation: `<Operation>` The operation to be set as a predecessor.
        """
        self.predecessors.append(operation)
        operation.successors.append(self)


    def add_successor(self, operation: Operation) -> None:
        """
        Add a succeeding operation and update the relationships.

        `Input`
        - operation: `<Operation>` The operation to be set as a successor.
        """
        self.successors.append(operation)
        operation.predecessors.append(self)


    def execute(
        self, lm: AbstractLanguageModel, prompter: Prompter, parser: Parser, judge: Judge, **kwargs
    ) -> None:
        """
        Execute the operation, assuring that all predecessors have been executed.

        `Input`
        - lm: `<AbstractLanguageModel>` The language model to be used.
        - prompter: `<Prompter>` The prompter for crafting prompts.
        - parser: `<Parser>` The parser for parsing responses.
        - kwargs: Additional parameters for execution.

        `Raises`:
        - `AssertionError`: If not all predecessors have been executed.
        """

        assert (
            self.can_be_executed(), "Not all predecessors have been executed"
            "Executing operation %d of type %s", self.id, self.operation_type
        )
        self._execute(lm, prompter, parser, judge, **kwargs)
        print(self.__repr__())
        for t in self.thoughts:
            print("\t", t.state)
        self.executed = True

    @abstractmethod
    def _execute(
        self, lm: AbstractLanguageModel, prompter: Prompter, parser: Parser, **kwargs
    ) -> None:
        """
        Abstract method for the actual execution of the operation.
        This should be implemented in derived classes.

        `Input`:
        - lm: `<AbstractLanguageModel>` The language model to be used.
        - prompter: `<Prompter>` The prompter for crafting prompts.
        - parser: `<Parser>` The parser for parsing responses.
        - kwargs: Additional parameters for execution.
        """
        pass

    @abstractmethod
    def get_thoughts(self) -> List[Thought]:
        """
        Abstract method to retrieve the thoughts associated with the operation.
        This should be implemented in derived classes.

        :return: List of associated thoughts.
        :rtype: List[Thought]
        """
        pass


class Split(Operation):
    """
    Operation to split thoughts.
    """
    operation_type: OperationType = OperationType.split
    operation_name: str = "SPLIT"


    def __init__(self, num_split:int = 2) -> None:

        super().__init__()
        
        if num_split < 2:
            raise ValueError(f"num_split must greater than 1, but found {num_split}")
        
        self.num_split = num_split
        
        self.operation_name += f" {self.num_split}"


    def get_thoughts(self) -> List[Thought]:
        return self.thoughts
    

    def _execute(self, lm: AbstractLanguageModel, prompter: Prompter, parser: Parser, judge: Judge, **kwargs) -> None:
        """
        Executes the Split operation by generating thoughts from the predecessors.
        The thoughts are generated by prompting the LM with the predecessors' thought states.
        If there are no predecessors, the kwargs are used as a base state.

        `Input`:
        - lm: `<AbstractLanguageModel>` The language model to be used.
        - prompter: `<Prompter>` The prompter for crafting prompts.
        - parser: `<Parser>` The parser for parsing responses.
        - kwargs: Additional parameters for execution.
        """
        self.thoughts = []

        previous_thoughts: List[Thought] = self.get_previous_thoughts()
        if len(previous_thoughts) == 0:
            # no predecessors, use kwargs as base state
            previous_thoughts = [Thought(state=kwargs)]

        for thought in previous_thoughts:
            base_state = thought.state
            split_state, split_prompt = prompter.split_prompt({**base_state, **self.__dict__}, **kwargs)

            responses = lm.get_response_texts(
                lm.query(split_prompt)
            )
            print(responses)
            for new_state in parser.parse_split_answer(self.__dict__, base_state, responses):
                new_state = {**base_state, **new_state}
                new_state["state"] = split_state
                self.thoughts.append(Thought(new_state))

        if (len(self.thoughts) > self.num_split):
            print("LM returns more thoughts than expected.")


    def __repr__(self) -> str:
        return f"""Split Operation\nID:{self.id}\nNo. Split: {self.num_split};"""
    

class Generate(Operation):
    """
    Operation to generate thoughts.
    """
    operation_type: OperationType = OperationType.generate
    operation_name: str = "GENERATE"


    def __init__(self, num_try:int = 1, num_choice:int = 1, part:int = None) -> None:

        super().__init__()
        if num_choice > num_try:
            raise ValueError(f"num_choice must less than num_try, but found num_choice({num_choice}) > num_try({num_try})")
        
        if num_try < 1 or num_choice < 1:
            raise ValueError(f"num_try and num_choice must be positive")
        
        self.num_try = num_try
        self.num_choice = num_choice
        self.part = part

        self.operation_name += f" {self.num_try} {self.num_choice}"


    def get_thoughts(self) -> List[Thought]:
        return self.thoughts


    def _execute(
        self, lm: AbstractLanguageModel, prompter: Prompter, parser: Parser, judge: Judge, **kwargs
    ) -> None:
        """
        Executes the Generate operation by generating thoughts from the predecessors.
        The thoughts are generated by prompting the LM with the predecessors' thought states.
        If there are no predecessors, the kwargs are used as a base state.

        `Input`:
        - lm: `<AbstractLanguageModel>` The language model to be used.
        - prompter: `<Prompter>` The prompter for crafting prompts.
        - parser: `<Parser>` The parser for parsing responses.
        - kwargs: Additional parameters for execution.
        """
        self.thoughts = []

        previous_thoughts: List[Thought] = self.get_previous_thoughts()
        if len(previous_thoughts) == 0:
            if len(self.predecessors) > 0:
                return
            # no predecessors, use kwargs as base state
            previous_thoughts = [Thought(state=kwargs)]
        else:
            previous_thoughts = [(Thought.from_thought(self.get_previous_thoughts()[self.part]))]
        
        for thought in previous_thoughts:
            base_state = thought.state
            generate_state, generate_prompt = prompter.generate_prompt(base_state, **kwargs)

            responses = lm.get_response_texts(
                lm.query(generate_prompt, num_responses=self.num_try)
            )
            if self.num_try > 1:
                score_prompt = prompter.score_prompt(base_state, **kwargs)
                responses = judge.ranking(score_prompt, generate_prompt, responses, self.num_choice)

            for new_state in parser.parse_generate_answer(self.__dict__, base_state, responses):
                new_state = {**base_state, **new_state}
                new_state["state"] = generate_state
                self.thoughts.append(Thought(new_state))
        if (len(self.thoughts) > self.num_try * len(previous_thoughts)):
            print(f"Generate operation {self.id} created more thoughts than expected")


    def __repr__(self) -> str:
        return f"""Generate Operation\nID:{self.id}\nNo. Try: {self.num_try}\nNo. Choice: {self.num_choice};"""
    

class Improve(Generate):
    """
    Operation to Improve thoughts.
    """
    operation_type: OperationType = OperationType.improve
    operation_name: str = "IMPROVE"


    def __init__(self, num_try:int = 1, num_choice:int = 1, part:int = None) -> None:
        super().__init__(num_try, num_choice, part)


    def _execute(
        self, lm: AbstractLanguageModel, prompter: Prompter, parser: Parser, judge: Judge, **kwargs
    ) -> None:
        """
        Executes the Generate operation by generating thoughts from the predecessors.
        The thoughts are generated by prompting the LM with the predecessors' thought states.
        If there are no predecessors, the kwargs are used as a base state.

        `Input`:
        - lm: `<AbstractLanguageModel>` The language model to be used.
        - prompter: `<Prompter>` The prompter for crafting prompts.
        - parser: `<Parser>` The parser for parsing responses.
        - kwargs: Additional parameters for execution.
        """
        self.thoughts = []

        previous_thoughts: List[Thought] = self.get_previous_thoughts()
        if len(previous_thoughts) == 0:
            if len(self.predecessors) > 0:
                return
            # no predecessors, use kwargs as base state
            previous_thoughts = [Thought(state=kwargs)]
        else:
            previous_thoughts = [(Thought.from_thought(self.get_previous_thoughts()[self.part]))]

        for thought in previous_thoughts:
            base_state = thought.state
            generate_state, generate_prompt = prompter.improve_prompt(base_state, **kwargs)

            responses = lm.get_response_texts(
                lm.query(generate_prompt, num_responses=self.num_try)
            )
            if self.num_try > 1:
                score_prompt = prompter.score_prompt(base_state, **kwargs)
                responses = judge.ranking(score_prompt, generate_prompt, responses, self.num_choice)

            for new_state in parser.parse_generate_answer(self.__dict__, base_state, responses):
                new_state = {**base_state, **new_state}
                new_state["state"] = generate_state
                self.thoughts.append(Thought(new_state))
        if (len(self.thoughts) > self.num_try * len(previous_thoughts)):
            raise Exception(f"Improve operation {self.id} created more thoughts than expected")


    def __repr__(self) -> str:
        return f"""Improve Operation\nID:{self.id}\nNo. Try: {self.num_try}\nNo. Choice: {self.num_choice};"""
    

class Aggregate(Operation):
    """
    Operation to Aggregate thoughts.
    """
    operation_type: OperationType = OperationType.aggregate
    operation_name: str = "AGGREGATE"


    def __init__(self, num_try:int = 1) -> None:
        super().__init__()
        if num_try < 1:
            raise ValueError(f"num_try must be positive")
        
        self.num_try = num_try

        self.operation_name += f" {self.num_try}"


    def get_thoughts(self) -> List[Thought]:
        return self.thoughts


    def _execute(
        self, lm: AbstractLanguageModel, prompter: Prompter, parser: Parser, judge: Judge, **kwargs) -> None:
        """
        Executes the Aggregate operation by aggregating the predecessors' thoughts.
        The thoughts are aggregated by prompting the LM with the predecessors' thought states.
        
        `Input`:

        - lm: `<AbstractLanguageModel>` The language model to be used.
        - prompter: `<Prompter>` The prompter for crafting prompts.
        - parser: `<Parser>` The parser for parsing responses.
        - kwargs: Additional parameters for execution.

        `Raises`:
        - `AssertionError`: If operation has no predecessors.
        """
        self.thoughts = []
        
        assert (
            len(self.predecessors) >= 1
        ), "Aggregate operation must have at least one predecessor"

        previous_thoughts: List[Thought] = self.get_previous_thoughts()

        if len(previous_thoughts) == 0:
            return

        # applied in order of score
        base_state: Dict = {
            "state": [],
            "current": [],
        }

        for idx, thought in enumerate(previous_thoughts):
            base_state["state"].append(f'TASK {idx+1}: {thought.state["state"]}')
            base_state["current"].append(f'RESULT OF TASK {idx+1}: {thought.state["current"]}')

        base_state["state"] = "\n".join(base_state["state"])
        base_state["current"] = "\n".join(base_state["current"])
        base_state["origin"] = previous_thoughts[0].state["origin"]


        aggregate_state, aggregate_prompt = prompter.aggregate_prompt(base_state, **kwargs)

        responses = lm.get_response_texts(
            lm.query(aggregate_prompt, num_responses=self.num_try)
        )
        if self.num_try > 1:
            score_prompt = prompter.score_prompt(base_state, **kwargs)
            responses = judge.ranking(score_prompt, aggregate_prompt, responses)

        for new_state in parser.parse_generate_answer(self.__dict__, base_state, responses):
                new_state = {**base_state, **new_state}
                new_state["state"] = aggregate_state
                self.thoughts.append(Thought(new_state))


    def __repr__(self) -> str:
        return f"""Aggregate Operation\nID:{self.id}\nNo. Try: {self.num_try};"""