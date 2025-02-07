""" Autonamous Guidelines Driven AI """
from typing import Any, Dict, List, Optional, Tuple, TypedDict, TypeVar

from openai.openai_object import OpenAIObject
from auto_gpt_plugin_template import AutoGPTPluginTemplate
from autogpt.models.command import Command
from autogpt.models.command_parameter import CommandParameter
from autogpt.llm.providers.openai import OpenAIFunctionCall
# from autogpt.config.ai_config import AIConfig
from .dospai import _dospai_find_similar, _dospai_msg_user, _dospai_ask_gpt, _dospai_store_memslot, _dospai_read_file
from .dospai_data import ClDOSPAIData

PromptGenerator = TypeVar("PromptGenerator")


class Message(TypedDict):
    role: str
    content: str


class ClDOSPAI(AutoGPTPluginTemplate):

    def __init__(self, config):
        super().__init__()
        self._name = "DOSPAI"
        self._version = "0.1.0"
        self._description = "Democratized Open Source Personal AI"
        self._data = ClDOSPAIData(config)

    def can_handle_on_response(self) -> bool:
        """This method is called to check that the plugin can
        handle the on_response method.
        Returns:
            bool: True if the plugin can handle the on_response method."""
        return True

    def on_response(self, content: str, function: OpenAIObject, *args, **kwargs) -> tuple[str, OpenAIFunctionCall]:
        """This method is called when a response is received from the model.
        This is called for any call to GPT not only the chat_with_ai() in the main
        loop start_interaction_loop()"""
        return self._data.process_actions(content, function)


    def can_handle_post_prompt(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_prompt method.
        Returns:
            bool: True if the plugin can handle the post_prompt method."""
        return True

    def can_handle_on_planning(self) -> bool:
        """This method is called to check that the plugin can
        handle the on_planning method.
        Returns:
            bool: True if the plugin can handle the on_planning method."""
        return True

    def on_planning(
        self, prompt: PromptGenerator, messages: List[str]
    ) -> Optional[str]:
        """This method is called before the planning chat completeion is done.
        Args:
            prompt (PromptGenerator): The prompt generator.
            messages (List[str]): The list of messages.
        """
        return self._data.process_msgs(messages)
        # return 'Use the find_similar command defined above to look for similar memories. Ensure your response uses the format specified above.'

    def can_handle_post_planning(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_planning method. 
        Returns:
            bool: True if the plugin can handle the post_planning method."""
        return False # True

    def post_planning(self, response: str) -> str:
        """This method is called after the planning chat completion is done. The respose is the return from GPT with thoughts strategies etc. Can be used to belay unethical commands
        Args:
            response (str): The response.
        Returns:
            str: The resulting response.
        """
        pass # return self._data.process_actions(response)

    def can_handle_pre_instruction(self) -> bool:
        """This method is called to check that the plugin can
        handle the pre_instruction method.
        Returns:
            bool: True if the plugin can handle the pre_instruction method."""
        return False

    def pre_instruction(self, messages: List[str]) -> List[str]:
        """This method is called before the instruction chat is done.
        Args:
            messages (List[str]): The list of context messages.
        Returns:
            List[str]: The resulting list of messages.
        """
        pass

    def can_handle_on_instruction(self) -> bool:
        """This method is called to check that the plugin can
        handle the on_instruction method.
        Returns:
            bool: True if the plugin can handle the on_instruction method."""
        return False

    def on_instruction(self, messages: List[str]) -> Optional[str]:
        """This method is called when the instruction chat is done.
        Args:
            messages (List[str]): The list of context messages.
        Returns:
            Optional[str]: The resulting message.
        """
        pass

    def can_handle_post_instruction(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_instruction method.
        Returns:
            bool: True if the plugin can handle the post_instruction method."""
        return False

    def post_instruction(self, response: str) -> str:
        """This method is called after the instruction chat is done.
        Args:
            response (str): The response.
        Returns:
            str: The resulting response.
        """
        pass

    def can_handle_pre_command(self) -> bool:
        """This method is called to check that the plugin can
        handle the pre_command method.
        Returns:
            bool: True if the plugin can handle the pre_command method."""
        return False

    def pre_command(
        self, command_name: str, arguments: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """This method is called before the command is executed.
        Args:
            command_name (str): The command name.
            arguments (Dict[str, Any]): The arguments.
        Returns:
            Tuple[str, Dict[str, Any]]: The command name and the arguments.
        """
        pass

    def can_handle_post_command(self) -> bool:
        """This method is called to check that the plugin can
        handle the post_command method.
        Returns:
            bool: True if the plugin can handle the post_command method."""
        return True

    def post_command(self, command_name: str, response: str) -> str:
        """This method is called after the command is executed.
        Args:
            command_name (str): The command name.
            response (str): The response.
        Returns:
            str: The resulting response.
        """
        self._data.store_last_command_response(response)
        return response

    def can_handle_chat_completion(
        self,
        messages: list[Dict[Any, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> bool:
        """This method is called to check that the plugin can
        handle the chat_completion method. Called directly before request to GPT, not only in main loop
        Args:
            messages (Dict[Any, Any]): The messages.
            model (str): The model name.
            temperature (float): The temperature.
            max_tokens (int): The max tokens.
        Returns:
            bool: True if the plugin can handle the chat_completion method."""
        return True
    def handle_chat_completion(
        self,
        messages: list[Dict[Any, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """This method is called when the chat completion is done.
        Args:
            messages (Dict[Any, Any]): The messages.
            model (str): The model name.
            temperature (float): The temperature.
            max_tokens (int): The max tokens.
        Returns:
            str: The resulting response.
        """
        return self._data.replace_chat_completion()

    def post_prompt(self, ai_config, prompt: PromptGenerator) -> PromptGenerator:
        """This method is called just after the generate_prompt is called,
            but actually before the prompt is generated.
        Args:
            prompt (PromptGenerator): The prompt generator.
        Returns:
            PromptGenerator: The prompt generator.
        """

        self._data.set_agent_name(prompt.name)
        cmds = [
            Command(
                'telegram_message_user',
                'Message user',
                _dospai_msg_user,
                [CommandParameter("message", "string", description="message_to_send", required=True)]
            ),
            Command(
                'ask_gpt',
                'Send a question back to GPT. Formulate the request as prompt that is well designed and'
                '\nlikely to evoke the correct answer from GPT. Choose a name '
                '\nfor a memory slot to which the answer can be assigned for future reference.',
                _dospai_ask_gpt,
                [
                    CommandParameter("prompt", "string", description="question to ask GPT", required=True),
                    CommandParameter("memslot", "string", description="A name for a memory slot to which the answer will be assigned", required=True),
                ]
            ),
            Command(
                'file_read',
                'read the contents of a text file',
                _dospai_read_file,
                [
                    CommandParameter("filename", "string", description="file name to read", required=True),
                ]
            ),
            Command(
                'store_in_memslot',
                'Store the result of the last command in a memory slot for future use',
                _dospai_store_memslot,
                [
                    CommandParameter("memslot", "string", description="A name for a memory slot to which the answer will be assigned", required=True),
                ]
            ),
        ]
        # Please also provide the name for a memory slot to which your"    "\nanswer can be assigned for future memory reference."
        # "Create a prompt for a question to ask the GPT engine "and provide the name of a memory slot to assign the answer to"
        self._data.register_cmds(cmds, ai_config)
        prompt.add_command(
            "find_similar",
            "Find similar memories that succeeded in the past. ",
            {"memory": "<memory_like_this>"},
            _dospai_find_similar,
        )

        prompt.add_command(
            'telegram_message_user',
            'Message user',
            {"message": "<message_to_send>"},
            _dospai_msg_user,
        )
        return prompt

    def can_handle_text_embedding(
        self, text: str
    ) -> bool:
        """This method is called to check that the plugin can
          handle the text_embedding method.
        Args:
            text (str): The text to be convert to embedding.
          Returns:
              bool: True if the plugin can handle the text_embedding method."""
        return False
    
    def handle_text_embedding(
        self, text: str
    ) -> list:
        """This method is called when the chat completion is done.
        Args:
            text (str): The text to be convert to embedding.
        Returns:
            list: The text embedding.
        """
        pass

    def can_handle_user_input(self, user_input: str) -> bool:
        """This method is called to check that the plugin can
        handle the user_input method.

        Args:
            user_input (str): The user input.

        Returns:
            bool: True if the plugin can handle the user_input method."""
        return False

    def user_input(self, user_input: str) -> str:
        """This method is called to request user input to the user.

        Args:
            user_input (str): The question or prompt to ask the user.

        Returns:
            str: The user input.
        """

        pass

    def can_handle_report(self) -> bool:
        """This method is called to check that the plugin can
        handle the report method.

        Returns:
            bool: True if the plugin can handle the report method."""
        return False

    def report(self, message: str) -> None:
        """This method is called to report a message to the user.

        Args:
            message (str): The message to report.
        """
        pass
