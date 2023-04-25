from abc import ABC, abstractmethod
from typing import Union, List, Dict, Callable, Tuple, Optional

from code_genie.client import Client, GetExecutableRequest, GetPandasExecutableRequest


class GenieBase(ABC):

    def __init__(self,
                 instructions: Union[str, List[str]],
                 inputs: Dict[str, str],
                 allowed_imports: Optional[List[str]] = None,
                 client: Optional[Client] = None):
        """Initialize a genie instance

        Args:
            instructions: text instructions on the task required to be performed. use the keywords in inputs argument
                to refer to the inputs.
            inputs: a dictionary of inputs to the function. the keys are the names of the inputs and the values are
                small description of the inputs.
            allowed_imports: a list of imports which are allowed to be used in the code. note that this is not
                strictly enforced yet. but it should work most of the times.
            client: an instance of the client to use for making requests to the api. if not provided, a new instance
                will be created.

        Returns:
            A callable which can be used to execute the code generated by the genie.
        """
        self._inputs = inputs
        if isinstance(instructions, str):
            instructions = [instructions]
        self._instructions = instructions
        self._allowed_imports = allowed_imports
        self._code, self._fn_name = self._get_code(client=client or Client())
        self._executor = self._extract_executable(self._code, self._fn_name)

    @abstractmethod
    def _get_code(self, client: Client) -> Tuple[str, str]:
        raise NotImplementedError

    @classmethod
    def _extract_executable(cls, code: str, fn_name: str) -> Callable:
        # define function in memory
        mem = {}
        exec(code, mem)
        return mem[fn_name]

    def __call__(self, *args, **kwargs):
        return self._executor(*args, **kwargs)

    @property
    def code(self):
        """The code generated by the genie"""
        return self._code


class Genie(GenieBase):
    """A generic genie creator with no presets or additional functionality"""

    def _get_code(self, client: Client) -> Tuple[str, str]:
        return client.get_generic(
            GetExecutableRequest(instructions=self._instructions,
                                 inputs=self._inputs,
                                 allowed_imports=self._allowed_imports))


class PandasGenie(GenieBase):
    """Pandas specific genie creator. This is specially configured to work with pandas dataframes."""

    def __init__(self,
                 instructions: Union[str, List[str]],
                 columns: Optional[List[str]] = None,
                 inputs: Optional[Dict[str, str]] = None,
                 allowed_imports: Optional[List[str]] = None,
                 client: Optional[Client] = None):
        """Initialize the Pandas Genie

        Args:
            instructions: text instructions on the task required to be performed. use the keywords in inputs argument
                to refer to the inputs.
            columns: a list of column names in the dataframe to be used as inputs. this helps the genie infer the
                correct column name even if a slightly misspelled name is provided in the instructions.
            inputs: a dictionary of inputs to the function. the keys are the names of the inputs and the values are
                small description of the inputs. a default input of "df" referring to a pandas dataframe will be used
                if not provided.
            allowed_imports: a list of imports which are allowed to be used in the code. note that this is not
                strictly enforced yet. default imports: ["pandas", "numpy", "math", "datetime", "matplotlib", "seaborn"]
            client: an instance of the client to use for making requests to the api. if not provided, a new instance
                will be created.

        Returns:
            A callable which can be used to execute the code generated by the genie.
        """
        self._columns = columns
        super().__init__(instructions, inputs, allowed_imports, client)

    def _get_code(self, client: Client) -> Tuple[str, str]:
        return client.get_pandas(
            GetPandasExecutableRequest(instructions=self._instructions,
                                       inputs=self._inputs,
                                       columns=self._columns,
                                       allowed_imports=self._allowed_imports))
